"""
ITokenRepository — Puerto (interfaz) del repositorio de refresh tokens.
Los refresh tokens se almacenan hasheados; la rotación los revoca.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class ITokenRepository(ABC):
    """Interfaz del repositorio de refresh tokens."""

    @abstractmethod
    async def save_refresh_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
    ) -> None:
        """Persiste un refresh token asociado al usuario."""
        ...

    @abstractmethod
    async def find_valid_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Busca un refresh token activo (no revocado y no expirado).
        Retorna dict con 'user_id' y 'token', o None si no existe/inválido.
        """
        ...

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Revoca un refresh token (marca revoked_at = now)."""
        ...
