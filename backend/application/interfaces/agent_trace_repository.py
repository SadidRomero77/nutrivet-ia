"""
IAgentTraceRepository — Append-only. Sin update() por diseño.

Constitution REGLA 6: agent_traces son inmutables post-generación.
Solo INSERT permitido. Las correcciones se registran como nueva traza
con referencia a la original.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class IAgentTraceRepository(ABC):
    """
    Interfaz de repositorio para AgentTrace.
    NOTA: No existe método update() — inmutabilidad garantizada.
    """

    @abstractmethod
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
        """
        Inserta una nueva traza. Retorna el trace_id generado.
        NUNCA actualizar trazas existentes.
        """

    @abstractmethod
    async def find_by_plan(self, plan_id: uuid.UUID) -> list[dict[str, Any]]:
        """Lista trazas asociadas a un plan (lectura)."""
