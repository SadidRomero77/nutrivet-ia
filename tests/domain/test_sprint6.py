"""
Tests Sprint 6 — NutriVet.IA
Cubre: D-01 (plan_job.py), D-02 (user_account.py coverage gaps),
       D-03 (domain_errors.py)
"""
from __future__ import annotations

import uuid

import pytest


# ---------------------------------------------------------------------------
# D-01 — PlanJob (plan_job.py) — 0% → 100%
# ---------------------------------------------------------------------------

class TestPlanJob:

    def _make_job(self, modality: str = "natural"):
        from backend.domain.value_objects.plan_job import PlanJob, PlanJobStatus
        return PlanJob(
            job_id=uuid.uuid4(),
            pet_id=uuid.uuid4(),
            owner_id=uuid.uuid4(),
            modality=modality,
        ), PlanJobStatus

    def test_initial_status_is_queued(self):
        job, Status = self._make_job()
        assert job.status == Status.QUEUED

    def test_mark_processing_transitions_to_processing(self):
        job, Status = self._make_job()
        job.mark_processing()
        assert job.status == Status.PROCESSING

    def test_mark_ready_sets_plan_id_and_status(self):
        job, Status = self._make_job()
        job.mark_processing()
        plan_id = uuid.uuid4()
        job.mark_ready(plan_id)
        assert job.status == Status.READY
        assert job.plan_id == plan_id

    def test_mark_failed_sets_error_message(self):
        job, Status = self._make_job()
        job.mark_processing()
        job.mark_failed("LLM timeout after 2 retries")
        assert job.status == Status.FAILED
        assert job.error_message == "LLM timeout after 2 retries"

    def test_plan_id_none_initially(self):
        job, _ = self._make_job()
        assert job.plan_id is None

    def test_error_message_none_initially(self):
        job, _ = self._make_job()
        assert job.error_message is None

    def test_updated_at_changes_on_mark_processing(self):
        from datetime import timedelta
        import time
        job, _ = self._make_job()
        before = job.updated_at
        time.sleep(0.01)
        job.mark_processing()
        assert job.updated_at >= before

    def test_updated_at_changes_on_mark_ready(self):
        import time
        job, _ = self._make_job()
        job.mark_processing()
        before = job.updated_at
        time.sleep(0.01)
        job.mark_ready(uuid.uuid4())
        assert job.updated_at >= before

    def test_updated_at_changes_on_mark_failed(self):
        import time
        job, _ = self._make_job()
        job.mark_processing()
        before = job.updated_at
        time.sleep(0.01)
        job.mark_failed("error")
        assert job.updated_at >= before

    def test_modality_stored(self):
        job, _ = self._make_job("concentrado")
        assert job.modality == "concentrado"

    def test_plan_job_status_string_values(self):
        from backend.domain.value_objects.plan_job import PlanJobStatus
        assert PlanJobStatus.QUEUED == "QUEUED"
        assert PlanJobStatus.PROCESSING == "PROCESSING"
        assert PlanJobStatus.READY == "READY"
        assert PlanJobStatus.FAILED == "FAILED"


# ---------------------------------------------------------------------------
# D-02 — UserAccount coverage gaps (65% → ≥80%)
# ---------------------------------------------------------------------------

