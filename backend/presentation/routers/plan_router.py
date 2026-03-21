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

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.use_cases.hitl_review_use_case import HitlReviewUseCase
from backend.application.use_cases.ingredient_substitution_use_case import (
    IngredientSubstitutionUseCase,
)
from backend.application.use_cases.plan_generation_use_case import PlanGenerationUseCase
from backend.domain.exceptions.domain_errors import DomainError
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
    IngredientsSection,
    NutritionalProfileSection,
    PlanApproveRequest,
    PlanGenerateRequest,
    PlanJobResponse,
    PlanResponse,
    PlanReturnRequest,
    PlanSummaryResponse,
    PortionsSection,
    PreparationSection,
    SubstituteRequest,
    SubstituteResponse,
    TransitionSection,
)

router = APIRouter(tags=["plans"])
vet_router = APIRouter(tags=["vet"])


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
    """Convierte NutritionPlan → PlanResponse con 5 secciones."""
    content = plan.content or {}

    # Sección 1: Perfil nutricional
    perfil = NutritionalProfileSection(
        rer_kcal=plan.rer_kcal,
        der_kcal=plan.der_kcal,
        weight_phase=plan.weight_phase.value if hasattr(plan.weight_phase, "value") else str(plan.weight_phase),
        protein_pct=content.get("perfil_nutricional", {}).get("protein_pct"),
        fat_pct=content.get("perfil_nutricional", {}).get("fat_pct"),
        carbs_pct=content.get("perfil_nutricional", {}).get("carbs_pct"),
    )

    # Sección 2: Ingredientes
    ingredientes_raw = content.get("ingredientes", [])
    if isinstance(ingredientes_raw, list):
        from backend.presentation.schemas.plan_schemas import IngredientItem
        items = [
            IngredientItem(
                nombre=i["nombre"] if isinstance(i, dict) else str(i),
                cantidad_gramos=i.get("cantidad_gramos") if isinstance(i, dict) else None,
            )
            for i in ingredientes_raw
        ]
    else:
        items = []

    # Sección 3: Porciones
    porciones_raw = content.get("porciones", {})
    porciones = PortionsSection(
        comidas_por_dia=porciones_raw.get("comidas_por_dia", 2) if isinstance(porciones_raw, dict) else 2,
        porcion_por_comida_gramos=porciones_raw.get("porcion_por_comida_gramos") if isinstance(porciones_raw, dict) else None,
    )

    # Sección 4: Instrucciones
    instr_raw = content.get("instrucciones_preparacion", {})
    instrucciones = PreparationSection(
        pasos=instr_raw.get("pasos", []) if isinstance(instr_raw, dict) else [],
        tiempo_estimado_minutos=instr_raw.get("tiempo_estimado_minutos") if isinstance(instr_raw, dict) else None,
    )

    # Sección 5: Transición (condicional)
    trans_raw = content.get("transicion_dieta")
    transicion = TransitionSection(**trans_raw) if isinstance(trans_raw, dict) else None

    return PlanResponse(
        plan_id=plan.plan_id,
        pet_id=plan.pet_id,
        owner_id=plan.owner_id,
        plan_type=plan.plan_type.value if hasattr(plan.plan_type, "value") else str(plan.plan_type),
        status=plan.status.value if hasattr(plan.status, "value") else str(plan.status),
        modality=plan.modality.value if hasattr(plan.modality, "value") else str(plan.modality),
        llm_model_used=plan.llm_model_used,
        perfil_nutricional=perfil,
        ingredientes=IngredientsSection(items=items),
        porciones=porciones,
        instrucciones_preparacion=instrucciones,
        transicion_dieta=transicion,
        approved_by_vet_id=plan.approved_by_vet_id,
        review_date=plan.review_date,
        vet_comment=plan.vet_comment,
    )


def _plan_to_summary(plan: Any) -> PlanSummaryResponse:
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
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/v1/plans/generate", response_model=PlanJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_plan(
    body: PlanGenerateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> PlanJobResponse:
    """Encola job de generación de plan. Retorna job_id para polling."""
    try:
        uc = _gen_use_case(session)
        job_id = await uc.enqueue(
            pet_id=body.pet_id,
            owner_id=user.user_id,
            user_tier=user.tier,
            modality=body.modality,
        )
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
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> dict:
    """Vet aprueba plan PENDING_VET → ACTIVE."""
    try:
        uc = _hitl_use_case(session)
        return await uc.approve(
            plan_id=plan_id, vet_id=user.user_id, review_date=body.review_date
        )
    except DomainError as e:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY if "review_date" in str(e).lower() or "revisión" in str(e).lower() else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=str(e)) from e


@router.patch("/v1/plans/{plan_id}/return", response_model=dict)
async def return_plan(
    plan_id: uuid.UUID,
    body: PlanReturnRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> dict:
    """Vet devuelve plan al owner con comentario obligatorio."""
    try:
        uc = _hitl_use_case(session)
        return await uc.return_to_owner(
            plan_id=plan_id, vet_id=user.user_id, comment=body.comment
        )
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


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
    """Lista planes PENDING_VET para el dashboard del vet."""
    plan_repo = PostgreSQLPlanRepository(session)
    plans = await plan_repo.list_pending_vet()
    return [_plan_to_summary(p) for p in plans]


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
    """
    from backend.infrastructure.db.models import PetModel as PetORM
    pet_repo = PostgreSQLPetRepository(session)

    # Query directa al ORM para acceder a owner_name_hint y owner_phone_hint
    stmt = select(PetORM).where(
        PetORM.vet_id == user.user_id,
        PetORM.is_clinic_pet.is_(True),
        PetORM.is_active.is_(True),
    )
    result = await session.execute(stmt)
    models = result.scalars().all()

    responses: list[PetResponse] = []
    for model in models:
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
            claim_code=claim_code,
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
