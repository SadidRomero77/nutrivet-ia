"""
LoadContext — Nodo que carga PetProfile y plan activo desde DB.

Primer nodo del pipeline: enriquece el estado con datos de la mascota.
No llama LLM.
"""
from __future__ import annotations

from typing import Any

from backend.application.interfaces.pet_repository import IPetRepository
from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.safety.breed_restriction_engine import (
    get_breed_restrictions,
    has_breed_restrictions,
)
from backend.infrastructure.agent.state import NutriVetState


def _pet_to_dict(pet: Any) -> dict[str, Any]:
    """Serializa PetProfile a dict (sin PII — solo campos técnicos)."""
    breed_id: str | None = getattr(pet, "breed_id", None)

    # Restricciones preventivas por raza (A-08) — solo si hay raza registrada
    breed_restrictions: dict[str, Any] = {}
    if breed_id and has_breed_restrictions(breed_id):
        r = get_breed_restrictions(breed_id)
        if r is not None:
            breed_restrictions = {
                "prohibited_preventive": sorted(r.prohibited_preventive),
                "limited_preventive": sorted(r.limited_preventive),
                "recommended_preventive": sorted(r.recommended_preventive),
                "special_preventive": sorted(r.special_preventive),
                "alert": r.alert,
            }

    # Nombre de raza: preferir campo breed (string) sobre breed_id
    breed_name: str | None = getattr(pet, "breed", None) or breed_id

    # Campos opcionales con fallback seguro
    sex_val = pet.sex.value if hasattr(pet, "sex") and pet.sex else None
    size_val = pet.size.value if hasattr(pet, "size") and pet.size else None
    current_diet_val = (
        pet.current_diet.value
        if hasattr(pet, "current_diet") and pet.current_diet
        else None
    )

    result: dict[str, Any] = {
        "pet_id": str(pet.pet_id),
        "species": pet.species.value,
        "breed": breed_name,
        "sex": sex_val,
        "weight_kg": pet.weight_kg,
        "age_months": pet.age_months,
        "size": size_val,
        "reproductive_status": pet.reproductive_status.value,
        "activity_level": pet.activity_level.value,
        "bcs": pet.bcs.value,
        "medical_conditions": [c.value for c in pet.medical_conditions],
        "allergies": list(pet.allergies) if pet.allergies else [],
        "current_diet": current_diet_val,
        "owner_id": str(pet.owner_id),
        "breed_id": breed_id,
    }
    if breed_restrictions:
        result["breed_preventive_restrictions"] = breed_restrictions
    return result


def _plan_to_dict(plan: Any) -> dict[str, Any]:
    """Serializa NutritionPlan a dict (con content completo para plan activo)."""
    return {
        "plan_id": str(plan.plan_id),
        "status": plan.status.value,
        "plan_type": plan.plan_type.value,
        "modality": plan.modality.value,
        "rer_kcal": plan.rer_kcal,
        "der_kcal": plan.der_kcal,
        "content": plan.content or {},
    }


def _plan_to_summary(plan: Any) -> dict[str, Any]:
    """
    Serializa NutritionPlan a resumen compacto para historial.

    Solo incluye metadatos — sin content JSONB completo para no saturar el contexto.
    """
    created_at_str = (
        plan.created_at.strftime("%Y-%m-%d")
        if hasattr(plan, "created_at") and plan.created_at
        else "fecha desconocida"
    )
    content = plan.content or {}
    modality_val = plan.modality.value if hasattr(plan.modality, "value") else str(plan.modality)
    return {
        "plan_id": str(plan.plan_id),
        "status": plan.status.value,
        "plan_type": plan.plan_type.value,
        "modality": modality_val,
        "rer_kcal": plan.rer_kcal,
        "der_kcal": plan.der_kcal,
        "created_at": created_at_str,
        # Incluir solo nombres de ingredientes principales (sin cantidades/proporciones)
        "main_ingredients": [
            ing.get("nombre", "") if isinstance(ing, dict) else str(ing)
            for ing in (content.get("ingredientes") or [])[:5]
        ],
    }


async def load_context(
    state: NutriVetState,
    pet_repo: IPetRepository,
    plan_repo: IPlanRepository,
) -> NutriVetState:
    """
    Carga PetProfile y plan activo desde DB.

    Valida que el usuario autenticado tiene acceso a la mascota:
    - owner: solo puede acceder a sus propias mascotas (pet.owner_id == user_id)
    - vet: puede acceder a mascotas asignadas (pet.vet_id == user_id) o propias

    Si la mascota no existe → error en state.
    Si no hay plan activo → active_plan = None.
    """
    import uuid

    pet_id_str = state.get("pet_id", "")
    if not pet_id_str:
        return {**state, "pet_profile": None, "active_plan": None, "error": "pet_id requerido"}

    try:
        pet_id = uuid.UUID(pet_id_str)
    except ValueError:
        return {**state, "pet_profile": None, "active_plan": None, "error": "pet_id con formato inválido"}

    pet = await pet_repo.find_by_id(pet_id)
    if pet is None:
        return {**state, "pet_profile": None, "active_plan": None, "error": "Mascota no encontrada"}

    # Validación de acceso — Constitution REGLA 6 (aislamiento de datos)
    user_id_str = state.get("user_id", "")
    user_role = state.get("user_role", "owner")
    try:
        requester_id = uuid.UUID(user_id_str)
    except ValueError:
        return {**state, "pet_profile": None, "active_plan": None, "error": "Sesión inválida"}

    is_owner = pet.owner_id == requester_id
    is_assigned_vet = user_role == "vet" and pet.vet_id is not None and pet.vet_id == requester_id

    if not (is_owner or is_assigned_vet):
        return {**state, "pet_profile": None, "active_plan": None, "error": "Acceso denegado a esta mascota"}

    pet_dict = _pet_to_dict(pet)

    active_plan = await plan_repo.find_active_by_pet(pet_id)
    plan_dict = _plan_to_dict(active_plan) if active_plan else None

    # Historial de planes recientes (para memoria contextual del agente)
    plan_history: list[dict[str, Any]] = []
    try:
        recent_plans = await plan_repo.list_recent_by_pet(pet_id, limit=3)
        for p in recent_plans:
            # Excluir el plan activo actual para no duplicar
            if active_plan and str(p.plan_id) == str(active_plan.plan_id):
                continue
            plan_history.append(_plan_to_summary(p))
    except AttributeError:
        # list_recent_by_pet puede no estar implementado en mocks de test
        pass

    return {**state, "pet_profile": pet_dict, "active_plan": plan_dict, "plan_history": plan_history}
