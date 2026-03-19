"""IClaimCodeRepository — Puerto del repositorio de claim codes."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class IClaimCodeRepository(ABC):
    """Interfaz del repositorio de códigos de reclamación de mascotas."""

    @abstractmethod
    async def save(
        self,
        pet_id: uuid.UUID,
        code: str,
        expires_at: datetime,
    ) -> None:
        """Persiste un nuevo claim code."""
        ...

    @abstractmethod
    async def find_by_code(self, code: str) -> Optional[dict[str, Any]]:
        """Busca un claim code. Retorna dict con pet_id, used, expires_at o None."""
        ...

    @abstractmethod
    async def mark_used(self, code: str) -> None:
        """Marca un claim code como usado (single-use enforcement)."""
        ...
