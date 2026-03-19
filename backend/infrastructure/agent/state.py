"""
NutriVetState — Estado compartido del grafo LangGraph.

Todos los nodos leen y escriben sobre este TypedDict.
Los campos son inmutables entre nodos (LangGraph reemplaza, no muta).
"""
from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class NutriVetState(TypedDict, total=False):
    """Estado compartido entre orquestador y subgrafos."""

    # Contexto del request
    user_id: str                          # UUID del usuario autenticado (str para serialización)
    pet_id: str                           # UUID de la mascota objetivo
    user_tier: str                        # "FREE" | "BASICO" | "PREMIUM" | "VET"
    user_role: str                        # "owner" | "vet"
    message: str                          # Mensaje original del usuario
    modality: str                         # "natural" | "concentrado" | "mixto"

    # Clasificación de intención
    intent: str                           # "plan_generation" | "consultation" | "scanner" | "referral" | "emergency"

    # Perfil de mascota (cargado por load_context)
    pet_profile: Optional[dict[str, Any]]   # PetProfile serializado
    active_plan: Optional[dict[str, Any]]   # NutritionPlan activo serializado

    # Datos nutricionales calculados (determinístico)
    rer_kcal: Optional[float]
    der_kcal: Optional[float]
    bcs_phase: Optional[str]
    medical_restrictions: list[str]       # Lista de restricciones hard-coded (REGLA 2)
    allergy_list: list[str]

    # LLM
    llm_model: Optional[str]             # Modelo seleccionado por LLMRouter (REGLA 5)
    llm_response_content: Optional[str]  # JSON raw del LLM
    plan_content: Optional[dict[str, Any]]  # plan_content parseado + substitute_set

    # Output del subgrafo
    response: Optional[str]              # Respuesta final al usuario
    plan_id: Optional[str]               # UUID del plan generado (si aplica)
    job_id: Optional[str]                # UUID del job ARQ (si aplica)
    requires_vet_review: bool            # HITL flag (REGLA 4)
    error: Optional[str]                 # Error capturado en el pipeline

    # Trazabilidad
    agent_traces: list[dict[str, Any]]   # Lista de trazas acumuladas (REGLA 6)

    # Historial conversacional
    conversation_history: list[dict[str, str]]  # [{role, content}, ...]
