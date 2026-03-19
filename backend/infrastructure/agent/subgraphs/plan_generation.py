"""
PlanGenerationSubgraph — 10 nodos para generación de planes nutricionales.

Nodos determinísticos (sin LLM): 1, 2, 3, 4, 5
Nodo LLM: 6 (generate_with_llm)
Nodos post-LLM: 7, 8, 9, 10

Constitution REGLAs activas: 1 (toxicidad), 2 (restricciones), 3 (RER/DER),
4 (HITL), 5 (routing), 6 (PII).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from backend.application.interfaces.agent_trace_repository import IAgentTraceRepository
from backend.application.interfaces.plan_repository import IPlanRepository
from backend.application.llm.llm_router import LLMRouter
from backend.domain.aggregates.nutrition_plan import (
    NutritionPlan, PlanModality, PlanStatus, PlanType,
)
from backend.domain.aggregates.user_account import UserTier
from backend.domain.nutrition.nrc_calculator import NRCCalculator
from backend.domain.safety.food_safety_checker import FoodSafetyChecker
from backend.domain.safety.medical_restriction_engine import MedicalRestrictionEngine
from backend.domain.value_objects.bcs import BCS
from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.llm.openrouter_client import OpenRouterClient


# ─── Nodo 1: load_context (ya ejecutado en el orquestador antes del subgrafo) ─

def nodo_1_verificar_contexto(state: NutriVetState) -> NutriVetState:
    """Verifica que el contexto de la mascota esté cargado."""
    if not state.get("pet_profile"):
        raise ValueError(state.get("error", "pet_profile no disponible en state"))
    return state


# ─── Nodo 2: calculate_nutrition ──────────────────────────────────────────────

def nodo_2_calculate_nutrition(state: NutriVetState) -> NutriVetState:
    """
    Calcula RER/DER de forma determinística (REGLA 3 — nunca LLM).
    No hace llamadas externas.
    """
    pet = state["pet_profile"]

    rer = NRCCalculator.calculate_rer(pet["weight_kg"])
    der = NRCCalculator.calculate_der(
        rer=rer,
        species=pet["species"],
        age_months=pet["age_months"],
        reproductive_status=pet["reproductive_status"],
        activity_level=pet["activity_level"],
        bcs=pet["bcs"],
    )
    bcs_phase = BCS(pet["bcs"]).phase.value

    return {**state, "rer_kcal": round(rer, 2), "der_kcal": round(der, 2), "bcs_phase": bcs_phase}


# ─── Nodo 3: apply_restrictions ───────────────────────────────────────────────

def nodo_3_apply_restrictions(state: NutriVetState) -> NutriVetState:
    """
    Obtiene restricciones médicas hard-coded (REGLA 2 — LLM no puede sobrescribir).
    No hace llamadas externas.
    """
    pet = state["pet_profile"]
    conditions = pet.get("medical_conditions", [])

    result = MedicalRestrictionEngine.get_restrictions_for_conditions(conditions)
    restrictions = list(result.prohibited)

    return {**state, "medical_restrictions": restrictions}


# ─── Nodo 4: check_safety_pre ─────────────────────────────────────────────────

def nodo_4_check_safety_pre(state: NutriVetState) -> NutriVetState:
    """
    Valida alergias registradas contra la base de toxicidad (pre-LLM).
    Si hay alergia tóxica → registra en state para que el prompt lo incluya.
    No hace llamadas externas.
    """
    pet = state["pet_profile"]
    allergies = pet.get("allergies", [])
    species = pet.get("species", "perro")

    toxic_allergies: list[str] = []
    for allergy in allergies:
        check = FoodSafetyChecker.check_ingredient(ingredient=allergy, species=species)
        if check.is_toxic:
            toxic_allergies.append(allergy)

    return {**state, "allergy_list": allergies}


# ─── Nodo 5: select_llm ───────────────────────────────────────────────────────

def nodo_5_select_llm(state: NutriVetState) -> NutriVetState:
    """
    Selecciona el modelo LLM según tier y condiciones (REGLA 5 — determinístico).
    No hace llamadas externas.
    """
    pet = state["pet_profile"]
    conditions_count = len(pet.get("medical_conditions", []))
    tier_str = state.get("user_tier", "FREE")

    try:
        tier = UserTier(tier_str.lower())
    except ValueError:
        tier = UserTier.FREE

    model = LLMRouter.select_model(tier=tier, conditions_count=conditions_count)

    return {**state, "llm_model": model}


# ─── Nodo 6: generate_with_llm ────────────────────────────────────────────────

def _build_system_prompt(restrictions: list[str], allergies: list[str]) -> str:
    """Construye system prompt con restricciones (REGLA 6: sin PII)."""
    base = (
        "Eres un nutricionista veterinario especializado en alimentación de perros y gatos. "
        "Genera un plan nutricional estructurado en JSON con 5 secciones: "
        "perfil_nutricional, ingredientes, porciones, instrucciones_preparacion, transicion_dieta. "
        "Solo usa ingredientes disponibles en LATAM en español. "
        "NO incluyas ningún dato personal del dueño ni nombre de la mascota. "
        "Responde SOLO con JSON válido."
    )
    combined = restrictions + allergies
    if combined:
        restriction_text = "; ".join(combined[:10])
        base += f"\n\nRESTRICCIONES (no negociables): {restriction_text}"
    return base


def _build_user_prompt(
    species: str,
    weight_kg: float,
    rer_kcal: float,
    der_kcal: float,
    modality: str,
    bcs_phase: str,
) -> str:
    """Construye user prompt sin PII (REGLA 6)."""
    return (
        f"Especie: {species}. Peso: {weight_kg} kg. "
        f"RER: {rer_kcal:.1f} kcal/día. DER: {der_kcal:.1f} kcal/día. "
        f"Modalidad: {modality}. Fase de peso: {bcs_phase}. "
        "Genera el plan nutricional completo en JSON con las 5 secciones indicadas."
    )


async def nodo_6_generate_with_llm(
    state: NutriVetState,
    llm_client: OpenRouterClient | None = None,
) -> NutriVetState:
    """Genera el plan nutricional con el LLM seleccionado (REGLA 5)."""
    client = llm_client or OpenRouterClient()
    pet = state["pet_profile"]

    system_prompt = _build_system_prompt(
        state.get("medical_restrictions", []),
        state.get("allergy_list", []),
    )
    user_prompt = _build_user_prompt(
        species=pet["species"],
        weight_kg=pet["weight_kg"],
        rer_kcal=state["rer_kcal"],
        der_kcal=state["der_kcal"],
        modality=state.get("modality", "natural"),
        bcs_phase=state["bcs_phase"],
    )

    response = await client.generate(
        model=state["llm_model"],
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    traces = list(state.get("agent_traces", []))
    traces.append({
        "llm_model": response.model_used,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "latency_ms": response.latency_ms,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return {**state, "llm_response_content": response.content, "agent_traces": traces}


# ─── Nodo 7: validate_output ──────────────────────────────────────────────────

def nodo_7_validate_output(state: NutriVetState) -> NutriVetState:
    """
    Valida el output del LLM con FoodSafetyChecker (REGLA 1 — post-LLM).
    Si hay ingrediente tóxico → levanta ValueError (job → FAILED).
    """
    raw = state.get("llm_response_content", "")
    pet = state["pet_profile"]
    species = pet.get("species", "perro")

    try:
        plan_content: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM retornó JSON inválido: {e}") from e

    ingredients_raw: list[str] = []
    ing = plan_content.get("ingredientes")
    if isinstance(ing, list):
        ingredients_raw = [i["nombre"] if isinstance(i, dict) else str(i) for i in ing]
    elif isinstance(ing, dict):
        ingredients_raw = list(ing.keys())

    toxicity_results = FoodSafetyChecker.validate_plan_ingredients(
        ingredients=ingredients_raw, species=species
    )
    toxic_found = [r.ingredient for r in toxicity_results if r.is_toxic]
    if toxic_found:
        raise ValueError(
            f"Plan rechazado: ingredientes tóxicos detectados: {toxic_found}"
        )

    return {**state, "plan_content": plan_content}


# ─── Nodo 8: generate_substitutes ─────────────────────────────────────────────

def nodo_8_generate_substitutes(state: NutriVetState) -> NutriVetState:
    """Genera el substitute_set: ingredientes aprobados para sustitución sin HITL."""
    plan_content = dict(state.get("plan_content") or {})
    forbidden = [f.lower() for f in state.get("medical_restrictions", [])]

    ingredients_raw: list[str] = []
    ing = plan_content.get("ingredientes")
    if isinstance(ing, list):
        ingredients_raw = [i["nombre"] if isinstance(i, dict) else str(i) for i in ing]
    elif isinstance(ing, dict):
        ingredients_raw = list(ing.keys())

    substitute_set = [
        ing_name for ing_name in ingredients_raw
        if ing_name.lower() not in forbidden
    ]
    plan_content["substitute_set"] = substitute_set

    return {**state, "plan_content": plan_content}


# ─── Nodo 9: determine_hitl ───────────────────────────────────────────────────

def nodo_9_determine_hitl(state: NutriVetState) -> NutriVetState:
    """
    Determina si el plan requiere revisión vet (REGLA 4).
    Mascotas con condición médica → PENDING_VET.
    Mascotas sanas → ACTIVE directo.
    """
    pet = state["pet_profile"]
    has_conditions = len(pet.get("medical_conditions", [])) > 0
    return {**state, "requires_vet_review": has_conditions}


# ─── Nodo 10: persist_and_notify ──────────────────────────────────────────────

async def nodo_10_persist_and_notify(
    state: NutriVetState,
    plan_repo: IPlanRepository,
    trace_repo: IAgentTraceRepository,
) -> NutriVetState:
    """
    Persiste el plan y las trazas. Actualiza state con plan_id.

    agent_traces son append-only — sin UPDATE (REGLA 6).
    """
    import uuid as _uuid

    pet = state["pet_profile"]
    pet_id = _uuid.UUID(pet["pet_id"])
    owner_id = _uuid.UUID(pet["owner_id"])
    requires_vet = state.get("requires_vet_review", False)

    plan_status = PlanStatus.PENDING_VET if requires_vet else PlanStatus.ACTIVE
    plan_type = PlanType.TEMPORAL_MEDICAL if requires_vet else PlanType.ESTANDAR

    from backend.domain.value_objects.bcs import BCSPhase
    bcs_phase = BCSPhase(state["bcs_phase"])

    traces = state.get("agent_traces", [])
    last_trace = traces[-1] if traces else {}

    trace_id = await trace_repo.append(
        pet_id=pet_id,
        plan_id=None,
        llm_model=last_trace.get("llm_model", "unknown"),
        prompt_tokens=last_trace.get("prompt_tokens", 0),
        completion_tokens=last_trace.get("completion_tokens", 0),
        latency_ms=last_trace.get("latency_ms", 0),
        input_summary={
            "species": pet["species"],
            "weight_kg": pet["weight_kg"],
            "conditions_count": len(pet.get("medical_conditions", [])),
            "modality": state.get("modality", "natural"),
        },
        output_summary={
            "rer_kcal": state["rer_kcal"],
            "der_kcal": state["der_kcal"],
        },
        created_at=datetime.utcnow(),
    )

    plan_content = state.get("plan_content") or {}
    plan_id = _uuid.uuid4()
    modality_val = state.get("modality", "natural")

    plan = NutritionPlan(
        plan_id=plan_id,
        pet_id=pet_id,
        owner_id=owner_id,
        plan_type=plan_type,
        status=plan_status,
        modality=PlanModality(modality_val),
        rer_kcal=state["rer_kcal"],
        der_kcal=state["der_kcal"],
        weight_phase=bcs_phase,
        llm_model_used=last_trace.get("llm_model", "unknown"),
        content=plan_content,
        approved_by_vet_id=None,
        approval_timestamp=None,
        review_date=None,
        vet_comment=None,
        agent_trace_id=trace_id,
    )
    await plan_repo.save(plan)

    response = (
        f"✅ Plan nutricional generado.\n"
        f"RER: {state['rer_kcal']} kcal/día · DER: {state['der_kcal']} kcal/día.\n"
        + ("⏳ En revisión veterinaria — recibirás notificación cuando esté listo."
           if requires_vet else
           "🟢 Plan activo y disponible.")
    )

    return {**state, "plan_id": str(plan_id), "response": response}
