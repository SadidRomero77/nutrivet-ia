"""PostgreSQLClaimCodeRepository — Repositorio de claim codes con single-use enforcement."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.claim_code_repository import IClaimCodeRepository
from backend.infrastructure.db.models import ClaimCodeModel


class PostgreSQLClaimCodeRepository(IClaimCodeRepository):
    """Repositorio de claim codes. El método mark_used usa SELECT FOR UPDATE."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self, pet_id: uuid.UUID, code: str, expires_at: datetime
    ) -> None:
        """Persiste un nuevo claim code."""
        model = ClaimCodeModel(
            id=uuid.uuid4(),
            pet_id=pet_id,
            code=code,
            used=False,
            expires_at=expires_at,
        )
        self._session.add(model)

    async def find_by_code(self, code: str) -> Optional[dict[str, Any]]:
        """Busca un claim code. Retorna dict o None."""
        stmt = select(ClaimCodeModel).where(ClaimCodeModel.code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return {
            "pet_id": model.pet_id,
            "code": model.code,
            "used": model.used,
            "expires_at": model.expires_at,
        }

    async def mark_used(self, code: str) -> None:
        """Marca el claim code como usado con timestamp."""
        stmt = select(ClaimCodeModel).where(ClaimCodeModel.code == code).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            model.used = True
            model.used_at = datetime.now(timezone.utc)
