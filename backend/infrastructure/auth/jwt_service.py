"""
JWTService — Generación y verificación de tokens JWT.
Access tokens: HS256, expiración 15 minutos.
Refresh tokens: UUID v4, rotativos, almacenados en DB.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional

from jose import ExpiredSignatureError, JWTError, jwt

from backend.domain.aggregates.user_account import UserRole, UserTier
from backend.domain.exceptions.domain_errors import DomainError

_DEFAULT_EXPIRES_SECONDS = 900  # 15 minutos


@dataclass
class TokenPayload:
    """Payload decodificado de un access token."""

    user_id: uuid.UUID
    role: UserRole
    tier: UserTier
    exp: float


class JWTService:
    """
    Servicio de autenticación JWT.

    Responsabilidades:
    - Crear access tokens firmados con HS256.
    - Verificar y decodificar access tokens.
    - Generar refresh tokens UUID v4 rotativos.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256") -> None:
        """
        Inicializa el servicio con la clave secreta y algoritmo.

        Args:
            secret_key: Clave secreta para firmar tokens. Nunca hardcoded.
            algorithm: Algoritmo de firma (default HS256).
        """
        self._secret_key = secret_key
        self._algorithm = algorithm

    def create_access_token(
        self,
        user_id: uuid.UUID,
        role: UserRole,
        tier: UserTier,
        expires_seconds: Optional[int] = None,
    ) -> str:
        """
        Genera un access token JWT firmado.

        Args:
            user_id: ID del usuario (UUID anónimo — no PII en el payload).
            role: Rol del usuario (owner/vet).
            tier: Tier de suscripción.
            expires_seconds: Tiempo de vida en segundos (default 900 = 15min).

        Returns:
            Token JWT como string.
        """
        if expires_seconds is None:
            expires_seconds = _DEFAULT_EXPIRES_SECONDS

        exp = time.time() + expires_seconds
        payload = {
            "sub": str(user_id),
            "role": role.value,
            "tier": tier.value,
            "exp": exp,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_access_token(self, token: str) -> TokenPayload:
        """
        Decodifica y verifica un access token JWT.

        Args:
            token: Token JWT como string.

        Returns:
            TokenPayload con datos del usuario.

        Raises:
            DomainError: Si el token es inválido o ha expirado.
        """
        try:
            data = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except ExpiredSignatureError:
            raise DomainError("El token JWT ha expirado. Solicita uno nuevo.")
        except JWTError:
            raise DomainError("El token JWT es inválido o fue manipulado.")

        return TokenPayload(
            user_id=uuid.UUID(data["sub"]),
            role=UserRole(data["role"]),
            tier=UserTier(data["tier"]),
            exp=data["exp"],
        )

    def create_refresh_token(self) -> str:
        """
        Genera un refresh token UUID v4.

        Returns:
            UUID v4 como string. Debe almacenarse hasheado en DB.
        """
        return str(uuid.uuid4())

    def create_reset_token(
        self,
        user_id: uuid.UUID,
        expires_seconds: int = 900,
    ) -> str:
        """
        Genera un token JWT de un solo uso para reset de contraseña.

        Args:
            user_id: ID del usuario que solicita el reset.
            expires_seconds: TTL del token (default 15 minutos).

        Returns:
            Token JWT firmado con HS256.
        """
        exp = time.time() + expires_seconds
        payload = {
            "sub": str(user_id),
            "purpose": "password_reset",
            "exp": exp,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_reset_token(self, token: str) -> uuid.UUID:
        """
        Decodifica y valida un token de reset de contraseña.

        Args:
            token: Token JWT de reset.

        Returns:
            UUID del usuario si el token es válido.

        Raises:
            DomainError: Si el token es inválido, expirado o no es de reset.
        """
        try:
            data = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except ExpiredSignatureError:
            raise DomainError("El enlace de recuperación expiró. Solicita uno nuevo.")
        except JWTError:
            raise DomainError("El enlace de recuperación es inválido.")

        if data.get("purpose") != "password_reset":
            raise DomainError("El token no es válido para este propósito.")

        return uuid.UUID(data["sub"])
