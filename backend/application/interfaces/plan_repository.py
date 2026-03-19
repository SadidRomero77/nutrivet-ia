"""
IPlanRepository — Puerto de salida para persistencia de NutritionPlan.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.aggregates.nutrition_plan import NutritionPlan


class IPlanRepository(ABC):
    """Interfaz de repositorio para NutritionPlan."""

    @abstractmethod
    async def save(self, plan: NutritionPlan) -> None:
        """Persiste un nuevo plan nutricional."""

    @abstractmethod
    async def update(self, plan: NutritionPlan) -> None:
        """Actualiza un plan existente (estado, aprobación, comentario)."""

    @abstractmethod
    async def find_by_id(self, plan_id: uuid.UUID) -> Optional[NutritionPlan]:
        """Busca un plan por su ID. Retorna None si no existe."""

    @abstractmethod
    async def find_active_by_pet(self, pet_id: uuid.UUID) -> Optional[NutritionPlan]:
        """Retorna el plan ACTIVE o PENDING_VET actual de la mascota, si existe."""

    @abstractmethod
    async def list_by_owner(self, owner_id: uuid.UUID) -> list[NutritionPlan]:
        """Lista todos los planes (activos y archivados) del owner."""

    @abstractmethod
    async def list_pending_vet(self) -> list[NutritionPlan]:
        """Lista todos los planes en estado PENDING_VET (dashboard del vet)."""

    @abstractmethod
    async def count_active_by_owner(self, owner_id: uuid.UUID) -> int:
        """Cuenta los planes ACTIVE o PENDING_VET del owner (para límite de tier)."""
