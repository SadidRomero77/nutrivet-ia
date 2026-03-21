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

import uuid
from datetime import datetime
from typing import Any

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
from backend.domain.safety.food_safety_checker import FoodSafetyChecker
from backend.domain.safety.medical_restriction_engine import MedicalRestrictionEngine
from backend.domain.value_objects.bcs import BCS, BCSPhase
from backend.infrastructure.agent.prompts.plan_generation_prompts import (
    build_plan_system_prompt,
    build_plan_user_prompt,
)
from backend.infrastructure.agent.validators.json_repair import safe_parse_plan_json
from backend.infrastructure.agent.validators.nutritional_validator import (
    enrich_plan_with_validation,
    validate_nutritional_plan,
)
from backend.infrastructure.llm.openrouter_client import OpenRouterClient


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
        """
        # --- Paso 1: Cargar job ---
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            return

        job.mark_processing()
        await self._job_repo.update(job)

        try:
            plan_id = await self._generate(job=job, user_tier=user_tier)
            job.mark_ready(plan_id=plan_id)
        except Exception as e:
            job.mark_failed(error_message=str(e))

        await self._job_repo.update(job)

    async def _generate(self, job: Any, user_tier: UserTier) -> uuid.UUID:
        """Pasos 1-10 de generación. Retorna el plan_id creado."""

        # --- Paso 1: Cargar PetProfile ---
        pet = await self._pet_repo.find_by_id(job.pet_id)
        if pet is None:
            raise ValueError(f"Mascota '{job.pet_id}' no encontrada.")

        # --- Paso 2: Calcular RER/DER (determinista — REGLA 3) ---
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
        conditions = [c.value for c in pet.medical_conditions]
        restriction_result = MedicalRestrictionEngine.get_restrictions_for_conditions(
            conditions
        )
        forbidden_ingredients = list(restriction_result.prohibited)

        # --- Paso 4: Validar alergias ---
        allergy_list = list(pet.allergies) if pet.allergies else []

        # --- Paso 5: Seleccionar modelo LLM (determinista — REGLA 5) ---
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
            current_diet=pet.current_diet.value if hasattr(pet.current_diet, "value") else str(getattr(pet, "current_diet", "concentrado")),
            modality=job.modality,
            rer_kcal=rer,
            der_kcal=der,
            medical_restrictions=forbidden_ingredients,
        )
        llm_response = await self._llm_client.generate(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        # --- Paso 7: Validación en 3 capas (REGLA 1 + coherencia NRC) ---

        # Capa 1: JSON repair + parsing robusto
        plan_content = safe_parse_plan_json(llm_response.content, der_kcal=der)

        # Capa 2: FoodSafetyChecker — toxicidad (REGLA 1)
        ingredients_raw: list[str] = []
        ing = plan_content.get("ingredientes", [])
        if isinstance(ing, list):
            ingredients_raw = [
                i["nombre"] if isinstance(i, dict) else str(i) for i in ing
            ]
        elif isinstance(ing, dict):
            ingredients_raw = list(ing.keys())

        toxicity_results = FoodSafetyChecker.validate_plan_ingredients(
            ingredients=ingredients_raw,
            species=pet.species.value,
        )
        toxic_found = [r.ingredient for r in toxicity_results if r.is_toxic]
        if toxic_found:
            raise ValueError(
                f"Plan rechazado: ingredientes tóxicos detectados: {toxic_found}"
            )

        # Capa 3: validación nutricional NRC (proteína, Ca:P, grasa, restricciones)
        validation_result = validate_nutritional_plan(
            plan_content=plan_content,
            species=pet.species.value,
            conditions=conditions,
            der_kcal=der,
            rer_kcal=rer,
            allergies=allergy_list,
            medical_restrictions=forbidden_ingredients,
            age_months=pet.age_months,
        )
        if validation_result.blocking_errors:
            raise ValueError(
                "Plan rechazado por validación nutricional: "
                + " | ".join(validation_result.blocking_errors)
            )
        plan_content = enrich_plan_with_validation(plan_content, validation_result)

        # --- Paso 8: Generar substitute_set ---
        substitute_set = [
            ing_name for ing_name in ingredients_raw
            if ing_name.lower() not in [f.lower() for f in forbidden_ingredients]
        ]

        # --- Paso 9: Determinar HITL (REGLA 4) ---
        has_medical_conditions = len(conditions) > 0
        plan_status = PlanStatus.PENDING_VET if has_medical_conditions else PlanStatus.ACTIVE
        plan_type = PlanType.TEMPORAL_MEDICAL if has_medical_conditions else PlanType.ESTANDAR

        # --- Paso 10: Persistir agent_trace (inmutable — REGLA 6) ---
        trace_id = await self._trace_repo.append(
            pet_id=pet.pet_id,
            plan_id=None,  # Se actualizará con el plan_id real
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
                "toxic_found": toxic_found,
            },
            created_at=datetime.utcnow(),
        )

        # Incluir substitute_set en el contenido del plan
        plan_content["substitute_set"] = substitute_set

        # Persistir plan
        plan = NutritionPlan(
            plan_id=uuid.uuid4(),
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
