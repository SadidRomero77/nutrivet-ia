"""Schemas Pydantic para los endpoints de mascotas."""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from backend.domain.aggregates.pet_profile import (
    CurrentDiet,
    MedicalCondition,
    ReproductiveStatus,
    Sex,
    Size,
    Species,
)


class PetCreateRequest(BaseModel):
    """Body de POST /v1/pets."""
    name: str = Field(..., min_length=1, max_length=100)
    species: Species
    breed: str = Field(..., min_length=1, max_length=100)
    sex: Sex
    age_months: int = Field(..., gt=0)
    weight_kg: float = Field(..., gt=0)
    size: Optional[Size] = None
    reproductive_status: ReproductiveStatus
    activity_level: str
    bcs: int = Field(..., ge=1, le=9)
    medical_conditions: list[MedicalCondition] = []
    allergies: list[str] = []
    current_diet: CurrentDiet = CurrentDiet.CONCENTRADO


class PetUpdateRequest(BaseModel):
    """Body de PATCH /v1/pets/{pet_id}."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    weight_kg: Optional[float] = Field(None, gt=0)
    bcs: Optional[int] = Field(None, ge=1, le=9)
    activity_level: Optional[str] = None
    current_diet: Optional[CurrentDiet] = None


class WeightRecordRequest(BaseModel):
    """Body de POST /v1/pets/{pet_id}/weight."""
    weight_kg: float = Field(..., gt=0)
    bcs: Optional[int] = Field(None, ge=1, le=9)


class ClinicPetRequest(BaseModel):
    """Body de POST /v1/pets/clinic (vet only)."""
    pet_data: PetCreateRequest
    owner_name: str = Field(..., min_length=1, max_length=100)
    owner_phone: str = Field(..., min_length=5, max_length=30)


class ClaimPetRequest(BaseModel):
    """Body de POST /v1/pets/claim."""
    code: str = Field(..., min_length=8, max_length=8)


class PetResponse(BaseModel):
    """Respuesta de perfil de mascota."""
    pet_id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    species: str
    breed: str
    sex: str
    age_months: int
    weight_kg: float
    size: Optional[str]
    reproductive_status: str
    activity_level: str
    bcs: int
    medical_conditions: list[str]
    allergies: list[str]
    current_diet: str
    vet_id: Optional[uuid.UUID] = None


class WeightRecordResponse(BaseModel):
    """Respuesta de registro de peso."""
    record_id: uuid.UUID


class ClaimCodeResponse(BaseModel):
    """Respuesta de claim code generado."""
    pet_id: uuid.UUID
    claim_code: str


class ClaimPetResponse(BaseModel):
    """Respuesta de claim exitoso."""
    pet_id: uuid.UUID
