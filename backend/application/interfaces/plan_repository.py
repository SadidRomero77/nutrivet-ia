"""
IPlanRepository — Puerto de salida para persistencia de NutritionPlan.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
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
    async def list_by_owner(
        self,
        owner_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[NutritionPlan]:
        """Lista planes del owner, más reciente primero. Soporta paginación."""

    @abstractmethod
    async def list_pending_vet(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NutritionPlan]:
        """Lista planes en estado PENDING_VET ordenados por antigüedad. Soporta paginación."""

    @abstractmethod
    async def list_pending_vet_with_conditions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[NutritionPlan, int, datetime]]:
        """
        Lista planes PENDING_VET con conteo de condiciones médicas y fecha de creación.

        Retorna tuplas (plan, conditions_count, created_at) para el dashboard del vet.
        Requiere JOIN con PetModel y desencriptación de medical_conditions_enc.
        Orden: más antiguo primero (prioridad de atención).
        """

    @abstractmethod
    async def count_active_by_owner(self, owner_id: uuid.UUID) -> int:
        """Cuenta los planes ACTIVE o PENDING_VET del owner (para límite de tier)."""

    @abstractmethod
    async def list_recent_by_pet(
        self, pet_id: uuid.UUID, limit: int = 3
    ) -> list[NutritionPlan]:
        """
        Lista los planes más recientes de una mascota (activos y archivados).

        Usado por el agente para dar contexto histórico de planes anteriores.
        Orden: más reciente primero.
        """
