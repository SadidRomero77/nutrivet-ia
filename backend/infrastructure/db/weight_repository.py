"""PostgreSQLWeightRepository — Repositorio append-only de registros de peso."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.weight_repository import IWeightRepository
from backend.domain.value_objects.bcs import BCS
from backend.infrastructure.db.models import WeightRecordModel


class PostgreSQLWeightRepository(IWeightRepository):
    """Repositorio append-only de historial de peso. Sin método update()."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(
        self,
        pet_id: uuid.UUID,
        weight_kg: float,
        bcs: BCS | None,
        recorded_by: uuid.UUID,
        recorded_at: datetime,
    ) -> uuid.UUID:
        """Agrega un registro de peso y retorna su ID."""
        record = WeightRecordModel(
            id=uuid.uuid4(),
            pet_id=pet_id,
            weight_kg=weight_kg,
            bcs=bcs.value if bcs else None,
            recorded_by=recorded_by,
            recorded_at=recorded_at,
        )
        self._session.add(record)
        return record.id

    async def list_by_pet(
        self, pet_id: uuid.UUID, limit: int = 30, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Lista historial de peso paginado, orden descendente por fecha."""
        stmt = (
            select(WeightRecordModel)
            .where(WeightRecordModel.pet_id == pet_id)
            .order_by(WeightRecordModel.recorded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "id": r.id,
                "pet_id": r.pet_id,
                "weight_kg": r.weight_kg,
                "bcs": r.bcs,
                "recorded_by": r.recorded_by,
                "recorded_at": r.recorded_at,
            }
            for r in result.scalars().all()
        ]
