"""
Schemas Pydantic para los endpoints de autenticación.
Todos los campos con validación estricta — nunca raw dict en endpoints.
"""
from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from backend.domain.aggregates.user_account import UserRole


class RegisterRequest(BaseModel):
    """
    Body del endpoint POST /v1/auth/register.

    Soporta registro de owner y vet. Los admins se crean exclusivamente via DB/admin panel.
    Los vets se auto-aprueban en MVP (vet_status='approved' directo) — no requieren aprobación manual.

    Roles válidos: 'owner' (propietario de mascota) | 'vet' (veterinario).
    Cualquier valor distinto se rechaza con 422.
    """

    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "owner"  # 'owner' | 'vet' — default owner

    @field_validator("role")
    @classmethod
    def role_must_be_user_role(cls, v: Optional[str]) -> Optional[str]:
        """Solo owner y vet pueden registrarse. Los admins se crean via panel admin."""
        if v is None:
            return "owner"
        normalized = v.lower().strip()
        if normalized not in ("owner", "vet"):
            raise ValueError(
                "Rol inválido. Usa 'owner' (propietario) o 'vet' (veterinario). "
                "Los administradores se crean exclusivamente desde el panel de administración."
            )
        return normalized

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Valida que la contraseña cumpla los requisitos mínimos de seguridad.
        Mínimo 8 caracteres, al menos una mayúscula y al menos un número.
        """
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
        if not any(c.isdigit() for c in v):
            raise ValueError("La contraseña debe contener al menos un número.")
        return v


class LoginRequest(BaseModel):
    """Body del endpoint POST /v1/auth/login."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Body del endpoint POST /v1/auth/refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Body del endpoint POST /v1/auth/logout."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Respuesta estándar de autenticación con tokens JWT."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UpdateProfileRequest(BaseModel):
    """Body del endpoint PATCH /v1/auth/me — actualización parcial de perfil."""

    full_name: Optional[str] = None
    phone: Optional[str] = None
    clinic_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Body del endpoint PATCH /v1/auth/me/password."""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        """La nueva contraseña debe tener al menos 8 caracteres, una mayúscula y un número."""
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


class UserProfileResponse(BaseModel):
    """Respuesta del perfil del usuario autenticado."""

    user_id: uuid.UUID
    email: str
    role: str
    tier: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    clinic_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    vet_status: Optional[str] = None  # pending | approved — solo para rol vet


class UserStatsResponse(BaseModel):
    """Estadísticas de actividad del usuario autenticado."""

    # Owner
    pets_count: int = 0
    active_plans_count: int = 0
    # Vet
    patients_count: int = 0
    pending_plans_count: int = 0


class AdminCreateVetRequest(BaseModel):
    """Body para crear una cuenta de veterinario desde el panel admin."""

    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    clinic_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


class AdminUserResponse(BaseModel):
    """Respuesta completa de usuario para el panel admin."""

    user_id: uuid.UUID
    email: str
    role: str
    tier: str
    is_active: bool
    full_name: Optional[str] = None
    phone: Optional[str] = None
    clinic_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    vet_status: Optional[str] = None
    created_at: Optional[str] = None


class AdminChangeTierRequest(BaseModel):
    """Body para cambiar el tier de un usuario."""

    tier: str  # free | basico | premium | vet


class AdminRejectVetRequest(BaseModel):
    """Body para rechazar un vet con comentario."""

    comment: str = ""


class AdminOverviewStats(BaseModel):
    """Estadísticas globales para el dashboard admin."""

    total_users: int = 0
    owners_count: int = 0
    vets_count: int = 0
    vets_pending: int = 0
    active_subscriptions: int = 0
    total_payments: int = 0
    total_revenue_cop: float = 0.0


class ForgotPasswordRequest(BaseModel):
    """Body del endpoint POST /v1/auth/forgot-password."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Body del endpoint POST /v1/auth/reset-password."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        """Mínimo 8 caracteres."""
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return v


class TierUsageResponse(BaseModel):
    """Cuota de uso del tier actual del usuario."""

    tier: str
    plans_total: int = 0
    plans_limit: Optional[int] = None    # None = ilimitado
    plans_remaining: Optional[int] = None
    can_generate_plan: bool = True


class PaymentHistoryItem(BaseModel):
    """Un registro de pago en el historial."""

    payment_id: uuid.UUID
    tier: str
    amount_cop: float
    status: str
    created_at: Optional[str] = None
