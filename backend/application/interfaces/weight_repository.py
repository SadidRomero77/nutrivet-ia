"""IWeightRepository — Puerto del repositorio de registros de peso.
Append-only: sin método update() por diseño.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from backend.domain.value_objects.bcs import BCS


class IWeightRepository(ABC):
    """
    Interfaz append-only del repositorio de registros de peso.
    No existe método update() — los registros son inmutables por diseño.
    """

    @abstractmethod
    async def append(
        self,
        pet_id: uuid.UUID,
        weight_kg: float,
        bcs: BCS | None,
        recorded_by: uuid.UUID,
        recorded_at: datetime,
    ) -> uuid.UUID:
        """Agrega un nuevo registro de peso. Retorna el ID del registro."""
        ...

    @abstractmethod
    async def list_by_pet(
        self, pet_id: uuid.UUID, limit: int = 30, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Lista el historial de peso de una mascota, paginado."""
        ...
