"""
HitlReviewUseCase — Aprobación y devolución de planes por veterinario.

Constitution REGLA 4:
  - Solo mascotas con condición médica generan plan PENDING_VET.
  - Vet aprueba → ACTIVE.
  - Vet devuelve con comentario obligatorio → PENDING_VET (no RECHAZADO).
  - No existe estado RECHAZADO.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Optional

from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.exceptions.domain_errors import DomainError


class HitlReviewUseCase:
    """
    Casos de uso de revisión HITL por veterinario.

    Implementa:
    - approve: Vet aprueba plan PENDING_VET → ACTIVE.
    - return_to_owner: Vet devuelve con comentario obligatorio → PENDING_VET.
    """

    def __init__(self, plan_repo: IPlanRepository) -> None:
        self._plan_repo = plan_repo

    async def approve(
        self,
        plan_id: uuid.UUID,
        vet_id: uuid.UUID,
        review_date: Optional[date] = None,
    ) -> dict[str, Any]:
        """
        Vet aprueba plan: PENDING_VET → ACTIVE.

        Args:
            plan_id: ID del plan a aprobar.
            vet_id: ID del veterinario que aprueba.
            review_date: Fecha de revisión (obligatorio para TEMPORAL_MEDICAL).

        Returns:
            Dict con status, approved_by_vet_id, review_date.

        Raises:
            DomainError: Si el plan no existe, no está en PENDING_VET,
                         o es TEMPORAL_MEDICAL sin review_date.
        """
        plan = await self._plan_repo.find_by_id(plan_id)
        if plan is None:
            raise DomainError(f"Plan con ID '{plan_id}' no encontrado.")

        # Delegar regla de dominio al aggregate
        plan.approve(vet_id=vet_id, review_date=review_date)
        await self._plan_repo.update(plan)

        return {
            "plan_id": plan.plan_id,
            "status": plan.status.value,
            "approved_by_vet_id": plan.approved_by_vet_id,
            "review_date": str(plan.review_date) if plan.review_date else None,
        }

    async def return_to_owner(
        self,
        plan_id: uuid.UUID,
        vet_id: uuid.UUID,
        comment: str,
    ) -> dict[str, Any]:
        """
        Vet devuelve plan al owner con comentario obligatorio.

        El plan permanece en PENDING_VET — no existe estado RECHAZADO.

        Args:
            plan_id: ID del plan a devolver.
            vet_id: ID del veterinario que devuelve.
            comment: Comentario obligatorio con instrucciones de corrección.

        Returns:
            Dict con status y vet_comment.

        Raises:
            DomainError: Si el plan no existe, no está en PENDING_VET,
                         o el comentario está vacío.
        """
        plan = await self._plan_repo.find_by_id(plan_id)
        if plan is None:
            raise DomainError(f"Plan con ID '{plan_id}' no encontrado.")

        # Delegar regla de dominio al aggregate
        plan.return_to_owner(vet_id=vet_id, comment=comment)
        await self._plan_repo.update(plan)

        return {
            "plan_id": plan.plan_id,
            "status": plan.status.value,
            "vet_comment": plan.vet_comment,
        }
