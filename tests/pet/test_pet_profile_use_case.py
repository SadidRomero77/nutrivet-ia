"""Tests RED — PetProfileUseCase (unit-03-pet-service Paso 2)."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.pet_profile_use_case import PetProfileUseCase
from backend.domain.aggregates.pet_profile import (
    CatActivityLevel,
    CurrentDiet,
    DogActivityLevel,
    MedicalCondition,
    ReproductiveStatus,
    Sex,
    Size,
    Species,
)
from backend.domain.aggregates.user_account import UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.value_objects.bcs import BCS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dog_data(**overrides) -> dict:
    base = {
        "name": "Max",
        "species": Species.PERRO,
        "breed": "Labrador",
        "sex": Sex.MACHO,
        "age_months": 24,
        "weight_kg": 28.0,
        "size": Size.GRANDE,
        "reproductive_status": ReproductiveStatus.ESTERILIZADO,
        "activity_level": DogActivityLevel.MODERADO,
        "bcs": BCS(5),
        "medical_conditions": [],
        "allergies": [],
        "current_diet": CurrentDiet.CONCENTRADO,
    }
    base.update(overrides)
    return base


def _cat_data(**overrides) -> dict:
    base = {
        "name": "Luna",
        "species": Species.GATO,
        "breed": "Común europeo",
        "sex": Sex.HEMBRA,
        "age_months": 36,
        "weight_kg": 4.0,
        "size": None,
        "reproductive_status": ReproductiveStatus.ESTERILIZADO,
        "activity_level": CatActivityLevel.INDOOR,
        "bcs": BCS(5),
        "medical_conditions": [],
        "allergies": [],
        "current_diet": CurrentDiet.CONCENTRADO,
    }
    base.update(overrides)
    return base


@pytest.fixture
def mock_pet_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.list_by_owner = AsyncMock(return_value=[])
    repo.count_by_owner = AsyncMock(return_value=0)
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def use_case(mock_pet_repo: AsyncMock) -> PetProfileUseCase:
    return PetProfileUseCase(pet_repo=mock_pet_repo)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCrearMascota:

    @pytest.mark.asyncio
    async def test_crear_mascota_valida(
        self, use_case: PetProfileUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Owner crea mascota con 13 campos → pet_id retornado."""
        owner_id = uuid.uuid4()
        pet = await use_case.create_pet(
            owner_id=owner_id,
            pet_data=_dog_data(),
            user_tier=UserTier.FREE,
        )
        assert pet is not None
        assert pet.pet_id is not None
        mock_pet_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_free_tier_no_puede_crear_segunda_mascota(
        self, use_case: PetProfileUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Free tier: ya tiene 1 mascota → DomainError al intentar crear otra."""
        mock_pet_repo.count_by_owner.return_value = 1
        import backend.application.use_cases.pet_profile_use_case as _mod
        original = _mod.MVP_FREEMIUM_DISABLED
        _mod.MVP_FREEMIUM_DISABLED = False
        try:
            with pytest.raises(DomainError, match="(?i)límite"):
                await use_case.create_pet(
                    owner_id=uuid.uuid4(),
                    pet_data=_dog_data(),
                    user_tier=UserTier.FREE,
                )
        finally:
            _mod.MVP_FREEMIUM_DISABLED = original

    @pytest.mark.asyncio
    async def test_premium_puede_crear_hasta_3_mascotas(
        self, use_case: PetProfileUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Premium con 2 mascotas puede crear la tercera."""
        mock_pet_repo.count_by_owner.return_value = 2
        pet = await use_case.create_pet(
            owner_id=uuid.uuid4(),
            pet_data=_dog_data(),
            user_tier=UserTier.PREMIUM,
        )
        assert pet is not None

    @pytest.mark.asyncio
    async def test_talla_solo_requerida_para_perros(
        self, use_case: PetProfileUseCase
    ) -> None:
        """Perro sin talla → DomainError."""
        with pytest.raises(DomainError, match="(?i)talla"):
            await use_case.create_pet(
                owner_id=uuid.uuid4(),
                pet_data=_dog_data(size=None),
                user_tier=UserTier.FREE,
            )

    @pytest.mark.asyncio
    async def test_gato_sin_talla_es_valido(
        self, use_case: PetProfileUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Gato sin talla (size=None) es válido."""
        pet = await use_case.create_pet(
            owner_id=uuid.uuid4(),
            pet_data=_cat_data(),
            user_tier=UserTier.FREE,
        )
        assert pet is not None

    @pytest.mark.asyncio
    async def test_activity_level_valido_por_especie(
        self, use_case: PetProfileUseCase
    ) -> None:
        """Nivel de actividad 'indoor' (gato) en perro → DomainError."""
        with pytest.raises(DomainError, match="(?i)actividad"):
            await use_case.create_pet(
                owner_id=uuid.uuid4(),
                pet_data=_dog_data(activity_level=CatActivityLevel.INDOOR),
                user_tier=UserTier.FREE,
            )

    @pytest.mark.asyncio
    async def test_bcs_fuera_de_rango_falla(
        self, use_case: PetProfileUseCase
    ) -> None:
        """BCS fuera de rango 1-9 → DomainError en construcción del BCS."""
        with pytest.raises(DomainError):
            BCS(0)

    @pytest.mark.asyncio
    async def test_peso_negativo_falla(
        self, use_case: PetProfileUseCase
    ) -> None:
        """Peso negativo → DomainError."""
        with pytest.raises(DomainError):
            await use_case.create_pet(
                owner_id=uuid.uuid4(),
                pet_data=_dog_data(weight_kg=-1.0),
                user_tier=UserTier.FREE,
            )

    @pytest.mark.asyncio
    async def test_condicion_medica_invalida_falla(
        self, use_case: PetProfileUseCase
    ) -> None:
        """Condición médica desconocida → error."""
        with pytest.raises((DomainError, ValueError)):
            await use_case.create_pet(
                owner_id=uuid.uuid4(),
                pet_data=_dog_data(medical_conditions=["condicion_inexistente"]),
                user_tier=UserTier.FREE,
            )

    @pytest.mark.asyncio
    async def test_condicion_medica_agrega_a_plan_activo_dispara_pending_vet(
        self, use_case: PetProfileUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Agregar condición médica a mascota retorna requires_vet_review=True."""
        from backend.domain.aggregates.pet_profile import PetProfile

        pet = PetProfile(
            pet_id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            **_dog_data(medical_conditions=[]),
        )
        mock_pet_repo.find_by_id.return_value = pet

        result = await use_case.add_medical_condition(
            pet_id=pet.pet_id,
            requester_id=pet.owner_id,
            condition=MedicalCondition.DIABETICO,
        )
        assert result["requires_vet_review"] is True
