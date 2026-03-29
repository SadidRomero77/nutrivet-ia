"""
PostgreSQLPlanRepository — Persistencia de NutritionPlan y SubstituteSet.
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.aggregates.nutrition_plan import (
    NutritionPlan, PlanModality, PlanStatus, PlanType,
)
from backend.domain.value_objects.bcs import BCSPhase
from backend.infrastructure.db.models import NutritionPlanModel


def _to_domain(row: NutritionPlanModel) -> NutritionPlan:
    """Convierte ORM model → domain aggregate."""
    return NutritionPlan(
        plan_id=row.id,
        pet_id=row.pet_id,
        owner_id=row.owner_id,
        plan_type=PlanType(row.plan_type),
        status=PlanStatus(row.status),
        modality=PlanModality(row.modality),
        rer_kcal=row.rer_kcal,
        der_kcal=row.der_kcal,
        weight_phase=BCSPhase(row.weight_phase),
        llm_model_used=row.llm_model_used,
        content=row.content or {},
        approved_by_vet_id=row.approved_by_vet_id,
        approval_timestamp=row.approval_timestamp,
        review_date=row.review_date.date() if row.review_date else None,
        vet_comment=row.vet_comment,
        agent_trace_id=row.agent_trace_id,
    )


class PostgreSQLPlanRepository(IPlanRepository):
    """Repositorio PostgreSQL para NutritionPlan."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, plan: NutritionPlan) -> None:
        """Persiste un nuevo plan."""
        row = NutritionPlanModel(
            id=plan.plan_id,
            pet_id=plan.pet_id,
            owner_id=plan.owner_id,
            plan_type=plan.plan_type.value,
            status=plan.status.value,
            modality=plan.modality.value,
            rer_kcal=plan.rer_kcal,
            der_kcal=plan.der_kcal,
            weight_phase=plan.weight_phase.value,
            llm_model_used=plan.llm_model_used,
            content=plan.content,
            approved_by_vet_id=plan.approved_by_vet_id,
            approval_timestamp=plan.approval_timestamp,
            review_date=plan.review_date,
            vet_comment=plan.vet_comment,
            agent_trace_id=plan.agent_trace_id,
        )
        self._session.add(row)
        await self._session.flush()

    async def update(self, plan: NutritionPlan) -> None:
        """Actualiza estado, aprobación y comentario del plan."""
        result = await self._session.execute(
            select(NutritionPlanModel).where(NutritionPlanModel.id == plan.plan_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return
        row.status = plan.status.value
        row.approved_by_vet_id = plan.approved_by_vet_id
        row.approval_timestamp = plan.approval_timestamp
        row.review_date = plan.review_date
        row.vet_comment = plan.vet_comment
        row.content = plan.content
        await self._session.flush()

    async def find_by_id(self, plan_id: uuid.UUID) -> Optional[NutritionPlan]:
        """Busca plan por ID."""
        result = await self._session.execute(
            select(NutritionPlanModel).where(NutritionPlanModel.id == plan_id)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def find_active_by_pet(self, pet_id: uuid.UUID) -> Optional[NutritionPlan]:
        """Retorna el plan ACTIVE o PENDING_VET más reciente de la mascota."""
        result = await self._session.execute(
            select(NutritionPlanModel).where(
                NutritionPlanModel.pet_id == pet_id,
                NutritionPlanModel.status.in_(["ACTIVE", "PENDING_VET"]),
            ).order_by(NutritionPlanModel.created_at.desc()).limit(1)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[NutritionPlan]:
        """Lista todos los planes del owner."""
        result = await self._session.execute(
            select(NutritionPlanModel).where(
                NutritionPlanModel.owner_id == owner_id
            ).order_by(NutritionPlanModel.created_at.desc())
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def list_pending_vet(self) -> list[NutritionPlan]:
        """Lista todos los planes en PENDING_VET (dashboard vet)."""
        result = await self._session.execute(
            select(NutritionPlanModel).where(
                NutritionPlanModel.status == "PENDING_VET"
            ).order_by(NutritionPlanModel.created_at.asc())
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def count_active_by_owner(self, owner_id: uuid.UUID) -> int:
        """Cuenta planes ACTIVE o PENDING_VET del owner."""
        from sqlalchemy import func as sqlfunc
        result = await self._session.execute(
            select(sqlfunc.count()).select_from(NutritionPlanModel).where(
                NutritionPlanModel.owner_id == owner_id,
                NutritionPlanModel.status.in_(["ACTIVE", "PENDING_VET"]),
            )
        )
        return result.scalar() or 0

    async def list_recent_by_pet(
        self, pet_id: uuid.UUID, limit: int = 3
    ) -> list[NutritionPlan]:
        """
        Lista los planes más recientes de una mascota (activos y archivados).

        Usado por el agente para dar contexto histórico de planes anteriores.
        Orden: más reciente primero.
        """
        result = await self._session.execute(
            select(NutritionPlanModel)
            .where(NutritionPlanModel.pet_id == pet_id)
            .order_by(NutritionPlanModel.created_at.desc())
            .limit(limit)
        )
        return [_to_domain(row) for row in result.scalars().all()]
