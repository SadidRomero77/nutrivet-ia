# Plan: NFR Design — Unit 05: agent-core

**Unidad**: unit-05-agent-core
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a agent-core

### Patrón: Deterministic Keyword Bypass (Emergency Detection)

**Contexto**: Las emergencias deben detectarse antes de cualquier llamada LLM para
garantizar < 1ms de respuesta y evitar que una emergencia quede "bloqueada" si
el LLM está caído.

**Diseño**:
```python
# infrastructure/agent/nodes/emergency_detector.py
EMERGENCY_KEYWORDS: frozenset[str] = frozenset({
    "convulsión", "convulsiones", "no respira", "inconsciente",
    "veneno", "envenenado", "sangrado profuso", "atropellado",
    "no puede caminar", "desmayo", "parálisis"
})

def emergency_detector(state: NutriVetState) -> NutriVetState:
    """Detecta emergencias ANTES del clasificador LLM. < 1ms. Sin red."""
    message_lower = state["user_message"].lower()
    is_emergency = any(kw in message_lower for kw in EMERGENCY_KEYWORDS)
    return {
        **state,
        "intent": "emergency" if is_emergency else None
        # None → pasa al intent_classifier LLM
    }
```

**Wiring en el grafo**:
```python
graph.add_conditional_edges(
    "emergency_detector",
    lambda s: "referral_node" if s["intent"] == "emergency" else "intent_classifier"
)
```

### Patrón: Conditional Routing (LangGraph conditional_edges)

**Contexto**: El orquestador enruta a 4 subgrafos según el intent clasificado.

**Diseño**:
```python
def route_by_intent(state: NutriVetState) -> str:
    """Routing determinístico post-clasificación. Sin LLM."""
    intent = state.get("intent", "consultation")
    return {
        "plan_generation": "plan_generation_subgraph",
        "consultation":    "consultation_subgraph",
        "scanner":         "scanner_subgraph",
        "referral":        "referral_node",
    }.get(intent, "consultation_subgraph")  # default seguro

graph.add_conditional_edges("intent_classifier", route_by_intent)
```

### Patrón: Subgraph Delegation

**Contexto**: Cada subgrafo es independiente y puede ser desarrollado por separado.
Los stubs garantizan que el orquestador funcione antes de que los subgrafos estén completos.

**Diseño del stub**:
```python
# infrastructure/agent/subgraphs/consultation.py (stub)
def consultation_subgraph(state: NutriVetState) -> NutriVetState:
    """Stub — será reemplazado en unit-07."""
    return {
        **state,
        "agent_response": "Consultation subgraph pendiente de implementación (unit-07)."
    }
# Contrato: recibe NutriVetState, retorna NutriVetState con agent_response poblado
```

### Patrón: Append-Only Trace Accumulation in State

**Contexto**: Las trazas se acumulan durante el request y se persisten al final,
evitando múltiples escrituras a DB durante el grafo.

**Diseño**:
```python
# En cualquier nodo que genere una traza:
def add_trace(state: NutriVetState, trace: dict) -> NutriVetState:
    """Acumula traza en el estado. Persiste en nodo persist_and_notify."""
    return {
        **state,
        "agent_traces": [*state["agent_traces"], trace]
    }

# En nodo persist_and_notify (último nodo del plan subgraph):
for trace in state["agent_traces"]:
    await agent_trace_repo.add(AgentTrace(**trace))
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `nodes/emergency_detector.py` | 100% | Unit tests — todos los keywords |
| `nodes/intent_classifier.py` | 80% | Unit tests con LLM mock |
| `nodes/referral_node.py` | 100% | Unit tests — emergencia + no emergencia |
| `subgraphs/plan_generation.py` | 85% | Integration tests |
| `orchestrator.py` (routing) | 80% | Integration tests |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- Unit spec: `inception/units/unit-05-agent-core.md`
- Constitution: REGLA 1, 2, 3 (determinismo de nodos no-LLM)
