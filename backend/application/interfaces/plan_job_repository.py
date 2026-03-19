"""
IPlanJobRepository — Puerto de salida para PlanJob (cola async ARQ).
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.value_objects.plan_job import PlanJob


class IPlanJobRepository(ABC):
    """Interfaz de repositorio para PlanJob."""

    @abstractmethod
    async def save(self, job: PlanJob) -> None:
        """Persiste un nuevo job."""

    @abstractmethod
    async def find_by_id(self, job_id: uuid.UUID) -> Optional[PlanJob]:
        """Busca un job por ID. Retorna None si no existe."""

    @abstractmethod
    async def update(self, job: PlanJob) -> None:
        """Actualiza estado/resultado del job (QUEUED → PROCESSING → READY/FAILED)."""
