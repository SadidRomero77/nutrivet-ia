"""
PostgreSQLAgentTraceRepository — Append-only. Sin UPDATE (Constitution REGLA 6).

Solo INSERT. Las correcciones se registran como nueva traza con referencia a la original.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.agent_trace_repository import IAgentTraceRepository
from backend.infrastructure.db.models import AgentTraceModel


class PostgreSQLAgentTraceRepository(IAgentTraceRepository):
    """Repositorio append-only para AgentTrace. Sin método update()."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        *,
        pet_id: uuid.UUID,
        plan_id: uuid.UUID | None,
        llm_model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        input_summary: dict[str, Any],
        output_summary: dict[str, Any],
        created_at: datetime,
    ) -> uuid.UUID:
        """Inserta una nueva traza. Retorna el trace_id."""
        trace_id = uuid.uuid4()
        row = AgentTraceModel(
            id=trace_id,
            pet_id=pet_id,
            plan_id=plan_id,
            llm_model=llm_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            input_summary=input_summary,
            output_summary=output_summary,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return trace_id

    async def find_by_plan(self, plan_id: uuid.UUID) -> list[dict[str, Any]]:
        """Lista trazas asociadas a un plan (solo lectura)."""
        result = await self._session.execute(
            select(AgentTraceModel).where(
                AgentTraceModel.plan_id == plan_id
            ).order_by(AgentTraceModel.created_at.asc())
        )
        return [
            {
                "trace_id": row.id,
                "llm_model": row.llm_model,
                "prompt_tokens": row.prompt_tokens,
                "completion_tokens": row.completion_tokens,
                "latency_ms": row.latency_ms,
                "input_summary": row.input_summary,
                "output_summary": row.output_summary,
                "created_at": row.created_at,
            }
            for row in result.scalars().all()
        ]
