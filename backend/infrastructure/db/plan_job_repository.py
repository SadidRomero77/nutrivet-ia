"""
PostgreSQLPlanJobRepository — Persistencia de PlanJob.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.plan_job_repository import IPlanJobRepository
from backend.domain.value_objects.plan_job import PlanJob, PlanJobStatus
from backend.infrastructure.db.models import PlanJobModel


def _to_domain(row: PlanJobModel) -> PlanJob:
    """Convierte ORM model → value object."""
    job = PlanJob(
        job_id=row.id,
        pet_id=row.pet_id,
        owner_id=row.owner_id,
        modality=row.modality,
        status=PlanJobStatus(row.status),
        plan_id=row.plan_id,
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
    return job


class PostgreSQLPlanJobRepository(IPlanJobRepository):
    """Repositorio PostgreSQL para PlanJob."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, job: PlanJob) -> None:
        """Persiste un nuevo job."""
        row = PlanJobModel(
            id=job.job_id,
            pet_id=job.pet_id,
            owner_id=job.owner_id,
            modality=job.modality,
            status=job.status.value,
            plan_id=job.plan_id,
            error_message=job.error_message,
        )
        self._session.add(row)
        await self._session.flush()

    async def find_by_id(self, job_id: uuid.UUID) -> Optional[PlanJob]:
        """Busca job por ID."""
        result = await self._session.execute(
            select(PlanJobModel).where(PlanJobModel.id == job_id)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def update(self, job: PlanJob) -> None:
        """Actualiza estado, plan_id y error del job."""
        result = await self._session.execute(
            select(PlanJobModel).where(PlanJobModel.id == job.job_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return
        row.status = job.status.value
        row.plan_id = job.plan_id
        row.error_message = job.error_message
        await self._session.flush()