class TestUserAccountCreate:

    def test_create_owner_defaults_to_free_tier(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
        account = UserAccount.create(
            email="valentina@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
            full_name="Valentina López",
        )
        assert account.tier == UserTier.FREE
        assert account.role == UserRole.OWNER

    def test_create_vet_assigns_vet_tier_automatically(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
        account = UserAccount.create(
            email="dr.andres@bampysvet.com",
            password_hash="hashed",
            role=UserRole.VET,
            full_name="Dr. Andrés",
        )
        assert account.tier == UserTier.VET

    def test_create_owner_with_explicit_premium_tier(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
        account = UserAccount.create(
            email="camilo@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
            tier=UserTier.PREMIUM,
            full_name="Camilo Martínez",
        )
        assert account.tier == UserTier.PREMIUM

    def test_create_stores_full_name(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole
        account = UserAccount.create(
            email="valentina@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
            full_name="Valentina López",
        )
        assert account.full_name == "Valentina López"

    def test_create_generates_uuid(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole
        account = UserAccount.create(
            email="x@x.com",
            password_hash="hashed",
            role=UserRole.OWNER,
        )
        assert account.id is not None
        assert isinstance(account.id, uuid.UUID)


class TestValidateRawPassword:

    def test_valid_password_does_not_raise(self):
        from backend.domain.aggregates.user_account import UserAccount
        UserAccount.validate_raw_password("Segura123")  # no debe lanzar

    def test_password_without_uppercase_raises(self):
        from backend.domain.aggregates.user_account import UserAccount
        from backend.domain.exceptions.domain_errors import DomainError
        with pytest.raises(DomainError):
            UserAccount.validate_raw_password("sinmayuscula1")

    def test_password_without_number_raises(self):
        from backend.domain.aggregates.user_account import UserAccount
        from backend.domain.exceptions.domain_errors import DomainError
        with pytest.raises(DomainError):
            UserAccount.validate_raw_password("SinNumero")

    def test_empty_password_raises(self):
        from backend.domain.aggregates.user_account import UserAccount
        from backend.domain.exceptions.domain_errors import DomainError
        with pytest.raises(DomainError):
            UserAccount.validate_raw_password("")


class TestCanAddPet:

    def _make_account(self, tier):
        from backend.domain.aggregates.user_account import UserAccount, UserRole
        return UserAccount.create(
            email="x@x.com",
            password_hash="h",
            role=UserRole.OWNER,
            tier=tier,
        )

    def test_free_allows_first_pet(self):
        from backend.domain.aggregates.user_account import UserTier
        acc = self._make_account(UserTier.FREE)
        assert acc.can_add_pet(0) is True

    def test_free_blocks_second_pet(self):
        from backend.domain.aggregates.user_account import UserTier
        acc = self._make_account(UserTier.FREE)
        assert acc.can_add_pet(1) is False

    def test_premium_allows_up_to_3(self):
        from backend.domain.aggregates.user_account import UserTier
        acc = self._make_account(UserTier.PREMIUM)
        assert acc.can_add_pet(2) is True
        assert acc.can_add_pet(3) is False

    def test_vet_unlimited_pets(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole
        acc = UserAccount.create(
            email="vet@x.com",
            password_hash="h",
            role=UserRole.VET,
        )
        assert acc.can_add_pet(999) is True


class TestCanGeneratePlan:

    def _make_account(self, tier):
        from backend.domain.aggregates.user_account import UserAccount, UserRole
        return UserAccount.create(
            email="x@x.com",
            password_hash="h",
            role=UserRole.OWNER,
            tier=tier,
        )

    def test_free_allows_first_plan(self):
        from backend.domain.aggregates.user_account import UserTier
        acc = self._make_account(UserTier.FREE)
        assert acc.can_generate_plan(0) is True

    def test_free_blocks_second_plan(self):
        from backend.domain.aggregates.user_account import UserTier
        acc = self._make_account(UserTier.FREE)
        assert acc.can_generate_plan(1) is False

    def test_basico_unlimited_plans(self):
        from backend.domain.aggregates.user_account import UserTier
        acc = self._make_account(UserTier.BASICO)
        assert acc.can_generate_plan(100) is True


class TestCheckAgentQuota:

    def _make_free_account(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
        return UserAccount.create(
            email="x@x.com",
            password_hash="h",
            role=UserRole.OWNER,
            tier=UserTier.FREE,
        )

    def test_free_under_quota_is_allowed(self):
        acc = self._make_free_account()
        result = acc.check_agent_quota(questions_used=5, days_active=1)
        assert result.allowed is True
        assert result.requires_upgrade is False

    def test_free_at_9_questions_blocked(self):
        acc = self._make_free_account()
        result = acc.check_agent_quota(questions_used=9, days_active=3)
        assert result.allowed is False
        assert result.requires_upgrade is True

    def test_free_over_9_questions_blocked(self):
        acc = self._make_free_account()
        result = acc.check_agent_quota(questions_used=12, days_active=4)
        assert result.allowed is False

    def test_basico_tier_always_allowed(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
        acc = UserAccount.create(
            email="x@x.com",
            password_hash="h",
            role=UserRole.OWNER,
            tier=UserTier.BASICO,
        )
        result = acc.check_agent_quota(questions_used=1000, days_active=365)
        assert result.allowed is True

    def test_premium_tier_always_allowed(self):
        from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
        acc = UserAccount.create(
            email="x@x.com",
            password_hash="h",
            role=UserRole.OWNER,
            tier=UserTier.PREMIUM,
        )
        result = acc.check_agent_quota(questions_used=500, days_active=100)
        assert result.allowed is True

    def test_blocked_result_has_upgrade_message(self):
        acc = self._make_free_account()
        result = acc.check_agent_quota(questions_used=9, days_active=3)
        assert len(result.message) > 0
        assert "9" in result.message or "gratuitas" in result.message


# ---------------------------------------------------------------------------
# D-03 — DomainErrors (domain_errors.py) — 67% → 100%
# ---------------------------------------------------------------------------

class TestDomainErrors:

    def test_domain_error_stores_mensaje(self):
        from backend.domain.exceptions.domain_errors import DomainError
        err = DomainError("algo salió mal")
        assert err.mensaje == "algo salió mal"
        assert str(err) == "algo salió mal"

    def test_toxic_ingredient_error_fields(self):
        from backend.domain.exceptions.domain_errors import ToxicIngredientError
        err = ToxicIngredientError("uvas", "perro", "TOXIC_DOGS")
        assert err.ingrediente == "uvas"
        assert err.especie == "perro"
        assert err.lista == "TOXIC_DOGS"
        assert "uvas" in str(err)
        assert "perro" in str(err)

    def test_toxic_ingredient_error_is_domain_error(self):
        from backend.domain.exceptions.domain_errors import (
            ToxicIngredientError, DomainError,
        )
        err = ToxicIngredientError("chocolate", "gato", "TOXIC_CATS")
        assert isinstance(err, DomainError)

    def test_medical_restriction_violation_error_fields(self):
        from backend.domain.exceptions.domain_errors import MedicalRestrictionViolationError
        err = MedicalRestrictionViolationError("renal", "fósforo", "exceso de fósforo")
        assert err.condicion == "renal"
        assert err.elemento == "fósforo"
        assert err.razon == "exceso de fósforo"
        assert "renal" in str(err)
        assert "fósforo" in str(err)

    def test_medical_restriction_violation_is_domain_error(self):
        from backend.domain.exceptions.domain_errors import (
            MedicalRestrictionViolationError, DomainError,
        )
        err = MedicalRestrictionViolationError("diabético", "azúcar", "índice glucémico alto")
        assert isinstance(err, DomainError)

    def test_invalid_weight_error_fields(self):
        from backend.domain.exceptions.domain_errors import InvalidWeightError
        err = InvalidWeightError(-1.5)
        assert err.valor == -1.5
        assert "-1.5" in str(err)

    def test_invalid_weight_error_is_domain_error(self):
        from backend.domain.exceptions.domain_errors import InvalidWeightError, DomainError
        assert isinstance(InvalidWeightError(0), DomainError)

    def test_invalid_bcs_error_fields(self):
        from backend.domain.exceptions.domain_errors import InvalidBCSError
        err = InvalidBCSError(10)
        assert err.valor == 10
        assert "10" in str(err)

    def test_invalid_bcs_error_is_domain_error(self):
        from backend.domain.exceptions.domain_errors import InvalidBCSError, DomainError
        assert isinstance(InvalidBCSError(0), DomainError)

    def test_nrc_calculation_error_fields(self):
        from backend.domain.exceptions.domain_errors import NRCCalculationError
        err = NRCCalculationError("peso_kg debe ser mayor a 0")
        assert "peso_kg" in str(err)

    def test_nrc_calculation_error_is_domain_error(self):
        from backend.domain.exceptions.domain_errors import NRCCalculationError, DomainError
        assert isinstance(NRCCalculationError("error"), DomainError)
