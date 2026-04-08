"""
PlanGenerationWorker — ARQ worker de generación de planes nutricionales.

11 pasos internos:
  1. Carga PetProfile desde DB
  2. Calcula RER/DER (NRCCalculator — domain, no LLM)
  3. Obtiene restricciones (MedicalRestrictionEngine)
  4. Valida alergias
  5. Selecciona modelo (LLMRouter)
  6. Genera plan con LLM (OpenRouterClient)
  7. Valida output — FoodSafetyChecker (post-LLM, REGLA 1)
  8. Genera sustitutos aprobados (substitute_set)
  9. Determina HITL (requires_vet_review — REGLA 4)
  10. Persiste plan + 5 secciones + agent_trace
  11. Actualiza job READY + plan_id / FAILED + error

Constitution REGLAS activas: 1 (toxicidad), 2 (restricciones), 3 (RER/DER), 4 (HITL), 5 (routing), 6 (PII).
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Errores de validación de dominio → no reintentar (son deterministas)
_PERMANENT_ERROR_MARKERS = (
    "tóxicos detectados",
    "restricción",
    "validación nutricional",
    "no encontrada",
)

# Backoff para reintentos de errores transitorios (LLM timeout, red)
_RETRY_DELAYS = [5.0, 15.0]  # segundos — intento 1: 5s, intento 2: 15s
_MAX_RETRIES = len(_RETRY_DELAYS)


def _is_permanent_error(exc: Exception) -> bool:
    """Retorna True si el error es determinista y no tiene sentido reintentar."""
    if isinstance(exc, ValueError):
        msg = str(exc).lower()
        return any(marker in msg for marker in _PERMANENT_ERROR_MARKERS)
    return False

from backend.application.llm.llm_router import LLMRouter
from backend.application.interfaces.agent_trace_repository import IAgentTraceRepository
from backend.application.interfaces.pet_repository import IPetRepository
from backend.application.interfaces.plan_job_repository import IPlanJobRepository
from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.aggregates.nutrition_plan import (
    NutritionPlan, PlanModality, PlanStatus, PlanType,
)
from backend.domain.aggregates.user_account import UserTier
from backend.domain.nutrition.nrc_calculator import NRCCalculator
from backend.domain.safety.medical_restriction_engine import MedicalRestrictionEngine
from backend.domain.value_objects.bcs import BCS, BCSPhase
from backend.infrastructure.agent.prompts.plan_generation_prompts import (
    build_plan_system_prompt,
    build_plan_user_prompt,
)
from backend.infrastructure.agent.subgraphs._plan_generation_core import (
    build_substitute_set,
    requires_vet_review,
    validate_and_enrich_plan,
)
from backend.infrastructure.llm.openrouter_client import OpenRouterClient


async def _update_progress(job_id: uuid.UUID, step: int, message: str) -> None:
    """
    Actualiza el progreso del job en DB con su propia sesión y commit inmediato.

    Se usa durante la generación para que el endpoint de polling refleje el paso
    actual en tiempo real. El fallo de esta operación es silencioso — nunca debe
    bloquear la generación del plan.
    """
    from backend.infrastructure.db.session import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as session:
            from backend.infrastructure.db.plan_job_repository import PostgreSQLPlanJobRepository
            repo = PostgreSQLPlanJobRepository(session)
            job = await repo.find_by_id(job_id)
            if job is not None:
                job.update_progress(step=step, message=message)
                await repo.update(job)
                await session.commit()
    except Exception:
        pass  # El progreso es best-effort — no interrumpir la generación


class PlanGenerationWorker:
    """
    Worker de generación de planes. Ejecutado por ARQ de forma asíncrona.

    En producción se instancia dentro de la función ARQ `generate_plan(ctx, job_id)`.
    Para tests se puede instanciar directamente con dependencias mockeadas.
    """

    def __init__(
        self,
        pet_repo: IPetRepository,
        plan_repo: IPlanRepository,
        job_repo: IPlanJobRepository,
        trace_repo: IAgentTraceRepository,
        llm_client: OpenRouterClient | None = None,
    ) -> None:
        self._pet_repo = pet_repo
        self._plan_repo = plan_repo
        self._job_repo = job_repo
        self._trace_repo = trace_repo
        self._llm_client = llm_client or OpenRouterClient()

    async def execute(self, job_id: uuid.UUID, user_tier: UserTier) -> None:
        """
        Ejecuta los 11 pasos de generación de plan para el job dado.

        Actualiza el job a PROCESSING al inicio y a READY/FAILED al final.
        Reintenta hasta _MAX_RETRIES veces ante errores transitorios (LLM, red).
        Errores de dominio (tóxicos, restricciones, mascota no encontrada) fallan inmediatamente.
        """
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            return

        job.mark_processing()
        await self._job_repo.update(job)

        last_error: Exception | None = None
        for attempt in range(1 + _MAX_RETRIES):
            try:
                plan_id = await self._generate(job=job, user_tier=user_tier)
                job.mark_ready(plan_id=plan_id)
                await self._job_repo.update(job)
                return
            except Exception as exc:
                last_error = exc
                if _is_permanent_error(exc):
                    logger.warning(
                        "job=%s error permanente (intento %d) — no reintentar: %s",
                        job_id, attempt + 1, exc,
                    )
                    break
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS[attempt]
                    logger.warning(
                        "job=%s error transitorio (intento %d/%d) — reintentando en %.0fs: %s",
                        job_id, attempt + 1, 1 + _MAX_RETRIES, delay, type(exc).__name__,
                    )
                    await asyncio.sleep(delay)

        job.mark_failed(error_message=str(last_error))
        await self._job_repo.update(job)

    async def _generate(self, job: Any, user_tier: UserTier) -> uuid.UUID:
        """Pasos 1-10 de generación. Retorna el plan_id creado."""

        # --- Paso 1: Cargar PetProfile ---
        await _update_progress(job.job_id, 1, "Cargando perfil de la mascota...")
        pet = await self._pet_repo.find_by_id(job.pet_id)
        if pet is None:
            raise ValueError(f"Mascota '{job.pet_id}' no encontrada.")

        # --- Paso 2: Calcular RER/DER (determinista — REGLA 3) ---
        await _update_progress(job.job_id, 2, "Calculando requerimientos calóricos (NRC)...")
        rer = NRCCalculator.calculate_rer(pet.weight_kg)
        der = NRCCalculator.calculate_der(
            rer=rer,
            species=pet.species.value,
            age_months=pet.age_months,
            reproductive_status=pet.reproductive_status.value,
            activity_level=pet.activity_level.value,
            bcs=pet.bcs.value,
        )
        bcs_phase: BCSPhase = BCS(pet.bcs.value).phase

        # --- Paso 3: Obtener restricciones médicas (hard-coded — REGLA 2) ---
        await _update_progress(job.job_id, 3, "Verificando restricciones médicas...")
        conditions = [c.value for c in pet.medical_conditions]
        restriction_result = MedicalRestrictionEngine.get_restrictions_for_conditions(
            conditions
        )
        forbidden_ingredients = list(restriction_result.prohibited)

        # --- Paso 4: Validar alergias (incluye detección de alergias tóxicas — REGLA 1) ---
        await _update_progress(job.job_id, 4, "Validando alergias e intolerancias...")
        allergy_list = list(pet.allergies) if pet.allergies else []

        # Detectar alergias que coinciden con TOXIC_DOGS/TOXIC_CATS (refuerzo pre-LLM)
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        toxic_allergies: list[str] = [
            a for a in allergy_list
            if FoodSafetyChecker.check_ingredient(ingredient=a, species=pet.species.value).is_toxic
        ]

        # --- Paso 5: Seleccionar modelo LLM (determinista — REGLA 5) ---
        await _update_progress(job.job_id, 5, "Seleccionando modelo de IA...")
        model = LLMRouter.select_model(
            tier=user_tier,
            conditions_count=len(conditions),
        )

        # --- Paso 6: Generar plan con LLM (prompts expertos NRC/AAFCO + condiciones) ---
        system_prompt = build_plan_system_prompt(
            conditions=conditions,
            species=pet.species.value,
            modality=job.modality,
        )
        user_prompt = build_plan_user_prompt(
            species=pet.species.value,
            age_months=pet.age_months,
            weight_kg=pet.weight_kg,
            breed=getattr(pet, "breed", "raza no especificada"),
            size=getattr(pet, "size", "no especificado"),
            sex=pet.sex.value if hasattr(pet.sex, "value") else str(getattr(pet, "sex", "")),
            reproductive_status=pet.reproductive_status.value,
            activity_level=pet.activity_level.value,
            bcs=pet.bcs.value,
            bcs_phase=bcs_phase.value,
            conditions=conditions,
            allergies=allergy_list,
            toxic_allergies=toxic_allergies,
            current_diet=pet.current_diet.value if hasattr(pet.current_diet, "value") else str(getattr(pet, "current_diet", "concentrado")),
            modality=job.modality,
            rer_kcal=rer,
            der_kcal=der,
            medical_restrictions=forbidden_ingredients,
        )
        await _update_progress(job.job_id, 6, "Generando plan nutricional con IA...")
        # max_tokens=8192: planes complejos (5+ condiciones, 10 secciones) pueden superar 4096 tokens
        llm_response = await self._llm_client.generate(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8192,
        )

        # --- Paso 7: Validación en 3 capas (REGLA 1 + coherencia NRC) ---
        await _update_progress(job.job_id, 7, "Verificando seguridad alimentaria...")
        plan_content, ingredients_raw = validate_and_enrich_plan(
            raw_llm_response=llm_response.content,
            species=pet.species.value,
            conditions=conditions,
            der_kcal=der,
            rer_kcal=rer,
            allergies=allergy_list,
            medical_restrictions=forbidden_ingredients,
            age_months=pet.age_months,
        )

        # --- Paso 8: Generar substitute_set ---
        await _update_progress(job.job_id, 8, "Generando sustitutos de ingredientes...")
        substitute_set = build_substitute_set(
            ingredients_raw=ingredients_raw,
            forbidden_ingredients=forbidden_ingredients,
        )

        # --- Paso 9: Determinar HITL (REGLA 4) ---
        await _update_progress(job.job_id, 9, "Determinando revisión veterinaria...")
        needs_review = requires_vet_review(conditions)
        plan_status = PlanStatus.PENDING_VET if needs_review else PlanStatus.ACTIVE
        plan_type = PlanType.TEMPORAL_MEDICAL if needs_review else PlanType.ESTANDAR

        # --- Paso 10: Persistir agent_trace (inmutable — REGLA 6) ---
        await _update_progress(job.job_id, 10, "Guardando plan en base de datos...")
        # plan_id se genera aquí para pasarlo al trace.
        # agent_traces son append-only sin UPDATE, por lo que plan_id debe
        # conocerse ANTES de insertar el trace.
        plan_uuid = uuid.uuid4()

        trace_id = await self._trace_repo.append(
            pet_id=pet.pet_id,
            plan_id=plan_uuid,
            llm_model=llm_response.model_used,
            prompt_tokens=llm_response.prompt_tokens,
            completion_tokens=llm_response.completion_tokens,
            latency_ms=llm_response.latency_ms,
            input_summary={
                "species": pet.species.value,
                "weight_kg": pet.weight_kg,
                "conditions_count": len(conditions),
                "modality": job.modality,
            },
            output_summary={
                "rer_kcal": round(rer, 2),
                "der_kcal": round(der, 2),
                "ingredients_count": len(ingredients_raw),
            },
            created_at=datetime.now(timezone.utc),
        )

        # Incluir substitute_set en el contenido del plan
        plan_content["substitute_set"] = substitute_set

        # Persistir plan usando el mismo plan_uuid ya referenciado en el trace
        plan = NutritionPlan(
            plan_id=plan_uuid,
            pet_id=pet.pet_id,
            owner_id=pet.owner_id,
            plan_type=plan_type,
            status=plan_status,
            modality=PlanModality(job.modality),
            rer_kcal=round(rer, 2),
            der_kcal=round(der, 2),
            weight_phase=bcs_phase,
            llm_model_used=llm_response.model_used,
            content=plan_content,
            approved_by_vet_id=None,
            approval_timestamp=None,
            review_date=None,
            vet_comment=None,
            agent_trace_id=trace_id,
        )
        await self._plan_repo.save(plan)

        return plan.plan_id
