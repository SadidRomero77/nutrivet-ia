"""
Router de planes nutricionales — 9 endpoints FastAPI.

POST  /v1/plans/generate             — encola job, retorna job_id
GET   /v1/plans/jobs/{job_id}        — polling status del job
GET   /v1/plans/{plan_id}            — obtener plan con 5 secciones
GET   /v1/plans                      — listar planes del owner
PATCH /v1/plans/{plan_id}/approve    — HITL approve (vet only)
PATCH /v1/plans/{plan_id}/return     — HITL return (vet only)
GET   /v1/plans/{plan_id}/substitutes — listar substitute set
POST  /v1/plans/{plan_id}/substitutes — solicitar sustitución
GET   /v1/vet/plans/pending          — lista PENDING_VET para vet dashboard
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from backend.application.use_cases.hitl_review_use_case import HitlReviewUseCase
from backend.application.use_cases.ingredient_substitution_use_case import (
    IngredientSubstitutionUseCase,
)
from backend.application.use_cases.plan_generation_use_case import PlanGenerationUseCase
from backend.domain.aggregates.user_account import UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.db.session import AsyncSessionLocal
from backend.infrastructure.workers.plan_generation_worker import PlanGenerationWorker
from backend.infrastructure.auth.jwt_service import TokenPayload
from backend.infrastructure.db.agent_trace_repository import PostgreSQLAgentTraceRepository
from sqlalchemy import select
from backend.infrastructure.db.models import ClaimCodeModel
from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
from backend.infrastructure.db.plan_job_repository import PostgreSQLPlanJobRepository
from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
from backend.presentation.schemas.pet_schemas import PetResponse
from backend.infrastructure.db.session import get_db_session
from backend.presentation.middleware.auth_middleware import get_current_user, require_role
from backend.presentation.schemas.plan_schemas import (
    ComidaDistribucion,
    FaseTransicion,
    IngredientItem,
    IngredientsSection,
    InstruccionesPorGrupo,
    NutritionalProfileSection,
    PlanApproveRequest,
    PlanGenerateRequest,
    PlanJobResponse,
    PlanResponse,
    PlanReturnRequest,
    PlanSummaryResponse,
    PortionsSection,
    PreparationSection,
    SnackSaludable,
    SubstituteRequest,
    SubstituteResponse,
    SupplementItem,
    TransitionSection,
)

from backend.infrastructure.db.device_token_repository import PostgreSQLDeviceTokenRepository
from backend.infrastructure.push.fcm_client import PushNotification, send_push_to_tokens

router = APIRouter(tags=["plans"])
vet_router = APIRouter(tags=["vet"])


# ---------------------------------------------------------------------------
# Helper push notifications — fire-and-forget, nunca bloquea la respuesta
# ---------------------------------------------------------------------------

async def _push_to_user(user_id: uuid.UUID, notification: PushNotification) -> None:
    """Envía push notification a todos los devices de un usuario (fire-and-forget)."""
    try:
        async with AsyncSessionLocal() as session:
            token_repo = PostgreSQLDeviceTokenRepository(session)
            tokens = await token_repo.get_tokens_for_user(user_id)
            if tokens:
                await send_push_to_tokens(tokens=tokens, notification=notification)
    except Exception:
        logger.exception("Error enviando push notification a user=%s", user_id)


async def _notify_vet_if_pending(session: AsyncSession, job_id: uuid.UUID) -> None:
    """
    Si el plan recién creado está en PENDING_VET, notifica al vet del pet.

    Busca el vet vinculado al pet via ClaimCode para enviarle la push.
    """
    try:
        from sqlalchemy import select as _select
        from backend.infrastructure.db.models import (
            PlanJobModel, NutritionPlanModel, ClaimCodeModel,
        )
        from backend.infrastructure.db.device_token_repository import PostgreSQLDeviceTokenRepository

        # Obtener plan del job
        job_q = await session.execute(
            _select(PlanJobModel).where(PlanJobModel.id == job_id)
        )
        job = job_q.scalar_one_or_none()
        if job is None or job.plan_id is None:
            return

        plan_q = await session.execute(
            _select(NutritionPlanModel).where(NutritionPlanModel.id == job.plan_id)
        )
        plan = plan_q.scalar_one_or_none()
        if plan is None or plan.status != "pending_vet":
            return

        # Buscar vet vinculado al pet via ClaimCode
        claim_q = await session.execute(
            _select(ClaimCodeModel).where(
                ClaimCodeModel.pet_id == plan.pet_id,
                ClaimCodeModel.used.is_(True),
            ).order_by(ClaimCodeModel.created_at.desc()).limit(1)
        )
        claim = claim_q.scalar_one_or_none()
        if claim is None or claim.vet_id is None:
            return

        token_repo = PostgreSQLDeviceTokenRepository(session)
        tokens = await token_repo.get_tokens_for_user(claim.vet_id)
        if tokens:
            await send_push_to_tokens(
                tokens=tokens,
                notification=PushNotification(
                    title="Nuevo plan para revisar",
                    body="Un propietario generó un plan con condición médica. Requiere tu aprobación.",
                    data={"event": "plan_pending_vet", "plan_id": str(plan.id)},
                ),
            )
    except Exception:
        logger.exception("Error en _notify_vet_if_pending job=%s", job_id)


# ---------------------------------------------------------------------------
# Background worker (dev) — corre PlanGenerationWorker sin ARQ/Redis
# ---------------------------------------------------------------------------

async def _run_worker_background(job_id: uuid.UUID, user_tier: UserTier) -> None:
    """
    Ejecuta el PlanGenerationWorker en una sesión DB propia.

    En producción este rol lo cumple el ARQ worker (Celery-like sobre Redis).
    Para dev y staging sin Redis, FastAPI BackgroundTasks es suficiente.
    """
    async with AsyncSessionLocal() as session:
        try:
            from backend.infrastructure.db.agent_trace_repository import PostgreSQLAgentTraceRepository
            from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
            from backend.infrastructure.db.plan_job_repository import PostgreSQLPlanJobRepository
            from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
            worker = PlanGenerationWorker(
                pet_repo=PostgreSQLPetRepository(session),
                plan_repo=PostgreSQLPlanRepository(session),
                job_repo=PostgreSQLPlanJobRepository(session),
                trace_repo=PostgreSQLAgentTraceRepository(session),
            )
            await worker.execute(job_id=job_id, user_tier=user_tier)
            await session.commit()
            logger.info("plan_generation_worker completado job=%s", job_id)

            # Push notification: notificar al vet si el plan quedó PENDING_VET
            await _notify_vet_if_pending(session=session, job_id=job_id)
        except Exception:
            await session.rollback()
            logger.exception("plan_generation_worker falló job=%s", job_id)


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------

def _gen_use_case(session: AsyncSession) -> PlanGenerationUseCase:
    return PlanGenerationUseCase(
        plan_repo=PostgreSQLPlanRepository(session),
        job_repo=PostgreSQLPlanJobRepository(session),
        pet_repo=PostgreSQLPetRepository(session),
        trace_repo=PostgreSQLAgentTraceRepository(session),
    )


def _hitl_use_case(session: AsyncSession) -> HitlReviewUseCase:
    return HitlReviewUseCase(plan_repo=PostgreSQLPlanRepository(session))


def _sub_use_case(session: AsyncSession) -> IngredientSubstitutionUseCase:
    return IngredientSubstitutionUseCase(plan_repo=PostgreSQLPlanRepository(session))


# ---------------------------------------------------------------------------
# Helpers de serialización
# ---------------------------------------------------------------------------

def _plan_to_response(plan: Any) -> PlanResponse:
    """Convierte NutritionPlan → PlanResponse con estructura clínica completa."""
    content = plan.content or {}

    # Sección 1: Perfil nutricional
    pn_raw = content.get("perfil_nutricional", {}) or {}
    perfil = NutritionalProfileSection(
        rer_kcal=plan.rer_kcal,
        der_kcal=plan.der_kcal,
        weight_phase=plan.weight_phase.value if hasattr(plan.weight_phase, "value") else str(plan.weight_phase),
        protein_pct=pn_raw.get("proteina_pct_ms"),
        fat_pct=pn_raw.get("grasa_pct_ms"),
        racion_total_g_dia=pn_raw.get("racion_total_g_dia"),
        relacion_ca_p=pn_raw.get("relacion_ca_p"),
        omega3_mg_dia=pn_raw.get("omega3_mg_dia"),
    )

    # Sección 2: Ingredientes — campo correcto del LLM es `cantidad_g`
    ingredientes_raw = content.get("ingredientes", [])
    if isinstance(ingredientes_raw, list):
        items = [
            IngredientItem(
                nombre=i.get("nombre", "") if isinstance(i, dict) else str(i),
                cantidad_g=i.get("cantidad_g") if isinstance(i, dict) else None,
                kcal=i.get("kcal") if isinstance(i, dict) else None,
                proteina_g=i.get("proteina_g") if isinstance(i, dict) else None,
                grasa_g=i.get("grasa_g") if isinstance(i, dict) else None,
                fuente=i.get("fuente") if isinstance(i, dict) else None,
                frecuencia=i.get("frecuencia") if isinstance(i, dict) else None,
                notas=i.get("notas") if isinstance(i, dict) else None,
            )
            for i in ingredientes_raw
            if isinstance(i, dict) and i.get("nombre")
        ]
    else:
        items = []

    # Sección 3: Porciones con cronograma diario
    porciones_raw = content.get("porciones", {}) or {}
    distribucion_raw = porciones_raw.get("distribucion_comidas", []) if isinstance(porciones_raw, dict) else []
    distribucion = [
        ComidaDistribucion(
            horario=c.get("horario", ""),
            porcentaje=c.get("porcentaje"),
            gramos=c.get("gramos"),
            proteina_g=c.get("proteina_g"),
            carbo_g=c.get("carbo_g"),
            vegetal_g=c.get("vegetal_g"),
        )
        for c in distribucion_raw
        if isinstance(c, dict)
    ]
    g_por_comida = porciones_raw.get("g_por_comida") if isinstance(porciones_raw, dict) else None
    porciones = PortionsSection(
        comidas_por_dia=porciones_raw.get("numero_comidas", 2) if isinstance(porciones_raw, dict) else 2,
        total_g_dia=porciones_raw.get("total_g_dia") if isinstance(porciones_raw, dict) else None,
        g_por_comida=g_por_comida,
        porcion_por_comida_gramos=g_por_comida,
        distribucion_comidas=distribucion,
    )

    # Sección 4: Suplementos
    supl_raw = content.get("suplementos", []) or []
    suplementos = [
        SupplementItem(
            nombre=s.get("nombre", ""),
            dosis=s.get("dosis", ""),
            frecuencia=s.get("frecuencia", ""),
            forma=s.get("forma", ""),
            justificacion=s.get("justificacion", ""),
        )
        for s in supl_raw
        if isinstance(s, dict) and s.get("nombre")
    ]

    # Sección 5: Instrucciones de preparación completas
    instr_raw = content.get("instrucciones_preparacion", {}) or {}
    ipg_raw = instr_raw.get("instrucciones_por_grupo", {}) or {} if isinstance(instr_raw, dict) else {}
    instrucciones = PreparationSection(
        metodo=instr_raw.get("metodo") if isinstance(instr_raw, dict) else None,
        pasos=instr_raw.get("pasos", []) if isinstance(instr_raw, dict) else [],
        tiempo_preparacion_minutos=instr_raw.get("tiempo_preparacion_minutos") if isinstance(instr_raw, dict) else None,
        tiempo_estimado_minutos=instr_raw.get("tiempo_preparacion_minutos") if isinstance(instr_raw, dict) else None,
        almacenamiento=instr_raw.get("almacenamiento") if isinstance(instr_raw, dict) else None,
        advertencias=instr_raw.get("advertencias", []) if isinstance(instr_raw, dict) else [],
        instrucciones_por_grupo=InstruccionesPorGrupo(
            proteinas=ipg_raw.get("proteinas", []) if isinstance(ipg_raw, dict) else [],
            carbohidratos=ipg_raw.get("carbohidratos", []) if isinstance(ipg_raw, dict) else [],
            vegetales=ipg_raw.get("vegetales", []) if isinstance(ipg_raw, dict) else [],
        ),
        adiciones_permitidas=instr_raw.get("adiciones_permitidas", []) if isinstance(instr_raw, dict) else [],
    )

    # Sección 6: Snacks saludables
    snacks_raw = content.get("snacks_saludables", []) or []
    snacks = [
        SnackSaludable(
            nombre=s.get("nombre", ""),
            descripcion=s.get("descripcion", ""),
            cantidad_g=s.get("cantidad_g", 20),
            frecuencia=s.get("frecuencia", "ocasional"),
        )
        for s in snacks_raw
        if isinstance(s, dict) and s.get("nombre")
    ]

    # Sección 7: Transición (condicional)
    trans_raw = content.get("transicion_dieta") or {}
    if isinstance(trans_raw, dict) and trans_raw:
        fases_raw = trans_raw.get("fases", []) or []
        fases = [
            FaseTransicion(dias=f.get("dias", ""), descripcion=f.get("descripcion", ""))
            for f in fases_raw
            if isinstance(f, dict)
        ]
        transicion: TransitionSection | None = TransitionSection(
            requiere_transicion=trans_raw.get("requiere_transicion", True),
            duracion_dias=trans_raw.get("duracion_dias", 7),
            fases=fases,
            senales_de_alerta=trans_raw.get("senales_de_alerta", []),
        )
    else:
        transicion = None

    return PlanResponse(
        plan_id=plan.plan_id,
        pet_id=plan.pet_id,
        owner_id=plan.owner_id,
        plan_type=plan.plan_type.value if hasattr(plan.plan_type, "value") else str(plan.plan_type),
        status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
        modality=plan.modality.value if hasattr(plan.modality, "value") else str(plan.modality),
        llm_model_used=plan.llm_model_used,
        perfil_nutricional=perfil,
        objetivos_clinicos=content.get("objetivos_clinicos", []) or [],
        ingredientes_prohibidos=content.get("ingredientes_prohibidos", []) or [],
        ingredientes=IngredientsSection(items=items),
        porciones=porciones,
        suplementos=suplementos,
        instrucciones_preparacion=instrucciones,
        snacks_saludables=snacks,
        protocolo_digestivo=content.get("protocolo_digestivo", []) or [],
        transicion_dieta=transicion,
        notas_clinicas=content.get("notas_clinicas", []) or [],
        alertas_propietario=content.get("alertas_propietario", []) or [],
        approved_by_vet_id=plan.approved_by_vet_id,
        review_date=plan.review_date,
        vet_comment=plan.vet_comment,
    )


def _plan_to_summary(
    plan: Any,
    conditions_count: int = 0,
    created_at: Any = None,
) -> PlanSummaryResponse:
    created_at_str: str | None = None
    if created_at is not None and hasattr(created_at, "isoformat"):
        created_at_str = created_at.isoformat()
    elif created_at is not None:
        created_at_str = str(created_at)
    return PlanSummaryResponse(
        plan_id=plan.plan_id,
        pet_id=plan.pet_id,
        plan_type=plan.plan_type.value if hasattr(plan.plan_type, "value") else str(plan.plan_type),
        status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
        modality=plan.modality.value if hasattr(plan.modality, "value") else str(plan.modality),
        rer_kcal=plan.rer_kcal,
        der_kcal=plan.der_kcal,
        llm_model_used=plan.llm_model_used,
        approved_by_vet_id=plan.approved_by_vet_id,
        conditions_count=conditions_count,
        created_at=created_at_str,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/v1/plans/generate", response_model=PlanJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_plan(
    body: PlanGenerateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> PlanJobResponse:
    """
    Encola job de generación de plan. Retorna job_id para polling.

    El worker corre como BackgroundTask (dev) con su propia sesión DB.
    En producción equivale al ARQ worker sobre Redis.
    """
    try:
        uc = _gen_use_case(session)
        job_id = await uc.enqueue(
            pet_id=body.pet_id,
            owner_id=user.user_id,
            user_tier=user.tier,
            modality=body.modality,
        )
        # Commit explícito ANTES de disparar background task para evitar
        # condición de carrera: el worker crea su propia sesión y necesita
        # que el job ya esté persistido en DB.
        await session.commit()
        background_tasks.add_task(_run_worker_background, job_id, user.tier)
        return PlanJobResponse(job_id=job_id, status="QUEUED")
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/v1/plans/jobs/{job_id}", response_model=PlanJobResponse)
async def get_job_status(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> PlanJobResponse:
    """Polling del estado del job de generación."""
    try:
        uc = _gen_use_case(session)
        result = await uc.get_job(job_id=job_id, requester_id=user.user_id)
        return PlanJobResponse(**result)
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/v1/plans", response_model=list[PlanSummaryResponse])
async def list_plans(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> list[PlanSummaryResponse]:
    """Lista todos los planes del owner autenticado."""
    plan_repo = PostgreSQLPlanRepository(session)
    plans = await plan_repo.list_by_owner(user.user_id)
    return [_plan_to_summary(p) for p in plans]


@router.get("/v1/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> PlanResponse:
    """Obtener plan completo con 5 secciones."""
    plan_repo = PostgreSQLPlanRepository(session)
    plan = await plan_repo.find_by_id(plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado.")
    # Owners solo ven sus planes, vets ven todos
    if user.role.value != "vet" and plan.owner_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    return _plan_to_response(plan)


@router.patch("/v1/plans/{plan_id}/approve", response_model=dict)
async def approve_plan(
    plan_id: uuid.UUID,
    body: PlanApproveRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> dict:
    """Vet aprueba plan PENDING_VET → ACTIVE. Notifica al owner por push."""
    # Obtener owner_id antes de aprobar para la notificación
    plan_repo = PostgreSQLPlanRepository(session)
    plan_obj = await plan_repo.find_by_id(plan_id)
    owner_id = plan_obj.owner_id if plan_obj else None

    try:
        uc = _hitl_use_case(session)
        result = await uc.approve(
            plan_id=plan_id, vet_id=user.user_id, review_date=body.review_date
        )
    except DomainError as e:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY if "review_date" in str(e).lower() or "revisión" in str(e).lower() else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=str(e)) from e

    if owner_id:
        background_tasks.add_task(
            _push_to_user,
            owner_id,
            PushNotification(
                title="¡Tu plan nutricional está aprobado!",
                body="El veterinario revisó y aprobó el plan. Ya puedes verlo y exportarlo.",
                data={"event": "plan_approved", "plan_id": str(plan_id)},
            ),
        )

    return result


@router.patch("/v1/plans/{plan_id}/return", response_model=dict)
async def return_plan(
    plan_id: uuid.UUID,
    body: PlanReturnRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> dict:
    """Vet devuelve plan al owner con comentario obligatorio. Notifica al owner por push."""
    plan_repo = PostgreSQLPlanRepository(session)
    plan_obj = await plan_repo.find_by_id(plan_id)
    owner_id = plan_obj.owner_id if plan_obj else None

    try:
        uc = _hitl_use_case(session)
        result = await uc.return_to_owner(
            plan_id=plan_id, vet_id=user.user_id, comment=body.comment
        )
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    if owner_id:
        background_tasks.add_task(
            _push_to_user,
            owner_id,
            PushNotification(
                title="El vet revisó tu plan",
                body="Tu plan tiene un comentario del veterinario. Revísalo para hacer ajustes.",
                data={"event": "plan_returned", "plan_id": str(plan_id)},
            ),
        )

    return result


@router.get("/v1/plans/{plan_id}/substitutes", response_model=list[str])
async def get_substitutes(
    plan_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> list[str]:
    """Lista el substitute_set del plan."""
    plan_repo = PostgreSQLPlanRepository(session)
    plan = await plan_repo.find_by_id(plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado.")
    if user.role.value != "vet" and plan.owner_id != user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    return plan.content.get("substitute_set", [])


@router.post("/v1/plans/{plan_id}/substitutes", response_model=SubstituteResponse)
async def request_substitution(
    plan_id: uuid.UUID,
    body: SubstituteRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> SubstituteResponse:
    """Owner solicita sustitución de ingrediente."""
    try:
        uc = _sub_use_case(session)
        result = await uc.substitute(
            plan_id=plan_id,
            requester_id=user.user_id,
            original_ingredient=body.original_ingredient,
            substitute_ingredient=body.substitute_ingredient,
        )
        return SubstituteResponse(**result)
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Vet dashboard
# ---------------------------------------------------------------------------

@vet_router.get("/v1/vet/plans/pending", response_model=list[PlanSummaryResponse])
async def list_pending_plans(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> list[PlanSummaryResponse]:
    """Lista planes PENDING_VET para el dashboard del vet, ordenados por antigüedad."""
    from sqlalchemy import select as sa_select
    from backend.infrastructure.db.models import NutritionPlanModel, PetModel as PetORM

    result = await session.execute(
        sa_select(NutritionPlanModel, PetORM).join(
            PetORM, NutritionPlanModel.pet_id == PetORM.id
        ).where(
            NutritionPlanModel.status == "PENDING_VET"
        ).order_by(NutritionPlanModel.created_at.asc())
    )
    rows = result.all()

    from backend.infrastructure.db.plan_repository import _to_domain
    summaries = []
    for plan_row, pet_row in rows:
        plan = _to_domain(plan_row)
        conditions_count = len(pet_row.medical_conditions or [])
        summaries.append(_plan_to_summary(
            plan,
            conditions_count=conditions_count,
            created_at=plan_row.created_at,
        ))
    return summaries


def _vet_pet_to_response(pet: Any) -> PetResponse:
    """Convierte PetProfile → PetResponse para endpoints de vet."""
    return PetResponse(
        pet_id=pet.pet_id,
        owner_id=pet.owner_id,
        name=pet.name,
        species=pet.species.value,
        breed=pet.breed,
        sex=pet.sex.value,
        age_months=pet.age_months,
        weight_kg=pet.weight_kg,
        size=pet.size.value if pet.size else None,
        reproductive_status=pet.reproductive_status.value,
        activity_level=pet.activity_level.value,
        bcs=pet.bcs.value,
        medical_conditions=[c.value for c in pet.medical_conditions],
        allergies=pet.allergies,
        current_diet=pet.current_diet.value,
        vet_id=pet.vet_id,
    )


@vet_router.get("/v1/vet/patients", response_model=list[PetResponse])
async def list_vet_patients(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> list[PetResponse]:
    """Lista ClinicPets creados por el vet autenticado.

    Incluye owner_name, owner_phone y claim_code activo (si no fue reclamado aún).
    Usa 2 queries fijas (sin N+1): una para pacientes, una para claim codes.
    """
    import uuid as _uuid
    from backend.infrastructure.db.models import PetModel as PetORM
    pet_repo = PostgreSQLPetRepository(session)

    # Query 1: todos los pacientes del vet
    stmt = select(PetORM).where(
        PetORM.vet_id == user.user_id,
        PetORM.is_clinic_pet.is_(True),
        PetORM.is_active.is_(True),
    )
    result = await session.execute(stmt)
    models = result.scalars().all()

    if not models:
        return []

    # Query 2: claim codes activos para todos los pacientes (una sola query con IN)
    patient_ids = [m.id for m in models]
    claims_stmt = select(ClaimCodeModel.pet_id, ClaimCodeModel.code).where(
        ClaimCodeModel.pet_id.in_(patient_ids),
        ClaimCodeModel.used.is_(False),
    )
    claims_result = await session.execute(claims_stmt)
    # Tomar el primer claim code por pet (el resto los ignoramos)
    claim_codes_by_pet: dict[_uuid.UUID, str] = {}
    for row in claims_result:
        if row.pet_id not in claim_codes_by_pet:
            claim_codes_by_pet[row.pet_id] = row.code

    enc = pet_repo._enc
    responses: list[PetResponse] = []
    for model in models:
        conditions = enc.decrypt(model.medical_conditions_enc) if model.medical_conditions_enc else []
        allergies = enc.decrypt(model.allergies_enc) if model.allergies_enc else []

        responses.append(PetResponse(
            pet_id=model.id,
            owner_id=model.owner_id,
            name=model.name,
            species=model.species,
            breed=model.breed,
            sex=model.sex,
            age_months=model.age_months,
            weight_kg=model.weight_kg,
            size=model.size,
            reproductive_status=model.reproductive_status,
            activity_level=model.activity_level,
            bcs=model.bcs,
            medical_conditions=conditions,
            allergies=allergies,
            current_diet=model.current_diet,
            vet_id=model.vet_id,
            owner_name=model.owner_name_hint,
            owner_phone=model.owner_phone_hint,
            claim_code=claim_codes_by_pet.get(model.id),
        ))
    return responses


@vet_router.get("/v1/vet/patients/{pet_id}", response_model=PetResponse)
async def get_vet_patient(
    pet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> PetResponse:
    """Obtiene un paciente clínico por ID con datos completos del propietario y claim_code."""
    from backend.infrastructure.db.models import PetModel as PetORM
    pet_repo = PostgreSQLPetRepository(session)

    stmt = select(PetORM).where(
        PetORM.id == pet_id,
        PetORM.vet_id == user.user_id,
        PetORM.is_clinic_pet.is_(True),
        PetORM.is_active.is_(True),
    )
    result = await session.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado.")

    # Obtener claim code activo (sin usar) si existe
    claim_stmt = select(ClaimCodeModel.code).where(
        ClaimCodeModel.pet_id == model.id,
        ClaimCodeModel.used.is_(False),
    ).limit(1)
    claim_result = await session.execute(claim_stmt)
    claim_code = claim_result.scalar_one_or_none()

    # Desencriptar campos médicos
    enc = pet_repo._enc
    conditions = enc.decrypt(model.medical_conditions_enc) if model.medical_conditions_enc else []
    allergies = enc.decrypt(model.allergies_enc) if model.allergies_enc else []

    return PetResponse(
        pet_id=model.id,
        owner_id=model.owner_id,
        name=model.name,
        species=model.species,
        breed=model.breed,
        sex=model.sex,
        age_months=model.age_months,
        weight_kg=model.weight_kg,
        size=model.size,
        reproductive_status=model.reproductive_status,
        activity_level=model.activity_level,
        bcs=model.bcs,
        medical_conditions=conditions,
        allergies=allergies,
        current_diet=model.current_diet,
        vet_id=model.vet_id,
        owner_name=model.owner_name_hint,
        owner_phone=model.owner_phone_hint,
        claim_code=claim_code,
    )


@vet_router.delete("/v1/vet/patients/{pet_id}", status_code=204)
async def delete_vet_patient(
    pet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> None:
    """Elimina (soft-delete) un paciente clínico.

    Solo si el vet es propietario del paciente, no tiene planes asignados,
    y aún no ha sido reclamado (claim_code sin usar existe).
    """
    from backend.infrastructure.db.models import PetModel as PetORM, NutritionPlanModel
    stmt = select(PetORM).where(
        PetORM.id == pet_id,
        PetORM.vet_id == user.user_id,
        PetORM.is_clinic_pet.is_(True),
        PetORM.is_active.is_(True),
    )
    result = await session.execute(stmt)
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado.")

    # Verificar que no tenga planes asignados
    plan_stmt = select(NutritionPlanModel).where(NutritionPlanModel.pet_id == pet_id).limit(1)
    plan_result = await session.execute(plan_stmt)
    if plan_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: el paciente tiene planes nutricionales asignados.",
        )

    # Verificar que no esté vinculado (claim_code sin usar = no vinculado)
    claim_stmt = select(ClaimCodeModel).where(
        ClaimCodeModel.pet_id == pet_id,
        ClaimCodeModel.used.is_(True),
    ).limit(1)
    claim_result = await session.execute(claim_stmt)
    if claim_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar: el paciente ya fue vinculado a un propietario.",
        )

    model.is_active = False
