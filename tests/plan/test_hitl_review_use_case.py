"""Tests RED — HitlReviewUseCase (unit-04-plan-service Paso 5).

Constitution REGLA 4:
  - Solo mascotas con condición médica → PENDING_VET.
  - Vet aprueba → ACTIVE.
  - Vet devuelve con comentario obligatorio → permanece PENDING_VET.
  - No existe estado RECHAZADO.
"""
from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.application.use_cases.hitl_review_use_case import HitlReviewUseCase
from backend.domain.aggregates.nutrition_plan import NutritionPlan, PlanStatus, PlanType, PlanModality
from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.value_objects.bcs import BCSPhase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(
    status: PlanStatus = PlanStatus.PENDING_VET,
    plan_type: PlanType = PlanType.ESTANDAR,
) -> NutritionPlan:
    return NutritionPlan(
        plan_id=uuid.uuid4(),
        pet_id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        plan_type=plan_type,
        status=status,
        modality=PlanModality.CONCENTRADO,
        rer_kcal=396.0,
        der_kcal=534.0,
        weight_phase=BCSPhase.MANTENIMIENTO,
        llm_model_used="anthropic/claude-sonnet-4-5",
        content={"secciones": []},
        approved_by_vet_id=None,
        approval_timestamp=None,
        review_date=None,
        vet_comment=None,
        agent_trace_id=uuid.uuid4(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_plan_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def use_case(mock_plan_repo: AsyncMock) -> HitlReviewUseCase:
    return HitlReviewUseCase(plan_repo=mock_plan_repo)


# ---------------------------------------------------------------------------
# Tests: approve
# ---------------------------------------------------------------------------

class TestHitlApprove:

    @pytest.mark.asyncio
    async def test_vet_aprueba_plan_standard(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Vet aprueba plan PENDING_VET → ACTIVE."""
        plan = _make_plan(status=PlanStatus.PENDING_VET)
        vet_id = uuid.uuid4()
        mock_plan_repo.find_by_id.return_value = plan

        result = await use_case.approve(plan_id=plan.plan_id, vet_id=vet_id)
        assert result["status"] == PlanStatus.ACTIVE.value
        assert result["approved_by_vet_id"] == vet_id
        mock_plan_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_vet_aprueba_con_review_date_temporal_medical(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Plan TEMPORAL_MEDICAL aprobado con review_date → ACTIVE con fecha."""
        plan = _make_plan(plan_type=PlanType.TEMPORAL_MEDICAL)
        vet_id = uuid.uuid4()
        review_date = date(2026, 6, 1)
        mock_plan_repo.find_by_id.return_value = plan

        result = await use_case.approve(
            plan_id=plan.plan_id, vet_id=vet_id, review_date=review_date
        )
        assert result["status"] == PlanStatus.ACTIVE.value
        assert result["review_date"] == str(review_date)

    @pytest.mark.asyncio
    async def test_vet_aprueba_temporal_sin_review_date_falla(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Plan TEMPORAL_MEDICAL sin review_date → DomainError."""
        plan = _make_plan(plan_type=PlanType.TEMPORAL_MEDICAL)
        mock_plan_repo.find_by_id.return_value = plan

        with pytest.raises(DomainError, match="(?i)review_date|revisión"):
            await use_case.approve(plan_id=plan.plan_id, vet_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_aprobar_plan_ya_activo_falla(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Aprobar plan ya ACTIVE → DomainError."""
        plan = _make_plan(status=PlanStatus.ACTIVE)
        mock_plan_repo.find_by_id.return_value = plan

        with pytest.raises(DomainError, match="(?i)PENDING_VET"):
            await use_case.approve(plan_id=plan.plan_id, vet_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_plan_no_encontrado_falla(
        self, use_case: HitlReviewUseCase
    ) -> None:
        """Plan no existe → DomainError."""
        with pytest.raises(DomainError, match="(?i)plan"):
            await use_case.approve(plan_id=uuid.uuid4(), vet_id=uuid.uuid4())


# ---------------------------------------------------------------------------
# Tests: return_to_owner
# ---------------------------------------------------------------------------

class TestHitlReturn:

    @pytest.mark.asyncio
    async def test_vet_devuelve_con_comentario(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Vet devuelve con comentario → permanece PENDING_VET con comentario."""
        plan = _make_plan(status=PlanStatus.PENDING_VET)
        vet_id = uuid.uuid4()
        comment = "Ajustar porción de proteína para condición renal."
        mock_plan_repo.find_by_id.return_value = plan

        result = await use_case.return_to_owner(
            plan_id=plan.plan_id, vet_id=vet_id, comment=comment
        )
        assert result["status"] == PlanStatus.PENDING_VET.value
        assert result["vet_comment"] == comment

    @pytest.mark.asyncio
    async def test_vet_devuelve_requiere_comentario(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Comentario vacío al devolver → DomainError."""
        plan = _make_plan(status=PlanStatus.PENDING_VET)
        mock_plan_repo.find_by_id.return_value = plan

        with pytest.raises(DomainError, match="(?i)comentario"):
            await use_case.return_to_owner(
                plan_id=plan.plan_id, vet_id=uuid.uuid4(), comment=""
            )

    @pytest.mark.asyncio
    async def test_devolver_plan_activo_falla(
        self, use_case: HitlReviewUseCase, mock_plan_repo: AsyncMock
    ) -> None:
        """Devolver plan ACTIVE → DomainError."""
        plan = _make_plan(status=PlanStatus.ACTIVE)
        mock_plan_repo.find_by_id.return_value = plan

        with pytest.raises(DomainError, match="(?i)PENDING_VET"):
            await use_case.return_to_owner(
                plan_id=plan.plan_id, vet_id=uuid.uuid4(), comment="Algún comentario"
            )
