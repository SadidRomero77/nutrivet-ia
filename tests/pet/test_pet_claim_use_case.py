"""Tests RED — PetClaimUseCase (unit-03-pet-service Paso 3)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from backend.application.use_cases.pet_claim_use_case import PetClaimUseCase
from backend.domain.aggregates.pet_profile import (
    CurrentDiet,
    DogActivityLevel,
    ReproductiveStatus,
    Sex,
    Size,
    Species,
)
from backend.domain.aggregates.user_account import UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.value_objects.bcs import BCS


def _dog_data(**overrides) -> dict:
    base = {
        "name": "Rex",
        "species": Species.PERRO,
        "breed": "Pastor",
        "sex": Sex.MACHO,
        "age_months": 12,
        "weight_kg": 20.0,
        "size": Size.GRANDE,
        "reproductive_status": ReproductiveStatus.NO_ESTERILIZADO,
        "activity_level": DogActivityLevel.ACTIVO,
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
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_claim_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_code = AsyncMock(return_value=None)
    repo.mark_used = AsyncMock()
    return repo


@pytest.fixture
def use_case(mock_pet_repo: AsyncMock, mock_claim_repo: AsyncMock) -> PetClaimUseCase:
    return PetClaimUseCase(pet_repo=mock_pet_repo, claim_repo=mock_claim_repo)


class TestCreateClinicPet:

    @pytest.mark.asyncio
    async def test_create_clinic_pet(
        self, use_case: PetClaimUseCase, mock_pet_repo: AsyncMock, mock_claim_repo: AsyncMock
    ) -> None:
        """Vet crea ClinicPet → claim_code de 8 chars retornado."""
        result = await use_case.create_clinic_pet(
            vet_id=uuid.uuid4(),
            vet_tier=UserTier.VET,
            pet_data=_dog_data(),
            owner_name="Juan Pérez",
            owner_phone="+573001234567",
        )
        assert "claim_code" in result
        assert len(result["claim_code"]) == 8
        mock_pet_repo.save.assert_called_once()
        mock_claim_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_vet_free_no_puede_crear_clinic_pet(
        self, use_case: PetClaimUseCase
    ) -> None:
        """Vet con tier Free → DomainError (requiere tier Vet)."""
        with pytest.raises(DomainError, match="(?i)tier"):
            await use_case.create_clinic_pet(
                vet_id=uuid.uuid4(),
                vet_tier=UserTier.FREE,
                pet_data=_dog_data(),
                owner_name="Juan",
                owner_phone="+57300",
            )

    @pytest.mark.asyncio
    async def test_claim_code_8_chars_alfanumerico(
        self, use_case: PetClaimUseCase
    ) -> None:
        """El claim code tiene exactamente 8 caracteres alfanuméricos."""
        result = await use_case.create_clinic_pet(
            vet_id=uuid.uuid4(),
            vet_tier=UserTier.VET,
            pet_data=_dog_data(),
            owner_name="Juan",
            owner_phone="+57300",
        )
        code = result["claim_code"]
        assert len(code) == 8
        assert code.isalnum()

    @pytest.mark.asyncio
    async def test_claim_code_no_contiene_cero_ni_O(
        self, use_case: PetClaimUseCase
    ) -> None:
        """El claim code excluye '0' y 'O' para evitar confusión visual."""
        codes = []
        for _ in range(20):
            result = await use_case.create_clinic_pet(
                vet_id=uuid.uuid4(),
                vet_tier=UserTier.VET,
                pet_data=_dog_data(),
                owner_name="Juan",
                owner_phone="+57300",
            )
            codes.append(result["claim_code"])
        for code in codes:
            assert "0" not in code
            assert "O" not in code


class TestClaimPet:

    @pytest.mark.asyncio
    async def test_claim_code_expira_30_dias(
        self, use_case: PetClaimUseCase, mock_claim_repo: AsyncMock
    ) -> None:
        """Claim code con fecha pasada → DomainError (expirado)."""
        mock_claim_repo.find_by_code.return_value = {
            "pet_id": uuid.uuid4(),
            "code": "ABCD1234",
            "used": False,
            "expires_at": datetime.now(timezone.utc) - timedelta(days=1),
        }
        with pytest.raises(DomainError, match="(?i)expir"):
            await use_case.claim_pet(code="ABCD1234", owner_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_claim_code_un_solo_uso(
        self, use_case: PetClaimUseCase, mock_claim_repo: AsyncMock
    ) -> None:
        """Claim code ya usado → DomainError."""
        mock_claim_repo.find_by_code.return_value = {
            "pet_id": uuid.uuid4(),
            "code": "ABCD1234",
            "used": True,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=10),
        }
        with pytest.raises(DomainError, match="(?i)usado"):
            await use_case.claim_pet(code="ABCD1234", owner_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_claim_convierte_clinic_pet_en_app_pet(
        self, use_case: PetClaimUseCase, mock_claim_repo: AsyncMock, mock_pet_repo: AsyncMock
    ) -> None:
        """Claim exitoso asigna owner_id a la mascota y marca código como usado."""
        from backend.domain.aggregates.pet_profile import PetProfile

        pet_id = uuid.uuid4()
        owner_id = uuid.uuid4()
        pet = PetProfile(pet_id=pet_id, owner_id=uuid.uuid4(), **_dog_data())
        mock_pet_repo.find_by_id.return_value = pet
        mock_claim_repo.find_by_code.return_value = {
            "pet_id": pet_id,
            "code": "ABCD1234",
            "used": False,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=20),
        }

        result = await use_case.claim_pet(code="ABCD1234", owner_id=owner_id)

        assert result["pet_id"] == pet_id
        mock_claim_repo.mark_used.assert_called_once()
        mock_pet_repo.update.assert_called_once()
