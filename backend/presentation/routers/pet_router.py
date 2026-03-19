"""
Router de mascotas — FastAPI.
8 endpoints: CRUD de AppPet, weight tracking, ClinicPet, claim.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.use_cases.pet_claim_use_case import PetClaimUseCase
from backend.application.use_cases.pet_profile_use_case import PetProfileUseCase
from backend.application.use_cases.weight_tracking_use_case import WeightTrackingUseCase
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import TokenPayload
from backend.infrastructure.db.claim_code_repository import PostgreSQLClaimCodeRepository
from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
from backend.infrastructure.db.session import get_db_session
from backend.infrastructure.db.weight_repository import PostgreSQLWeightRepository
from backend.domain.value_objects.bcs import BCS
from backend.presentation.middleware.auth_middleware import get_current_user, require_role
from backend.presentation.schemas.pet_schemas import (
    ClaimCodeResponse,
    ClaimPetRequest,
    ClaimPetResponse,
    ClinicPetRequest,
    PetCreateRequest,
    PetResponse,
    PetUpdateRequest,
    WeightRecordRequest,
    WeightRecordResponse,
)

router = APIRouter(prefix="/v1/pets", tags=["pets"])


def _pet_use_case(session: AsyncSession) -> PetProfileUseCase:
    return PetProfileUseCase(pet_repo=PostgreSQLPetRepository(session))


def _weight_use_case(session: AsyncSession) -> WeightTrackingUseCase:
    return WeightTrackingUseCase(
        weight_repo=PostgreSQLWeightRepository(session),
        pet_repo=PostgreSQLPetRepository(session),
    )


def _claim_use_case(session: AsyncSession) -> PetClaimUseCase:
    return PetClaimUseCase(
        pet_repo=PostgreSQLPetRepository(session),
        claim_repo=PostgreSQLClaimCodeRepository(session),
    )


def _to_pet_data(body: PetCreateRequest) -> dict:
    from backend.domain.aggregates.pet_profile import (
        CatActivityLevel, DogActivityLevel,
    )
    # Parsear activity_level según especie
    try:
        if body.species.value == "perro":
            activity = DogActivityLevel(body.activity_level)
        else:
            activity = CatActivityLevel(body.activity_level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Nivel de actividad inválido para {body.species.value}: '{body.activity_level}'",
        )
    return {
        "name": body.name,
        "species": body.species,
        "breed": body.breed,
        "sex": body.sex,
        "age_months": body.age_months,
        "weight_kg": body.weight_kg,
        "size": body.size,
        "reproductive_status": body.reproductive_status,
        "activity_level": activity,
        "bcs": BCS(body.bcs),
        "medical_conditions": body.medical_conditions,
        "allergies": body.allergies,
        "current_diet": body.current_diet,
    }


def _pet_to_response(pet) -> PetResponse:
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
    )


@router.post("", response_model=PetResponse, status_code=status.HTTP_201_CREATED)
async def create_pet(
    body: PetCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> PetResponse:
    """Crear mascota para el owner autenticado."""
    try:
        uc = _pet_use_case(session)
        pet = await uc.create_pet(
            owner_id=user.user_id,
            pet_data=_to_pet_data(body),
            user_tier=user.tier,
        )
        return _pet_to_response(pet)
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("", response_model=list[PetResponse])
async def list_pets(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> list[PetResponse]:
    """Listar mascotas del owner autenticado."""
    uc = _pet_use_case(session)
    pets = await uc.list_pets(owner_id=user.user_id)
    return [_pet_to_response(p) for p in pets]


@router.get("/{pet_id}", response_model=PetResponse)
async def get_pet(
    pet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> PetResponse:
    """Obtener mascota por ID (owner ve las suyas, vet ve cualquiera)."""
    try:
        uc = _pet_use_case(session)
        pet = await uc.get_pet(
            pet_id=pet_id,
            requester_id=user.user_id,
            requester_role=user.role.value,
        )
        return _pet_to_response(pet)
    except DomainError as e:
        status_code = status.HTTP_404_NOT_FOUND if "no encontrada" in str(e) else status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=str(e)) from e


@router.patch("/{pet_id}", response_model=PetResponse)
async def update_pet(
    pet_id: uuid.UUID,
    body: PetUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> PetResponse:
    """Actualizar datos de la mascota."""
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if "bcs" in update_data:
        update_data["bcs"] = BCS(update_data["bcs"])
    try:
        uc = _pet_use_case(session)
        pet = await uc.update_pet(pet_id=pet_id, update_data=update_data, requester_id=user.user_id)
        return _pet_to_response(pet)
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("/{pet_id}/weight", response_model=WeightRecordResponse, status_code=201)
async def add_weight(
    pet_id: uuid.UUID,
    body: WeightRecordRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> WeightRecordResponse:
    """Agregar registro de peso (append-only)."""
    try:
        uc = _weight_use_case(session)
        record_id = await uc.add_weight_record(
            pet_id=pet_id,
            requester_id=user.user_id,
            weight_kg=body.weight_kg,
            bcs=BCS(body.bcs) if body.bcs else None,
        )
        return WeightRecordResponse(record_id=record_id)
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.get("/{pet_id}/weight")
async def get_weight_history(
    pet_id: uuid.UUID,
    limit: int = 30,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> list[dict]:
    """Historial de peso paginado."""
    try:
        uc = _weight_use_case(session)
        return await uc.get_weight_history(
            pet_id=pet_id, requester_id=user.user_id, limit=limit, offset=offset
        )
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("/clinic", response_model=ClaimCodeResponse, status_code=201)
async def create_clinic_pet(
    body: ClinicPetRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("vet")),
) -> ClaimCodeResponse:
    """Crear ClinicPet y generar claim code (solo vets con tier Vet)."""
    try:
        uc = _claim_use_case(session)
        result = await uc.create_clinic_pet(
            vet_id=user.user_id,
            vet_tier=user.tier,
            pet_data=_to_pet_data(body.pet_data),
            owner_name=body.owner_name,
            owner_phone=body.owner_phone,
        )
        return ClaimCodeResponse(pet_id=result["pet_id"], claim_code=result["claim_code"])
    except DomainError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post("/claim", response_model=ClaimPetResponse)
async def claim_pet(
    body: ClaimPetRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> ClaimPetResponse:
    """Reclamar mascota clínica con código."""
    try:
        uc = _claim_use_case(session)
        result = await uc.claim_pet(code=body.code, owner_id=user.user_id)
        return ClaimPetResponse(pet_id=result["pet_id"])
    except DomainError as e:
        status_code = (
            status.HTTP_410_GONE if "expirado" in str(e)
            else status.HTTP_409_CONFLICT if "usado" in str(e)
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=status_code, detail=str(e)) from e
