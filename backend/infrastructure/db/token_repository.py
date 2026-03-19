"""
PostgreSQLTokenRepository — Implementación de ITokenRepository con SQLAlchemy async.
Los refresh tokens se almacenan como hash SHA-256 en DB, nunca el valor raw.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.token_repository import ITokenRepository
from backend.infrastructure.db.models import RefreshTokenModel


def _hash_token(token: str) -> str:
    """Hashea el refresh token con SHA-256 para almacenamiento seguro."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PostgreSQLTokenRepository(ITokenRepository):
    """
    Repositorio de refresh tokens backed por PostgreSQL vía SQLAlchemy async.

    Los tokens se almacenan hasheados — nunca en texto plano.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: Sesión async de SQLAlchemy inyectada por FastAPI.
        """
        self._session = session

    async def save_refresh_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
    ) -> None:
        """Persiste un nuevo refresh token (hasheado) para el usuario."""
        model = RefreshTokenModel(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=_hash_token(token),
            expires_at=expires_at,
        )
        self._session.add(model)

    async def find_valid_token(self, token: str) -> Optional[dict[str, Any]]:
        """
        Busca un refresh token activo (no revocado y no expirado).

        Returns:
            Dict con 'user_id' y 'token' si existe y es válido, None en otro caso.
        """
        token_hash = _hash_token(token)
        now = datetime.now(timezone.utc)

        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > now,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return {"user_id": model.user_id, "token": token}

    async def revoke_token(self, token: str) -> None:
        """Revoca un refresh token marcando revoked_at = now."""
        token_hash = _hash_token(token)
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is not None:
            model.revoked_at = datetime.now(timezone.utc)
