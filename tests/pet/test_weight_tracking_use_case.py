"""Tests RED — WeightTrackingUseCase (unit-03-pet-service Paso 4)."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from backend.application.interfaces.weight_repository import IWeightRepository
from backend.application.use_cases.weight_tracking_use_case import WeightTrackingUseCase
from backend.domain.exceptions.domain_errors import DomainError


@pytest.fixture
def mock_weight_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.append = AsyncMock(return_value=uuid.uuid4())
    repo.list_by_pet = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_pet_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def use_case(mock_weight_repo: AsyncMock, mock_pet_repo: AsyncMock) -> WeightTrackingUseCase:
    return WeightTrackingUseCase(weight_repo=mock_weight_repo, pet_repo=mock_pet_repo)


class TestWeightTracking:

    @pytest.mark.asyncio
    async def test_peso_append_only(
        self, use_case: WeightTrackingUseCase, mock_weight_repo: AsyncMock, mock_pet_repo: AsyncMock
    ) -> None:
        """Agregar registro de peso → record_id retornado."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS

        owner_id = uuid.uuid4()
        pet = PetProfile(
            pet_id=uuid.uuid4(), owner_id=owner_id,
            name="Max", species=Species.PERRO, breed="Lab",
            sex=Sex.MACHO, age_months=24, weight_kg=28.0,
            size=Size.GRANDE, reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.MODERADO, bcs=BCS(5),
            medical_conditions=[], allergies=[], current_diet=CurrentDiet.CONCENTRADO,
        )
        mock_pet_repo.find_by_id.return_value = pet

        record_id = await use_case.add_weight_record(
            pet_id=pet.pet_id,
            requester_id=owner_id,
            weight_kg=29.0,
            bcs=BCS(5),
        )
        assert record_id is not None
        mock_weight_repo.append.assert_called_once()

    @pytest.mark.asyncio
    async def test_peso_negativo_rechazado(
        self, use_case: WeightTrackingUseCase
    ) -> None:
        """Peso negativo → DomainError."""
        with pytest.raises(DomainError):
            await use_case.add_weight_record(
                pet_id=uuid.uuid4(),
                requester_id=uuid.uuid4(),
                weight_kg=-5.0,
                bcs=None,
            )

    @pytest.mark.asyncio
    async def test_historial_paginado_default_30(
        self, use_case: WeightTrackingUseCase, mock_weight_repo: AsyncMock, mock_pet_repo: AsyncMock
    ) -> None:
        """Historial de peso retorna máximo 30 registros por defecto."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS

        owner_id = uuid.uuid4()
        pet = PetProfile(
            pet_id=uuid.uuid4(), owner_id=owner_id,
            name="Max", species=Species.PERRO, breed="Lab",
            sex=Sex.MACHO, age_months=24, weight_kg=28.0,
            size=Size.GRANDE, reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.MODERADO, bcs=BCS(5),
            medical_conditions=[], allergies=[], current_diet=CurrentDiet.CONCENTRADO,
        )
        mock_pet_repo.find_by_id.return_value = pet

        await use_case.get_weight_history(
            pet_id=pet.pet_id, requester_id=owner_id
        )
        call_kwargs = mock_weight_repo.list_by_pet.call_args
        assert call_kwargs.kwargs.get("limit", call_kwargs.args[1] if len(call_kwargs.args) > 1 else 30) == 30

    def test_no_existe_metodo_update_weight(self) -> None:
        """IWeightRepository no debe tener método update()."""
        assert not hasattr(IWeightRepository, "update"), (
            "IWeightRepository no debe tener update() — weight tracking es append-only."
        )

    @pytest.mark.asyncio
    async def test_owner_puede_ver_historial_propio(
        self, use_case: WeightTrackingUseCase, mock_weight_repo: AsyncMock, mock_pet_repo: AsyncMock
    ) -> None:
        """Owner puede ver el historial de su propia mascota."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS

        owner_id = uuid.uuid4()
        pet = PetProfile(
            pet_id=uuid.uuid4(), owner_id=owner_id,
            name="Max", species=Species.PERRO, breed="Lab",
            sex=Sex.MACHO, age_months=24, weight_kg=28.0,
            size=Size.GRANDE, reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.MODERADO, bcs=BCS(5),
            medical_conditions=[], allergies=[], current_diet=CurrentDiet.CONCENTRADO,
        )
        mock_pet_repo.find_by_id.return_value = pet

        result = await use_case.get_weight_history(
            pet_id=pet.pet_id, requester_id=owner_id
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_owner_no_puede_ver_historial_ajeno(
        self, use_case: WeightTrackingUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Owner no puede ver el historial de mascota ajena → DomainError."""
        from backend.domain.aggregates.pet_profile import (
            CurrentDiet, DogActivityLevel, PetProfile,
            ReproductiveStatus, Sex, Size, Species,
        )
        from backend.domain.value_objects.bcs import BCS

        real_owner_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        pet = PetProfile(
            pet_id=uuid.uuid4(), owner_id=real_owner_id,
            name="Max", species=Species.PERRO, breed="Lab",
            sex=Sex.MACHO, age_months=24, weight_kg=28.0,
            size=Size.GRANDE, reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.MODERADO, bcs=BCS(5),
            medical_conditions=[], allergies=[], current_diet=CurrentDiet.CONCENTRADO,
        )
        mock_pet_repo.find_by_id.return_value = pet

        with pytest.raises(DomainError, match="(?i)acceso"):
            await use_case.get_weight_history(
                pet_id=pet.pet_id, requester_id=other_user_id
            )
