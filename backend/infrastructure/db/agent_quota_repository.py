"""
PostgreSQLAgentQuotaRepository — Repositorio de cuota del agente conversacional.

Cuota Free tier: 3 preguntas/día × 3 días = 9 total.
El reset diario ocurre automáticamente cuando cambia la fecha.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.db.models import AgentQuotaModel


class PostgreSQLAgentQuotaRepository:
    """Repositorio de cuota de uso del agente conversacional."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, user_id: str) -> AgentQuotaModel:
        """
        Obtiene o crea el registro de cuota del usuario.

        Si la fecha actual difiere de last_reset_date, reinicia daily_count.

        Args:
            user_id: ID anónimo del usuario.

        Returns:
            Instancia de AgentQuotaModel con daily_count y total_count actuales.
        """
        stmt = select(AgentQuotaModel).where(
            AgentQuotaModel.user_id == uuid.UUID(user_id)
        )
        result = await self._session.execute(stmt)
        quota = result.scalar_one_or_none()

        today = date.today().isoformat()

        if quota is None:
            quota = AgentQuotaModel(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                daily_count=0,
                total_count=0,
                last_reset_date=today,
            )
            self._session.add(quota)
            await self._session.flush()
        elif quota.last_reset_date != today:
            # Reset diario automático
            quota.daily_count = 0
            quota.last_reset_date = today
            await self._session.flush()

        return quota

    async def increment(self, user_id: str) -> None:
        """
        Incrementa daily_count y total_count atómicamente.

        Debe llamarse ANTES de invocar el LLM (Constitution).

        Args:
            user_id: ID anónimo del usuario.
        """
        stmt = select(AgentQuotaModel).where(
            AgentQuotaModel.user_id == uuid.UUID(user_id)
        )
        result = await self._session.execute(stmt)
        quota = result.scalar_one_or_none()

        if quota is not None:
            quota.daily_count += 1
            quota.total_count += 1
            quota.updated_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def reset_daily(self, user_id: str) -> None:
        """
        Reinicia el contador diario del usuario.

        Args:
            user_id: ID anónimo del usuario.
        """
        stmt = select(AgentQuotaModel).where(
            AgentQuotaModel.user_id == uuid.UUID(user_id)
        )
        result = await self._session.execute(stmt)
        quota = result.scalar_one_or_none()

        if quota is not None:
            quota.daily_count = 0
            quota.last_reset_date = date.today().isoformat()
            await self._session.flush()
