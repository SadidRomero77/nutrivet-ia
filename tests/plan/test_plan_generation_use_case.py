"""Tests RED — PlanGenerationUseCase (unit-04-plan-service Paso 4)."""
from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.application.use_cases.plan_generation_use_case import PlanGenerationUseCase
from backend.domain.aggregates.nutrition_plan import PlanStatus, PlanType
from backend.domain.aggregates.user_account import UserTier
from backend.domain.exceptions.domain_errors import DomainError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pet_stub(has_conditions: bool = False):
    """Crea un stub mínimo de PetProfile para los tests."""
    pet = MagicMock()
    pet.pet_id = uuid.uuid4()
    pet.owner_id = uuid.uuid4()
    pet.species = MagicMock(value="perro")
    pet.weight_kg = 28.0
    pet.age_months = 24
    pet.bcs = MagicMock(value=5)
    pet.reproductive_status = MagicMock(value="esterilizado")
    pet.activity_level = MagicMock(value="moderado")
    pet.medical_conditions = [MagicMock()] if has_conditions else []
    pet.allergies = []
    return pet


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_plan_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.find_active_by_pet = AsyncMock(return_value=None)
    repo.list_by_owner = AsyncMock(return_value=[])
    repo.count_active_by_owner = AsyncMock(return_value=0)
    return repo


@pytest.fixture
def mock_job_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_pet_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_trace_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.append = AsyncMock(return_value=uuid.uuid4())
    return repo


@pytest.fixture
def use_case(
    mock_plan_repo: AsyncMock,
    mock_job_repo: AsyncMock,
    mock_pet_repo: AsyncMock,
    mock_trace_repo: AsyncMock,
) -> PlanGenerationUseCase:
    return PlanGenerationUseCase(
        plan_repo=mock_plan_repo,
        job_repo=mock_job_repo,
        pet_repo=mock_pet_repo,
        trace_repo=mock_trace_repo,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPlanGenerationEnqueue:

    @pytest.mark.asyncio
    async def test_encolar_plan_retorna_job_id(
        self, use_case: PlanGenerationUseCase, mock_pet_repo: AsyncMock, mock_job_repo: AsyncMock
    ) -> None:
        """Solicitar plan → retorna job_id para polling."""
        pet = _make_pet_stub(has_conditions=False)
        mock_pet_repo.find_by_id.return_value = pet

        job_id = await use_case.enqueue(
            pet_id=pet.pet_id,
            owner_id=pet.owner_id,
            user_tier=UserTier.FREE,
            modality="concentrado",
        )
        assert job_id is not None
        mock_job_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_pet_no_encontrada_falla(
        self, use_case: PlanGenerationUseCase
    ) -> None:
        """Pet no existe → DomainError."""
        with pytest.raises(DomainError, match="(?i)mascota"):
            await use_case.enqueue(
                pet_id=uuid.uuid4(),
                owner_id=uuid.uuid4(),
                user_tier=UserTier.FREE,
                modality="concentrado",
            )

    @pytest.mark.asyncio
    async def test_owner_solo_encola_su_pet(
        self, use_case: PlanGenerationUseCase, mock_pet_repo: AsyncMock
    ) -> None:
        """Owner no puede encolar plan para mascota ajena → DomainError."""
        pet = _make_pet_stub()
        mock_pet_repo.find_by_id.return_value = pet

        with pytest.raises(DomainError, match="(?i)acceso"):
            await use_case.enqueue(
                pet_id=pet.pet_id,
                owner_id=uuid.uuid4(),  # owner distinto
                user_tier=UserTier.FREE,
                modality="concentrado",
            )

    @pytest.mark.asyncio
    async def test_free_tier_segundo_plan_falla(
        self, use_case: PlanGenerationUseCase, mock_pet_repo: AsyncMock, mock_plan_repo: AsyncMock
    ) -> None:
        """Free tier: ya tiene 1 plan activo → DomainError al intentar generar otro."""
        pet = _make_pet_stub()
        mock_pet_repo.find_by_id.return_value = pet
        mock_plan_repo.count_active_by_owner.return_value = 1  # ya tiene 1

        with pytest.raises(DomainError, match="(?i)límite"):
            await use_case.enqueue(
                pet_id=pet.pet_id,
                owner_id=pet.owner_id,
                user_tier=UserTier.FREE,
                modality="concentrado",
            )

    @pytest.mark.asyncio
    async def test_get_job_retorna_status(
        self, use_case: PlanGenerationUseCase, mock_job_repo: AsyncMock
    ) -> None:
        """get_job retorna status del job dado el job_id."""
        job_id = uuid.uuid4()
        job_stub = MagicMock()
        job_stub.job_id = job_id
        job_stub.status = "QUEUED"
        job_stub.plan_id = None
        mock_job_repo.find_by_id.return_value = job_stub

        result = await use_case.get_job(job_id=job_id, requester_id=uuid.uuid4())
        assert result["status"] == "QUEUED"

    @pytest.mark.asyncio
    async def test_get_job_no_encontrado_falla(
        self, use_case: PlanGenerationUseCase
    ) -> None:
        """Job no encontrado → DomainError."""
        with pytest.raises(DomainError, match="(?i)job"):
            await use_case.get_job(job_id=uuid.uuid4(), requester_id=uuid.uuid4())


class TestAgentTraceInmutabilidad:

    def test_agent_traces_no_tiene_update(self) -> None:
        """IAgentTraceRepository NO debe tener método update() — append-only (REGLA 6)."""
        from backend.application.interfaces.agent_trace_repository import IAgentTraceRepository
        assert not hasattr(IAgentTraceRepository, "update"), (
            "IAgentTraceRepository no debe tener update() — agent_traces son inmutables."
        )
