"""
_plan_generation_core — Funciones compartidas de generación de planes.

Este módulo es la fuente única de verdad para la lógica que usaban
duplicada plan_generation_subgraph.py y plan_generation_worker.py.

Reglas de uso:
  - Agregar aquí cualquier lógica que exista en ambos archivos.
  - plan_generation_subgraph.py y plan_generation_worker.py importan de aquí.
  - No tiene dependencias de FastAPI, LangGraph ni ARQ — es infraestructura pura.

Constitution REGLAS activas: 1 (toxicidad post-LLM), 2 (restricciones), 4 (HITL).
"""
from __future__ import annotations

from typing import Any

from backend.domain.safety.food_safety_checker import FoodSafetyChecker
from backend.infrastructure.agent.validators.json_repair import safe_parse_plan_json
from backend.infrastructure.agent.validators.nutritional_validator import (
    enrich_plan_with_validation,
    validate_nutritional_plan,
)


def extract_ingredient_names(plan_content: dict[str, Any]) -> list[str]:
    """
    Extrae los nombres de ingredientes desde el contenido del plan generado por el LLM.

    Soporta dos formatos que el LLM puede retornar:
      - lista de dicts: [{"nombre": "pollo", ...}, ...]
      - dict: {"pollo": {...}, "arroz": {...}}

    Args:
        plan_content: Contenido JSON del plan (parseado).

    Returns:
        Lista de nombres de ingredientes en texto plano.
    """
    ingredients_raw: list[str] = []
    ing = plan_content.get("ingredientes")
    if isinstance(ing, list):
        ingredients_raw = [
            i["nombre"] if isinstance(i, dict) else str(i) for i in ing
        ]
    elif isinstance(ing, dict):
        ingredients_raw = list(ing.keys())
    return ingredients_raw


def validate_and_enrich_plan(
    raw_llm_response: str,
    species: str,
    conditions: list[str],
    der_kcal: float,
    rer_kcal: float,
    allergies: list[str],
    medical_restrictions: list[str],
    age_months: int,
) -> tuple[dict[str, Any], list[str]]:
    """
    Valida el output del LLM en 3 capas (Constitution REGLA 1).

    Capa 1: JSON repair + parsing robusto.
    Capa 2: FoodSafetyChecker — bloquea ingredientes tóxicos (tolerancia CERO).
    Capa 3: NutritionalValidator — coherencia calórica, proteína, Ca:P, restricciones.

    Args:
        raw_llm_response: Texto crudo retornado por el LLM.
        species:           "perro" | "gato".
        conditions:        Condiciones médicas activas (lista de strings).
        der_kcal:          DER calculado determinísticamente.
        rer_kcal:          RER calculado determinísticamente.
        allergies:         Lista de alergias registradas.
        medical_restrictions: Ingredientes prohibidos por condición (hard-coded).
        age_months:        Edad de la mascota en meses.

    Returns:
        Tuple (plan_content enriquecido, ingredients_raw).

    Raises:
        ValueError: Si hay ingredientes tóxicos o errores de validación bloqueantes.
    """
    # Capa 1: parseo robusto
    plan_content: dict[str, Any] = safe_parse_plan_json(raw_llm_response, der_kcal=der_kcal)

    # Capa 2: toxicidad (REGLA 1 — tolerancia CERO)
    ingredients_raw = extract_ingredient_names(plan_content)
    toxicity_results = FoodSafetyChecker.validate_plan_ingredients(
        ingredients=ingredients_raw, species=species
    )
    toxic_found = [r.ingredient for r in toxicity_results if r.is_toxic]
    if toxic_found:
        raise ValueError(
            f"Plan rechazado: ingredientes tóxicos detectados: {toxic_found}"
        )

    # Capa 3: validación nutricional NRC
    validation_result = validate_nutritional_plan(
        plan_content=plan_content,
        species=species,
        conditions=conditions,
        der_kcal=der_kcal,
        rer_kcal=rer_kcal,
        allergies=allergies,
        medical_restrictions=medical_restrictions,
        age_months=age_months,
    )
    if validation_result.blocking_errors:
        raise ValueError(
            "Plan rechazado por validación nutricional: "
            + " | ".join(validation_result.blocking_errors)
        )

    plan_content = enrich_plan_with_validation(plan_content, validation_result)
    return plan_content, ingredients_raw


def build_substitute_set(
    ingredients_raw: list[str],
    forbidden_ingredients: list[str],
) -> list[str]:
    """
    Genera el substitute_set: ingredientes del plan que el owner puede
    reemplazar sin necesidad de aprobación veterinaria adicional.

    Excluye ingredientes prohibidos por condición médica (REGLA 2).

    Args:
        ingredients_raw:      Lista de nombres de ingredientes del plan.
        forbidden_ingredients: Ingredientes prohibidos por condición (hard-coded).

    Returns:
        Lista de nombres de ingredientes sustituibles.
    """
    forbidden_lower = {f.lower() for f in forbidden_ingredients}
    return [ing for ing in ingredients_raw if ing.lower() not in forbidden_lower]


def requires_vet_review(conditions: list[str]) -> bool:
    """
    Determina si el plan requiere revisión veterinaria (REGLA 4 — HITL).

    Mascota con condición médica → True → plan PENDING_VET.
    Mascota sana               → False → plan ACTIVE directo.

    Args:
        conditions: Condiciones médicas activas.

    Returns:
        True si el plan debe ir a revisión veterinaria.
    """
    return len(conditions) > 0
