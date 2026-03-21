"""
PostgreSQLPetRepository — Repositorio de mascotas con encriptación AES-256.
Los campos medical_conditions y allergies se encriptan con Fernet antes de persistir.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.pet_repository import IPetRepository
from backend.domain.aggregates.pet_profile import (
    BCS,
    CatActivityLevel,
    CurrentDiet,
    DogActivityLevel,
    MedicalCondition,
    PetProfile,
    ReproductiveStatus,
    Sex,
    Size,
    Species,
)
from backend.infrastructure.db.models import PetModel
from backend.infrastructure.encryption.fernet_encryptor import FernetEncryptor


class PostgreSQLPetRepository(IPetRepository):
    """
    Repositorio de mascotas backed por PostgreSQL vía SQLAlchemy async.

    Encripta campos médicos sensibles antes de persistir (REGLA 6).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._enc = FernetEncryptor()

    async def save(self, pet: PetProfile) -> None:
        """Persiste un PetProfile nuevo con campos médicos encriptados."""
        model = PetModel(
            id=pet.pet_id,
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
            medical_conditions_enc=self._enc.encrypt(
                [c.value for c in pet.medical_conditions]
            ),
            allergies_enc=self._enc.encrypt(pet.allergies),
            current_diet=pet.current_diet.value,
            is_clinic_pet=pet.is_clinic_pet,
            vet_id=pet.vet_id,
        )
        self._session.add(model)

    async def update(self, pet: PetProfile) -> None:
        """Actualiza un PetProfile existente."""
        model = await self._session.get(PetModel, pet.pet_id)
        if model is None:
            return
        model.owner_id = pet.owner_id
        model.name = pet.name
        model.weight_kg = pet.weight_kg
        model.bcs = pet.bcs.value
        model.activity_level = pet.activity_level.value if hasattr(pet.activity_level, 'value') else str(pet.activity_level)
        model.current_diet = pet.current_diet.value if hasattr(pet.current_diet, 'value') else str(pet.current_diet)
        model.medical_conditions_enc = self._enc.encrypt(
            [c.value for c in pet.medical_conditions]
        )
        model.allergies_enc = self._enc.encrypt(pet.allergies)

    async def find_by_id(self, pet_id: uuid.UUID) -> Optional[PetProfile]:
        """Busca mascota por ID y desencripta campos médicos."""
        model = await self._session.get(PetModel, pet_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[PetProfile]:
        """Lista mascotas activas de un owner."""
        stmt = select(PetModel).where(
            PetModel.owner_id == owner_id,
            PetModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        """Cuenta mascotas propias activas de un owner (excluye ClinicPets reclamadas)."""
        from sqlalchemy import func as sa_func
        stmt = select(sa_func.count()).where(
            PetModel.owner_id == owner_id,
            PetModel.is_active.is_(True),
            PetModel.is_clinic_pet.is_(False),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def deactivate(self, pet_id: uuid.UUID) -> None:
        """Soft-delete: marca la mascota como inactiva."""
        model = await self._session.get(PetModel, pet_id)
        if model is not None:
            model.is_active = False

    async def list_clinic_by_vet(self, vet_id: uuid.UUID) -> list[PetProfile]:
        """Lista ClinicPets activos creados por un veterinario."""
        stmt = select(PetModel).where(
            PetModel.vet_id == vet_id,
            PetModel.is_clinic_pet.is_(True),
            PetModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: PetModel) -> PetProfile:
        """Mapea PetModel (ORM) → PetProfile (dominio), desencriptando campos médicos."""
        conditions_raw: list[str] = (
            self._enc.decrypt(model.medical_conditions_enc)
            if model.medical_conditions_enc
            else []
        )
        allergies: list[str] = (
            self._enc.decrypt(model.allergies_enc)
            if model.allergies_enc
            else []
        )
        return PetProfile(
            pet_id=model.id,
            owner_id=model.owner_id,
            name=model.name,
            species=Species(model.species),
            breed=model.breed,
            sex=Sex(model.sex),
            age_months=model.age_months,
            weight_kg=model.weight_kg,
            size=Size(model.size) if model.size else None,
            reproductive_status=ReproductiveStatus(model.reproductive_status),
            activity_level=self._parse_activity(model.species, model.activity_level),
            bcs=BCS(model.bcs),
            medical_conditions=[MedicalCondition(c) for c in conditions_raw],
            allergies=allergies,
            current_diet=CurrentDiet(model.current_diet),
            is_clinic_pet=model.is_clinic_pet,
            vet_id=model.vet_id,
        )

    @staticmethod
    def _parse_activity(
        species: str, activity_level: str
    ) -> DogActivityLevel | CatActivityLevel:
        """Parsea el activity_level según especie."""
        if species == "perro":
            return DogActivityLevel(activity_level)
        return CatActivityLevel(activity_level)
