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
    """Body del endpoint POST /v1/auth/register."""

    email: EmailStr
    password: str
    role: UserRole = UserRole.OWNER
    full_name: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        """La contraseña debe tener al menos 8 caracteres."""
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
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


class UserStatsResponse(BaseModel):
    """Estadísticas de actividad del usuario autenticado."""

    # Owner
    pets_count: int = 0
    active_plans_count: int = 0
    # Vet
    patients_count: int = 0
    pending_plans_count: int = 0
