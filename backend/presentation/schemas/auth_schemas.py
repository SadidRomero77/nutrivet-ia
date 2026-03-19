"""
Schemas Pydantic para los endpoints de autenticación.
Todos los campos con validación estricta — nunca raw dict en endpoints.
"""
from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator

from backend.domain.aggregates.user_account import UserRole


class RegisterRequest(BaseModel):
    """Body del endpoint POST /v1/auth/register."""

    email: EmailStr
    password: str
    role: UserRole = UserRole.OWNER

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
