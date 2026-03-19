"""
Tests para NutritionPlan Aggregate — NutriVet.IA
Fase TDD: RED → GREEN

Máquina de estados: PENDING_VET → ACTIVE → UNDER_REVIEW → ARCHIVED
Constitution REGLA 4: mascotas sanas → ACTIVE directo; con condición → PENDING_VET.
"""
import pytest
from datetime import date, timedelta
from uuid import uuid4


def _make_plan(has_condition: bool = False, plan_type: str = "estándar"):
    """Factory helper para crear planes de prueba."""
    from backend.domain.aggregates.nutrition_plan import (
        NutritionPlan, PlanModality, PlanStatus, PlanType,
    )
    from backend.domain.value_objects.bcs import BCSPhase
    status = PlanStatus.PENDING_VET if has_condition else PlanStatus.ACTIVE
    return NutritionPlan(
        plan_id=uuid4(), pet_id=uuid4(), owner_id=uuid4(),
        plan_type=PlanType(plan_type),
        status=status,
        modality=PlanModality.NATURAL,
        rer_kcal=396.0, der_kcal=534.0,
        weight_phase=BCSPhase.MANTENIMIENTO,
        llm_model_used="anthropic/claude-sonnet-4-5",
        content={"disclaimer": "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."},
        approved_by_vet_id=None, approval_timestamp=None,
        review_date=None, vet_comment=None,
        agent_trace_id=uuid4(),
    )


class TestNutritionPlanCreation:

    def test_plan_mascota_sana_status_active(self):
        from backend.domain.aggregates.nutrition_plan import PlanStatus
        plan = _make_plan(has_condition=False)
        assert plan.status == PlanStatus.ACTIVE

    def test_plan_con_condicion_status_pending_vet(self):
        from backend.domain.aggregates.nutrition_plan import PlanStatus
        plan = _make_plan(has_condition=True)
        assert plan.status == PlanStatus.PENDING_VET


class TestApprove:

    def test_aprobar_plan_pending_vet_cambia_a_active(self):
        from backend.domain.aggregates.nutrition_plan import PlanStatus
        plan = _make_plan(has_condition=True)
        plan.approve(vet_id=uuid4())
        assert plan.status == PlanStatus.ACTIVE

    def test_aprobar_plan_ya_active_lanza_error(self):
        from backend.domain.exceptions.domain_errors import DomainError
        plan = _make_plan(has_condition=False)
        with pytest.raises(DomainError):
            plan.approve(vet_id=uuid4())

    def test_aprobar_temporal_medical_sin_review_date_falla(self):
        from backend.domain.aggregates.nutrition_plan import (
            NutritionPlan, PlanModality, PlanStatus, PlanType,
        )
        from backend.domain.exceptions.domain_errors import DomainError
        from backend.domain.value_objects.bcs import BCSPhase
        plan = NutritionPlan(
            plan_id=uuid4(), pet_id=uuid4(), owner_id=uuid4(),
            plan_type=PlanType.TEMPORAL_MEDICAL,
            status=PlanStatus.PENDING_VET,
            modality=PlanModality.NATURAL,
            rer_kcal=396.0, der_kcal=534.0,
            weight_phase=BCSPhase.MANTENIMIENTO,
            llm_model_used="anthropic/claude-sonnet-4-5",
            content={"disclaimer": "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."},
            approved_by_vet_id=None, approval_timestamp=None,
            review_date=None, vet_comment=None, agent_trace_id=uuid4(),
        )
        with pytest.raises(DomainError):
            plan.approve(vet_id=uuid4(), review_date=None)

    def test_aprobar_temporal_medical_con_review_date(self):
        from backend.domain.aggregates.nutrition_plan import (
            NutritionPlan, PlanModality, PlanStatus, PlanType,
        )
        from backend.domain.value_objects.bcs import BCSPhase
        plan = NutritionPlan(
            plan_id=uuid4(), pet_id=uuid4(), owner_id=uuid4(),
            plan_type=PlanType.TEMPORAL_MEDICAL,
            status=PlanStatus.PENDING_VET,
            modality=PlanModality.NATURAL,
            rer_kcal=396.0, der_kcal=534.0,
            weight_phase=BCSPhase.MANTENIMIENTO,
            llm_model_used="anthropic/claude-sonnet-4-5",
            content={"disclaimer": "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."},
            approved_by_vet_id=None, approval_timestamp=None,
            review_date=None, vet_comment=None, agent_trace_id=uuid4(),
        )
        review = date.today() + timedelta(days=90)
        plan.approve(vet_id=uuid4(), review_date=review)
        assert plan.status == PlanStatus.ACTIVE
        assert plan.review_date == review

    def test_aprobar_guarda_vet_id(self):
        plan = _make_plan(has_condition=True)
        vet_id = uuid4()
        plan.approve(vet_id=vet_id)
        assert plan.approved_by_vet_id == vet_id


class TestReturnToOwner:

    def test_devolver_con_comentario_vacio_falla(self):
        from backend.domain.exceptions.domain_errors import DomainError
        plan = _make_plan(has_condition=True)
        with pytest.raises(DomainError):
            plan.return_to_owner(vet_id=uuid4(), comment="")

    def test_devolver_plan_activo_falla(self):
        from backend.domain.exceptions.domain_errors import DomainError
        plan = _make_plan(has_condition=False)
        with pytest.raises(DomainError):
            plan.return_to_owner(vet_id=uuid4(), comment="Falta info de alérgenos.")

    def test_devolver_plan_pending_vet_guarda_comentario(self):
        from backend.domain.aggregates.nutrition_plan import PlanStatus
        plan = _make_plan(has_condition=True)
        plan.return_to_owner(vet_id=uuid4(), comment="Revisar fósforo — paciente renal.")
        assert plan.status == PlanStatus.PENDING_VET
        assert "fósforo" in plan.vet_comment


class TestArchive:

    def test_archivar_plan_activo(self):
        from backend.domain.aggregates.nutrition_plan import PlanStatus
        plan = _make_plan(has_condition=False)
        plan.archive(replaced_by=uuid4())
        assert plan.status == PlanStatus.ARCHIVED

    def test_plan_archivado_no_modificable(self):
        from backend.domain.exceptions.domain_errors import DomainError
        plan = _make_plan(has_condition=False)
        plan.archive(replaced_by=uuid4())
        with pytest.raises(DomainError):
            plan.archive(replaced_by=uuid4())

    def test_archivar_plan_pending_vet_falla(self):
        from backend.domain.exceptions.domain_errors import DomainError
        plan = _make_plan(has_condition=True)
        with pytest.raises(DomainError):
            plan.archive(replaced_by=uuid4())


class TestExport:

    def test_can_export_solo_si_active(self):
        assert _make_plan(has_condition=False).can_export() is True
        assert _make_plan(has_condition=True).can_export() is False

    def test_plan_archivado_no_exportable(self):
        plan = _make_plan(has_condition=False)
        plan.archive(replaced_by=uuid4())
        assert plan.can_export() is False


class TestAgregarCondicion:

    def test_agregar_condicion_a_plan_activo_vuelve_pending_vet(self):
        """Constitution REGLA 4: plan ACTIVE con condición nueva → PENDING_VET."""
        from backend.domain.aggregates.nutrition_plan import PlanStatus
        plan = _make_plan(has_condition=False)
        assert plan.status == PlanStatus.ACTIVE
        plan.add_medical_condition_requires_review()
        assert plan.status == PlanStatus.PENDING_VET
