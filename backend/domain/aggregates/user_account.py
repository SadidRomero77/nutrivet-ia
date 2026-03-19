"""
UserAccount — Aggregate del dominio de autenticación y gestión de usuarios.
Contiene reglas de negocio: tier limits, cuota de agente, validación de contraseña.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from backend.domain.exceptions.domain_errors import DomainError


class UserRole(str, Enum):
    """Roles del sistema — RBAC."""

    OWNER = "owner"
    VET = "vet"


class UserTier(str, Enum):
    """Tiers del modelo freemium."""

    FREE = "free"
    BASICO = "basico"
    PREMIUM = "premium"
    VET = "vet"


# Límites de mascotas por tier (None = ilimitado)
TIER_PET_LIMITS: dict[UserTier, Optional[int]] = {
    UserTier.FREE: 1,
    UserTier.BASICO: 1,
    UserTier.PREMIUM: 3,
    UserTier.VET: None,
}

# Límites de planes por tier (None = ilimitado)
TIER_PLAN_LIMITS: dict[UserTier, Optional[int]] = {
    UserTier.FREE: 1,
    UserTier.BASICO: None,
    UserTier.PREMIUM: None,
    UserTier.VET: None,
}

# Cuota de preguntas al agente para tier Free: 3/día × 3 días = 9 total
FREE_TIER_AGENT_MAX_QUESTIONS = 9

_PASSWORD_REGEX = re.compile(r"^(?=.*[A-Z])(?=.*\d).+$")


@dataclass
class QuotaResult:
    """Resultado de verificación de cuota del agente conversacional."""

    allowed: bool
    requires_upgrade: bool = False
    message: str = ""


@dataclass
class UserAccount:
    """
    Aggregate raíz de autenticación.

    Invariantes:
    - El email es inmutable post-creación.
    - El tier de Vet se asigna automáticamente al crear usuarios con rol VET.
    - Un owner empieza siempre en tier FREE.
    """

    id: uuid.UUID
    email: str
    password_hash: str
    role: UserRole
    tier: UserTier
    is_active: bool = True

    # -- Factory method --

    @classmethod
    def create(
        cls,
        email: str,
        password_hash: str,
        role: UserRole,
        tier: Optional[UserTier] = None,
    ) -> "UserAccount":
        """
        Crea un UserAccount nuevo con valores por defecto según rol.

        Los vets reciben tier VET automáticamente.
        Los owners empiezan en FREE si no se especifica tier.
        """
        if role == UserRole.VET:
            assigned_tier = UserTier.VET
        else:
            assigned_tier = tier if tier is not None else UserTier.FREE

        return cls(
            id=uuid.uuid4(),
            email=email.lower().strip(),
            password_hash=password_hash,
            role=role,
            tier=assigned_tier,
        )

    # -- Validación de contraseña --

    @staticmethod
    def validate_raw_password(password: str) -> None:
        """
        Valida que la contraseña en texto plano cumpla los requisitos mínimos.

        Requisitos: al menos una mayúscula y al menos un número.
        Lanza DomainError si no cumple.
        """
        if not _PASSWORD_REGEX.match(password):
            raise DomainError(
                "La contraseña debe contener al menos una mayúscula y un número."
            )

    # -- Reglas de negocio: mascotas --

    def can_add_pet(self, current_count: int) -> bool:
        """
        Determina si el usuario puede agregar una mascota adicional según su tier.

        Args:
            current_count: Número de mascotas que el usuario ya tiene registradas.

        Returns:
            True si puede agregar, False si alcanzó el límite del tier.
        """
        limit = TIER_PET_LIMITS[self.tier]
        if limit is None:
            return True
        return current_count < limit

    # -- Reglas de negocio: planes --

    def can_generate_plan(self, existing_plans_count: int) -> bool:
        """
        Determina si el usuario puede generar un nuevo plan nutricional.

        Args:
            existing_plans_count: Planes activos/históricos del usuario.

        Returns:
            True si puede generar, False si alcanzó el límite.
        """
        limit = TIER_PLAN_LIMITS[self.tier]
        if limit is None:
            return True
        return existing_plans_count < limit

    # -- Reglas de negocio: agente conversacional --

    def check_agent_quota(self, questions_used: int, days_active: int) -> QuotaResult:
        """
        Verifica si el usuario puede hacer más preguntas al agente conversacional.

        Free tier: máximo 9 preguntas totales (3/día × 3 días).
        Tiers superiores: ilimitado.

        Args:
            questions_used: Total de preguntas realizadas al agente.
            days_active: Días desde que el usuario registró su cuenta.

        Returns:
            QuotaResult con allowed y requires_upgrade.
        """
        if self.tier != UserTier.FREE:
            return QuotaResult(allowed=True, requires_upgrade=False)

        if questions_used >= FREE_TIER_AGENT_MAX_QUESTIONS:
            return QuotaResult(
                allowed=False,
                requires_upgrade=True,
                message=(
                    "Has agotado tus 9 preguntas gratuitas. "
                    "Actualiza a Básico para continuar."
                ),
            )

        return QuotaResult(allowed=True, requires_upgrade=False)
