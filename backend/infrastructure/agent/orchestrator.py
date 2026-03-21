"""
Orquestador LangGraph — NutriVet.IA.

Flujo:
  START → load_context → emergency_detector
    → condicional: emergency → referral_node → END
    → intent_classifier
    → condicional: 4 intents → 4 subgrafos/nodos
    → cada subgrafo → END

Singleton:
  El grafo compilado se crea UNA sola vez al inicio de la aplicación.
  Las dependencias de sesión DB se pasan por ContextVar (correcto en async — una var por task).
  En tests se usa build_orchestrator() con funciones mock inyectadas directamente.
"""
from __future__ import annotations

import threading
from contextvars import ContextVar
from typing import Any, Callable

from langgraph.graph import END, START, StateGraph

from backend.infrastructure.agent.nodes.emergency_detector import emergency_detector
from backend.infrastructure.agent.nodes.referral_node import referral_node
from backend.infrastructure.agent.state import NutriVetState

# ── ContextVars para dependencias por-request ─────────────────────────────────
# Cada request asyncio corre en su propio Task y tiene su propio valor de ContextVar.
# Thread-safe: asyncio garantiza aislamiento por task.
_ctx_load_context_fn: ContextVar[Callable | None] = ContextVar(
    "nutrivet_load_context_fn", default=None
)
_ctx_plan_generation_fn: ContextVar[Callable | None] = ContextVar(
    "nutrivet_plan_generation_fn", default=None
)
_ctx_consultation_fn: ContextVar[Callable | None] = ContextVar(
    "nutrivet_consultation_fn", default=None
)
_ctx_scanner_fn: ContextVar[Callable | None] = ContextVar(
    "nutrivet_scanner_fn", default=None
)
_ctx_intent_classifier_fn: ContextVar[Callable | None] = ContextVar(
    "nutrivet_intent_classifier_fn", default=None
)


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


# ── Wrappers que delegan a ContextVars ────────────────────────────────────────

async def _dynamic_load_context(state: NutriVetState) -> NutriVetState:
    """Wrapper de load_context que usa la función del ContextVar actual."""
    fn = _ctx_load_context_fn.get()
    if fn is None:
        raise RuntimeError("load_context_fn no configurado para este request")
    return await fn(state)


async def _dynamic_plan_generation(state: NutriVetState) -> NutriVetState:
    """Wrapper de plan_generation que usa la función del ContextVar actual."""
    fn = _ctx_plan_generation_fn.get()
    if fn is None:
        raise RuntimeError("plan_generation_fn no configurado para este request")
    return await fn(state)


async def _dynamic_consultation(state: NutriVetState) -> NutriVetState:
    """Wrapper de consultation que usa la función del ContextVar actual."""
    fn = _ctx_consultation_fn.get()
    if fn is None:
        raise RuntimeError("consultation_fn no configurado para este request")
    return await fn(state)


async def _dynamic_scanner(state: NutriVetState) -> NutriVetState:
    """Wrapper de scanner que usa la función del ContextVar actual."""
    fn = _ctx_scanner_fn.get()
    if fn is None:
        raise RuntimeError("scanner_fn no configurado para este request")
    return await fn(state)


async def _dynamic_intent_classifier(state: NutriVetState) -> NutriVetState:
    """Wrapper de intent_classifier que usa la función del ContextVar actual."""
    fn = _ctx_intent_classifier_fn.get()
    if fn is None:
        raise RuntimeError("intent_classifier_fn no configurado para este request")
    return await fn(state)


# ── Singleton del grafo compilado ─────────────────────────────────────────────

_SINGLETON_LOCK = threading.Lock()
_SINGLETON_GRAPH: Any = None  # CompiledGraph — compilado una vez


def _get_singleton_graph() -> Any:
    """
    Retorna el grafo singleton compilado.

    Thread-safe: usa double-checked locking.
    El grafo se compila una sola vez con wrappers que delegan a ContextVars.
    """
    global _SINGLETON_GRAPH
    if _SINGLETON_GRAPH is not None:
        return _SINGLETON_GRAPH

    with _SINGLETON_LOCK:
        if _SINGLETON_GRAPH is not None:  # double-check
            return _SINGLETON_GRAPH

        graph = StateGraph(NutriVetState)

        # Nodos fijos (determinísticos — no necesitan session)
        graph.add_node("emergency_detector", emergency_detector)
        graph.add_node("referral_node", referral_node)

        # Nodos dinámicos — delegan a ContextVars por-request
        graph.add_node("load_context", _dynamic_load_context)
        graph.add_node("intent_classifier", _dynamic_intent_classifier)
        graph.add_node("plan_generation", _dynamic_plan_generation)
        graph.add_node("consultation", _dynamic_consultation)
        graph.add_node("scanner", _dynamic_scanner)

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

        _SINGLETON_GRAPH = graph.compile()

    return _SINGLETON_GRAPH


def set_request_functions(
    load_context_fn: Callable,
    intent_classifier_fn: Callable,
    plan_generation_fn: Callable,
    consultation_fn: Callable,
    scanner_fn: Callable,
) -> None:
    """
    Configura las funciones por-request en los ContextVars del task actual.

    Llamar ANTES de cada ainvoke(). Los ContextVars son automáticamente
    aislados por asyncio Task — no hay riesgo de cross-contamination entre requests.
    """
    _ctx_load_context_fn.set(load_context_fn)
    _ctx_intent_classifier_fn.set(intent_classifier_fn)
    _ctx_plan_generation_fn.set(plan_generation_fn)
    _ctx_consultation_fn.set(consultation_fn)
    _ctx_scanner_fn.set(scanner_fn)


def get_orchestrator() -> Any:
    """
    Retorna el orquestador singleton compilado.

    Usar en producción. Las funciones por-request deben configurarse
    con set_request_functions() antes de cada invocación.
    """
    return _get_singleton_graph()


def build_orchestrator(
    load_context_fn: Callable,
    intent_classifier_fn: Callable,
    plan_generation_fn: Callable,
    consultation_fn: Callable,
    scanner_fn: Callable,
) -> Any:
    """
    Construye y compila un nuevo grafo con las funciones inyectadas.

    Usar EN TESTS para inyectar mocks directamente sin afectar el singleton.
    En producción usar get_orchestrator() + set_request_functions().
    """
    graph = StateGraph(NutriVetState)

    graph.add_node("load_context", load_context_fn)
    graph.add_node("emergency_detector", emergency_detector)
    graph.add_node("intent_classifier", intent_classifier_fn)
    graph.add_node("referral_node", referral_node)
    graph.add_node("plan_generation", plan_generation_fn)
    graph.add_node("consultation", consultation_fn)
    graph.add_node("scanner", scanner_fn)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "emergency_detector")

    graph.add_conditional_edges(
        "emergency_detector",
        _route_after_emergency,
        {
            "referral_node": "referral_node",
            "intent_classifier": "intent_classifier",
        },
    )

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

    graph.add_edge("referral_node", END)
    graph.add_edge("plan_generation", END)
    graph.add_edge("consultation", END)
    graph.add_edge("scanner", END)

    return graph.compile()
