"""IPetRepository — Puerto del repositorio de mascotas."""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.aggregates.pet_profile import PetProfile


class IPetRepository(ABC):
    """Interfaz del repositorio de perfiles de mascotas."""

    @abstractmethod
    async def save(self, pet: PetProfile) -> None:
        """Persiste un PetProfile nuevo."""
        ...

    @abstractmethod
    async def update(self, pet: PetProfile) -> None:
        """Actualiza un PetProfile existente."""
        ...

    @abstractmethod
    async def find_by_id(self, pet_id: uuid.UUID) -> Optional[PetProfile]:
        """Busca una mascota por ID. Retorna None si no existe."""
        ...

    @abstractmethod
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[PetProfile]:
        """Lista todas las mascotas de un owner."""
        ...

    @abstractmethod
    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        """Cuenta las mascotas activas de un owner (para validar límites de tier)."""
        ...
