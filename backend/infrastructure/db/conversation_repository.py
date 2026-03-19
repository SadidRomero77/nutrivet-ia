"""
PostgreSQLConversationRepository — Repositorio de historial conversacional.

Append-only — sin UPDATE. Historial inmutable post-inserción (Constitution REGLA 6).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.db.models import ConversationModel


class PostgreSQLConversationRepository:
    """Repositorio de conversaciones — append-only, sin update."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        pet_id: str,
        user_id: str,
        message: str,
        response: str,
        intent: str | None = None,
    ) -> uuid.UUID:
        """
        Guarda un intercambio de conversación.

        Args:
            pet_id: ID anónimo de la mascota.
            user_id: ID anónimo del usuario.
            message: Mensaje del usuario.
            response: Respuesta del agente.
            intent: Intent clasificado (nutritional / medical / emergency).

        Returns:
            UUID del registro creado.
        """
        record = ConversationModel(
            id=uuid.uuid4(),
            pet_id=uuid.UUID(pet_id),
            user_id=uuid.UUID(user_id),
            message=message,
            response=response,
            intent=intent,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(record)
        await self._session.flush()
        return record.id

    async def list_by_pet(
        self,
        pet_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """
        Retorna los últimos N mensajes de la conversación de una mascota.

        Args:
            pet_id: ID anónimo de la mascota.
            limit: Máximo de mensajes a retornar (default 10).

        Returns:
            Lista de dicts {role, content} para el contexto LLM.
        """
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.pet_id == uuid.UUID(pet_id))
            .order_by(ConversationModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        # Invertir para orden cronológico y convertir a formato LLM
        messages: list[dict] = []
        for row in reversed(rows):
            messages.append({"role": "user", "content": row.message})
            messages.append({"role": "assistant", "content": row.response})

        return messages
