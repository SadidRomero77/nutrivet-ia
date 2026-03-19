"""
IngredientSubstitutionUseCase — Solicitud de sustitución de ingrediente.

Regla:
  - Sustituto dentro del substitute_set → ACTIVE directo.
  - Sustituto fuera del set → PENDING_VET (requiere revisión vet).
"""
from __future__ import annotations

import uuid
from typing import Any

from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.aggregates.nutrition_plan import PlanStatus
from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.safety.food_safety_checker import FoodSafetyChecker


class IngredientSubstitutionUseCase:
    """Gestiona sustituciones de ingredientes en planes activos o pending."""

    def __init__(self, plan_repo: IPlanRepository) -> None:
        self._plan_repo = plan_repo

    async def substitute(
        self,
        plan_id: uuid.UUID,
        requester_id: uuid.UUID,
        original_ingredient: str,
        substitute_ingredient: str,
    ) -> dict[str, Any]:
        """
        Solicita sustitución de un ingrediente.

        Args:
            plan_id: ID del plan a modificar.
            requester_id: ID del owner solicitante.
            original_ingredient: Ingrediente a reemplazar.
            substitute_ingredient: Ingrediente sustituto propuesto.

        Returns:
            Dict con requires_vet_review y plan_status resultante.

        Raises:
            DomainError: Si el plan no existe, no pertenece al owner,
                         o el sustituto es tóxico (REGLA 1).
        """
        plan = await self._plan_repo.find_by_id(plan_id)
        if plan is None:
            raise DomainError(f"Plan con ID '{plan_id}' no encontrado.")
        if plan.owner_id != requester_id:
            raise DomainError("Acceso denegado: no eres el dueño de este plan.")

        # REGLA 1: Verificar toxicidad del sustituto
        # Determinamos especie desde el plan (no incluimos PII — solo valor)
        species = "perro"  # Default — en producción se carga del PetProfile

        toxicity = FoodSafetyChecker.check_ingredient(
            ingredient=substitute_ingredient, species=species
        )
        if toxicity.is_toxic:
            raise DomainError(
                f"El ingrediente '{substitute_ingredient}' es tóxico para {species}. "
                "No se puede usar como sustituto."
            )

        # Verificar si el sustituto está en el substitute_set del plan
        content = plan.content or {}
        approved_substitutes: list[str] = content.get("substitute_set", [])
        in_set = substitute_ingredient.lower() in [s.lower() for s in approved_substitutes]

        requires_vet_review = not in_set

        if requires_vet_review and plan.status == PlanStatus.ACTIVE:
            plan.add_medical_condition_requires_review()
            await self._plan_repo.update(plan)

        return {
            "original_ingredient": original_ingredient,
            "substitute_ingredient": substitute_ingredient,
            "requires_vet_review": requires_vet_review,
            "plan_status": plan.status.value,
        }
