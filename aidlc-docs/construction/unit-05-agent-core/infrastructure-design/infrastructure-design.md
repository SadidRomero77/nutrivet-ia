# Infrastructure Design — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## LangGraph StateGraph

```python
# infrastructure/agent/langgraph_orchestrator.py
from langgraph.graph import StateGraph, END

def build_nutrivet_graph() -> CompiledGraph:
    """Construye y compila el grafo LangGraph de NutriVet.IA."""
    graph = StateGraph(NutriVetState)

    # Nodos del orquestador
    graph.add_node("load_context", load_context_node)
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("referral_node", referral_node)
    graph.add_node("plan_generation_subgraph", plan_generation_subgraph)
    graph.add_node("consultation_subgraph", consultation_subgraph)
    graph.add_node("scanner_subgraph", scanner_subgraph)
    graph.add_node("persist_traces", persist_traces_node)

    # Edges
    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "classify_intent")
    graph.add_conditional_edges("classify_intent", route_by_intent, {
        "referral": "referral_node",
        "plan":     "plan_generation_subgraph",
        "consult":  "consultation_subgraph",
        "scan":     "scanner_subgraph",
    })
    graph.add_edge("referral_node", "persist_traces")
    graph.add_edge("plan_generation_subgraph", "persist_traces")
    graph.add_edge("consultation_subgraph", "persist_traces")
    graph.add_edge("scanner_subgraph", "persist_traces")
    graph.add_edge("persist_traces", END)

    return graph.compile()
```

## Nodo: IntentClassifier

```python
# infrastructure/agent/nodes/intent_classifier.py
async def classify_intent_node(state: NutriVetState) -> NutriVetState:
    """Clasificar intención del mensaje. Usa lógica determinista primero."""
    # 1. Detección de emergencia (determinista — sin LLM)
    classifier = QueryClassifier()  # domain service
    classification = classifier.classify(state["user_message"])

    state["intent"] = classification.intent
    state["is_emergency"] = classification.is_emergency
    return state
```

## Subgrafo: PlanGenerationSubgraph

```python
# infrastructure/agent/subgraphs/plan_generation_subgraph.py
def build_plan_generation_subgraph() -> CompiledGraph:
    sg = StateGraph(NutriVetState)
    sg.add_node("validate_request", validate_plan_request_node)
    sg.add_node("enqueue_job", enqueue_plan_job_node)
    sg.add_node("hitl_router", hitl_router_node)
    sg.set_entry_point("validate_request")
    sg.add_edge("validate_request", "enqueue_job")
    sg.add_edge("enqueue_job", "hitl_router")
    sg.add_edge("hitl_router", END)
    return sg.compile()
```

## Nodo: ReferralNode

```python
# infrastructure/agent/nodes/referral_node.py
REFERRAL_TEMPLATE = """
Esta consulta requiere evaluación por un médico veterinario.

{emergency_text}

Tu veterinario de confianza puede orientarte correctamente.
NutriVet.IA proporciona asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario.
"""

EMERGENCY_TEXT = """
⚠️ ATENCIÓN URGENTE: Si tu mascota muestra signos de emergencia médica,
lleva inmediatamente a tu mascota al veterinario más cercano.
No administres medicamentos sin indicación veterinaria.
"""

async def referral_node(state: NutriVetState) -> NutriVetState:
    """Nodo terminal para consultas médicas y emergencias."""
    emergency_text = EMERGENCY_TEXT if state["is_emergency"] else ""
    state["agent_response"] = REFERRAL_TEMPLATE.format(emergency_text=emergency_text)
    return state
```

## Dependencias del Agent Core

```
langgraph==0.1.x          # StateGraph, nodos, edges
langchain-core==0.1.x     # BaseMessage, ChatPromptTemplate
langchain-openai==0.1.x   # ChatOpenAI (usado via OpenRouter base_url)
redis==5.x                # checkpointer + quota counters
```
