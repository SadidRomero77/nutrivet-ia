"""
Tests RED — ExportPlanUseCase (NUT-92 · Paso 2).

Reglas:
- Solo planes ACTIVE son exportables → 422 para otros estados.
- RBAC: owner_id == user_id o assigned_vet_id == user_id.
- Cache: mismo plan → mismo PDF (no re-genera).
- TTL pre-signed URL: exactamente 3600s.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.aggregates.nutrition_plan import (
    NutritionPlan,
    PlanModality,
    PlanStatus,
    PlanType,
)
from backend.domain.value_objects.bcs import BCSPhase


def _make_plan(
    status: PlanStatus = PlanStatus.ACTIVE,
    owner_id: uuid.UUID | None = None,
    approved_by_vet_id: uuid.UUID | None = None,
) -> NutritionPlan:
    return NutritionPlan(
        plan_id=uuid.uuid4(),
        pet_id=uuid.uuid4(),
        owner_id=owner_id or uuid.uuid4(),
        plan_type=PlanType.ESTANDAR,
        status=status,
        modality=PlanModality.NATURAL,
        rer_kcal=396.0,
        der_kcal=534.0,
        weight_phase=BCSPhase.MANTENIMIENTO,
        llm_model_used="anthropic/claude-sonnet-4-5",
        content={
            "seccion_1_perfil": {"especie": "perro", "peso_kg": 10.0},
            "seccion_2_calorias": {"rer": 396.0, "der": 534.0},
            "seccion_3_ingredientes": [{"nombre": "pollo", "gramos": 150}],
            "seccion_4_transicion": None,
            "seccion_5_sustitutos": [{"original": "pollo", "alternativa": "pavo"}],
            "has_transition_protocol": False,
        },
        approved_by_vet_id=approved_by_vet_id,
        approval_timestamp=datetime.utcnow() if status == PlanStatus.ACTIVE else None,
        review_date=None,
        vet_comment=None,
        agent_trace_id=uuid.uuid4(),
    )


def _mock_plan_repo(plan: NutritionPlan) -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_id.return_value = plan
    return repo


def _mock_pdf_gen(pdf_bytes: bytes = b"%PDF-fake") -> MagicMock:
    gen = MagicMock()
    gen.generate.return_value = pdf_bytes
    return gen


def _mock_storage(exists: bool = False, url: str = "https://r2.example.com/plan.pdf") -> MagicMock:
    client = MagicMock()
    client.exists.return_value = exists
    client.upload.return_value = "pdfs/plan-abc.pdf"
    client.generate_presigned_url.return_value = url
    return client


class TestExportPlanUseCase:

    @pytest.mark.asyncio
    async def test_exportar_plan_active_retorna_url(self) -> None:
        """Plan ACTIVE → URL pre-signed retornada."""
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase

        plan = _make_plan(status=PlanStatus.ACTIVE)
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        result = await uc.export(plan_id=plan.plan_id, user_id=plan.owner_id)
        assert result.url.startswith("https://")
        assert result.expires_at is not None

    @pytest.mark.asyncio
    async def test_exportar_pending_vet_falla(self) -> None:
        """Plan PENDING_VET → ExportNotAllowedError."""
        from backend.application.use_cases.export_plan_use_case import (
            ExportNotAllowedError,
            ExportPlanUseCase,
        )

        plan = _make_plan(status=PlanStatus.PENDING_VET)
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        with pytest.raises(ExportNotAllowedError, match="ACTIVE"):
            await uc.export(plan_id=plan.plan_id, user_id=plan.owner_id)

    @pytest.mark.asyncio
    async def test_exportar_under_review_falla(self) -> None:
        """Plan UNDER_REVIEW → ExportNotAllowedError."""
        from backend.application.use_cases.export_plan_use_case import (
            ExportNotAllowedError,
            ExportPlanUseCase,
        )

        plan = _make_plan(status=PlanStatus.UNDER_REVIEW)
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        with pytest.raises(ExportNotAllowedError):
            await uc.export(plan_id=plan.plan_id, user_id=plan.owner_id)

    @pytest.mark.asyncio
    async def test_exportar_archived_falla(self) -> None:
        """Plan ARCHIVED → ExportNotAllowedError."""
        from backend.application.use_cases.export_plan_use_case import (
            ExportNotAllowedError,
            ExportPlanUseCase,
        )

        plan = _make_plan(status=PlanStatus.ARCHIVED)
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        with pytest.raises(ExportNotAllowedError):
            await uc.export(plan_id=plan.plan_id, user_id=plan.owner_id)

    @pytest.mark.asyncio
    async def test_owner_puede_exportar(self) -> None:
        """owner_id == user_id → permitido."""
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase

        owner_id = uuid.uuid4()
        plan = _make_plan(status=PlanStatus.ACTIVE, owner_id=owner_id)
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        result = await uc.export(plan_id=plan.plan_id, user_id=owner_id)
        assert result.url

    @pytest.mark.asyncio
    async def test_vet_puede_exportar_su_paciente(self) -> None:
        """assigned_vet_id == user_id → permitido."""
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase

        vet_id = uuid.uuid4()
        plan = _make_plan(status=PlanStatus.ACTIVE, approved_by_vet_id=vet_id)
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        result = await uc.export(plan_id=plan.plan_id, user_id=vet_id)
        assert result.url

    @pytest.mark.asyncio
    async def test_otro_owner_no_autorizado(self) -> None:
        """Otro user_id (ni owner ni vet) → ExportForbiddenError."""
        from backend.application.use_cases.export_plan_use_case import (
            ExportForbiddenError,
            ExportPlanUseCase,
        )

        plan = _make_plan(status=PlanStatus.ACTIVE)
        otro_user = uuid.uuid4()
        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=_mock_storage(),
        )
        with pytest.raises(ExportForbiddenError):
            await uc.export(plan_id=plan.plan_id, user_id=otro_user)

    @pytest.mark.asyncio
    async def test_mismo_plan_cache_hit(self) -> None:
        """Segunda exportación usa R2 existente — pdf_generator.generate no se llama."""
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase

        plan = _make_plan(status=PlanStatus.ACTIVE)
        pdf_gen = _mock_pdf_gen()
        storage = _mock_storage(exists=True, url="https://r2.example.com/cached.pdf")

        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=pdf_gen,
            storage_client=storage,
        )
        result = await uc.export(plan_id=plan.plan_id, user_id=plan.owner_id)

        pdf_gen.generate.assert_not_called()
        assert "cached" in result.url

    @pytest.mark.asyncio
    async def test_presigned_url_expira_1h(self) -> None:
        """ExpiresIn == 3600 — TTL exacto en generate_presigned_url."""
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase

        plan = _make_plan(status=PlanStatus.ACTIVE)
        storage = _mock_storage()

        uc = ExportPlanUseCase(
            plan_repo=_mock_plan_repo(plan),
            pdf_generator=_mock_pdf_gen(),
            storage_client=storage,
        )
        await uc.export(plan_id=plan.plan_id, user_id=plan.owner_id)

        storage.generate_presigned_url.assert_called_once()
        call_kwargs = storage.generate_presigned_url.call_args
        # TTL debe ser exactamente 3600
        ttl = call_kwargs[1].get("expires_in") or (call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None)
        assert ttl == 3600
