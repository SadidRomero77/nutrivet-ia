"""
PostgreSQLLabelScanRepository — Persistencia de escaneos de etiquetas nutricionales.

SIN columna brand_name — principio de imparcialidad (Constitution REGLA 7).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.label_scan_repository import ILabelScanRepository
from backend.infrastructure.db.models import LabelScanModel


class PostgreSQLLabelScanRepository(ILabelScanRepository):
    """Repositorio PostgreSQL para LabelScan."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self,
        *,
        scan_id: uuid.UUID,
        pet_id: uuid.UUID,
        user_id: uuid.UUID,
        image_url: str,
        image_type: str,
        semaphore: str,
        ingredients: list[str],
        issues: list[str],
        recomendacion: str,
        created_at: datetime,
    ) -> uuid.UUID:
        """Inserta un nuevo registro de escaneo. Retorna el scan_id."""
        row = LabelScanModel(
            id=scan_id,
            pet_id=pet_id,
            user_id=user_id,
            image_url=image_url,
            image_type=image_type,
            semaphore=semaphore,
            ingredients_detected=ingredients,
            issues=issues,
            recomendacion=recomendacion,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return scan_id
