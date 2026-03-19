"""
Orquestador LangGraph — NutriVet.IA.

Flujo:
  START → load_context → emergency_detector
    → condicional: emergency → referral_node → END
    → intent_classifier
    → condicional: 4 intents → 4 subgrafos/nodos
    → cada subgrafo → END

Singleton ORCHESTRATOR compilado una vez y reutilizado entre requests.
"""
from __future__ import annotations

from typing import Callable

from langgraph.graph import END, START, StateGraph

from backend.infrastructure.agent.nodes.emergency_detector import emergency_detector
from backend.infrastructure.agent.nodes.referral_node import referral_node
from backend.infrastructure.agent.state import NutriVetState


def _route_after_emergency(state: NutriVetState) -> str:
    """Routing condicional: si ya se detectó emergencia → referral, sino → intent_classifier."""
    if state.get("intent") == "emergency":
        return "referral_node"
    return "intent_classifier"


def _route_by_intent(state: NutriVetState) -> str:
    """Routing condicional por intent clasificado."""
    intent = state.get("intent", "consultation")
    routes = {
        "plan_generation": "plan_generation",
        "consultation": "consultation",
        "scanner": "scanner",
        "referral": "referral_node",
        "emergency": "referral_node",
    }
    return routes.get(intent, "consultation")


def build_orchestrator(
    load_context_fn: Callable,
    intent_classifier_fn: Callable,
    plan_generation_fn: Callable,
    consultation_fn: Callable,
    scanner_fn: Callable,
) -> StateGraph:
    """
    Construye y compila el grafo LangGraph con las funciones inyectadas.

    Separar la construcción del singleton permite tests con mocks inyectados.
    """
    graph = StateGraph(NutriVetState)

    # Nodos fijos (determinísticos)
    graph.add_node("load_context", load_context_fn)
    graph.add_node("emergency_detector", emergency_detector)
    graph.add_node("intent_classifier", intent_classifier_fn)
    graph.add_node("referral_node", referral_node)

    # Nodos de subgrafos
    graph.add_node("plan_generation", plan_generation_fn)
    graph.add_node("consultation", consultation_fn)
    graph.add_node("scanner", scanner_fn)

    # Edges lineales
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "emergency_detector")

    # Routing condicional después de emergency_detector
    graph.add_conditional_edges(
        "emergency_detector",
        _route_after_emergency,
        {
            "referral_node": "referral_node",
            "intent_classifier": "intent_classifier",
        },
    )

    # Routing condicional por intent
    graph.add_conditional_edges(
        "intent_classifier",
        _route_by_intent,
        {
            "plan_generation": "plan_generation",
            "consultation": "consultation",
            "scanner": "scanner",
            "referral_node": "referral_node",
        },
    )

    # Todos los terminales → END
    graph.add_edge("referral_node", END)
    graph.add_edge("plan_generation", END)
    graph.add_edge("consultation", END)
    graph.add_edge("scanner", END)

    return graph.compile()
