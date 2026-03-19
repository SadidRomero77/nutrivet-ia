"""Tests RED — UserAccount domain entity (unit-02-auth-service Paso 2)."""
import pytest

from backend.domain.aggregates.user_account import (
    QuotaResult,
    UserAccount,
    UserRole,
    UserTier,
)
from backend.domain.exceptions.domain_errors import DomainError


class TestUserAccountCreation:
    """Creación de UserAccount con distintos roles y tiers."""

    def test_crear_user_account_owner(self) -> None:
        """Un owner nuevo tiene tier Free y rol owner."""
        user = UserAccount.create(
            email="valentina@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
        )
        assert user.role == UserRole.OWNER
        assert user.tier == UserTier.FREE
        assert user.email == "valentina@example.com"
        assert user.id is not None

    def test_crear_user_account_vet(self) -> None:
        """Un vet nuevo tiene tier Vet por defecto."""
        user = UserAccount.create(
            email="dr.andres@bampysvet.com",
            password_hash="hashed",
            role=UserRole.VET,
        )
        assert user.role == UserRole.VET
        assert user.tier == UserTier.VET

    def test_email_duplicado_detectado_en_dominio(self) -> None:
        """Dos UserAccount con el mismo email son detectables (email como clave)."""
        user1 = UserAccount.create(
            email="test@example.com",
            password_hash="h1",
            role=UserRole.OWNER,
        )
        user2 = UserAccount.create(
            email="test@example.com",
            password_hash="h2",
            role=UserRole.OWNER,
        )
        # En dominio: mismo email → misma identidad lógica
        assert user1.email == user2.email

    def test_password_debe_tener_mayuscula_y_numero(self) -> None:
        """La validación de contraseña requiere mayúscula y número en texto plano."""
        with pytest.raises(DomainError, match="contraseña"):
            UserAccount.validate_raw_password("sinmayuscula1")

        with pytest.raises(DomainError, match="contraseña"):
            UserAccount.validate_raw_password("SinNumero")

        # Contraseña válida no lanza excepción
        UserAccount.validate_raw_password("Valida123")

    def test_tier_initial_free(self) -> None:
        """Los owners empiezan en tier Free."""
        user = UserAccount.create(
            email="camilo@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
        )
        assert user.tier == UserTier.FREE


class TestCanAddPet:
    """Reglas de negocio para agregar mascotas según tier."""

    def test_can_add_pet_free_tier_maximo_1(self) -> None:
        """Tier Free: máximo 1 mascota."""
        user = UserAccount.create(
            email="u@e.com", password_hash="h", role=UserRole.OWNER
        )
        assert user.tier == UserTier.FREE
        assert user.can_add_pet(current_count=0) is True
        assert user.can_add_pet(current_count=1) is False

    def test_can_add_pet_basico_maximo_1(self) -> None:
        """Tier Básico: máximo 1 mascota."""
        user = UserAccount.create(
            email="u2@e.com", password_hash="h", role=UserRole.OWNER, tier=UserTier.BASICO
        )
        assert user.can_add_pet(current_count=0) is True
        assert user.can_add_pet(current_count=1) is False

    def test_can_add_pet_premium_hasta_3(self) -> None:
        """Tier Premium: hasta 3 mascotas."""
        user = UserAccount.create(
            email="u3@e.com", password_hash="h", role=UserRole.OWNER, tier=UserTier.PREMIUM
        )
        assert user.can_add_pet(current_count=0) is True
        assert user.can_add_pet(current_count=2) is True
        assert user.can_add_pet(current_count=3) is False

    def test_can_add_pet_vet_ilimitado(self) -> None:
        """Tier Vet: mascotas ilimitadas."""
        user = UserAccount.create(
            email="vet@clinic.com", password_hash="h", role=UserRole.VET
        )
        assert user.can_add_pet(current_count=999) is True


class TestCanGeneratePlan:
    """Reglas de negocio para generar planes según tier."""

    def test_can_generate_plan_free_con_plan_existente_falla(self) -> None:
        """Free tier: solo 1 plan total. Con 1 plan existente → no puede generar."""
        user = UserAccount.create(
            email="u@e.com", password_hash="h", role=UserRole.OWNER
        )
        assert user.can_generate_plan(existing_plans_count=0) is True
        assert user.can_generate_plan(existing_plans_count=1) is False

    def test_can_generate_plan_premium_ilimitado(self) -> None:
        """Premium puede generar planes ilimitados."""
        user = UserAccount.create(
            email="u@e.com", password_hash="h", role=UserRole.OWNER, tier=UserTier.PREMIUM
        )
        assert user.can_generate_plan(existing_plans_count=100) is True


class TestAgentQuota:
    """Cuota del agente conversacional por tier."""

    def test_agent_questions_free_limite_correcto(self) -> None:
        """Free: 3 preguntas/día × 3 días = 9 preguntas totales. Al agotar → upgrade."""
        user = UserAccount.create(
            email="u@e.com", password_hash="h", role=UserRole.OWNER
        )
        # Dentro del límite
        result: QuotaResult = user.check_agent_quota(questions_used=8, days_active=3)
        assert result.allowed is True

        # Al agotar
        result = user.check_agent_quota(questions_used=9, days_active=3)
        assert result.allowed is False
        assert result.requires_upgrade is True

    def test_agent_questions_basico_ilimitado(self) -> None:
        """Básico y superiores: agente ilimitado."""
        user = UserAccount.create(
            email="u@e.com", password_hash="h", role=UserRole.OWNER, tier=UserTier.BASICO
        )
        result = user.check_agent_quota(questions_used=10000, days_active=365)
        assert result.allowed is True
        assert result.requires_upgrade is False
