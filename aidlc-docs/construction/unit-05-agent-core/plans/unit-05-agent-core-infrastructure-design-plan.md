# Plan: Infrastructure Design — Unit 05: agent-core

**Unidad**: unit-05-agent-core
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| NutriVetOrchestrator (LangGraph) | In-process dentro del contenedor FastAPI |
| NutriVetState (TypedDict) | En memoria por request — sin estado entre requests |
| IntentClassifier node | `infrastructure/agent/nodes/intent_classifier.py` |
| HITLRouter node | `infrastructure/agent/nodes/hitl_router.py` |
| ReferralNode | `infrastructure/agent/nodes/referral_node.py` |
| Plan Generation Subgraph | `infrastructure/agent/subgraphs/plan_generation.py` |
| Consultation Subgraph (stub) | `infrastructure/agent/subgraphs/consultation.py` |
| Scanner Subgraph (stub) | `infrastructure/agent/subgraphs/scanner.py` |
| Orchestrator wiring | `infrastructure/agent/orchestrator.py` |

**Servidor**: Hetzner CPX31 — LangGraph corre in-process dentro del contenedor FastAPI.
No es un servicio separado. No requiere sidecar ni microservicio independiente.

### LangGraph — Sin Servidor Dedicado

LangGraph en NutriVet.IA es una biblioteca Python, no un servicio.
Cada request al endpoint `/v1/agent/process` crea una nueva instancia del grafo
e invoca `graph.ainvoke(initial_state)`.

```python
# infrastructure/agent/orchestrator.py
from langgraph.graph import StateGraph, END
from .state import NutriVetState
from .nodes import intent_classifier, referral_node, hitl_router
from .subgraphs import plan_generation_subgraph, consultation_stub, scanner_stub

def build_orchestrator() -> StateGraph:
    """Construye y compila el grafo LangGraph. Llamado al inicializar FastAPI."""
    graph = StateGraph(NutriVetState)
    # Nodos...
    # Edges...
    return graph.compile()

# Instancia singleton compilada al startup — reutilizada en todos los requests
ORCHESTRATOR = build_orchestrator()
```

### LLM — OpenRouter (mismo cliente que plan-service)

- Compartido con unit-04 vía `infrastructure/llm/openrouter_client.py`.
- IntentClassifier usa el modelo del tier del usuario (routing estándar).
- ReferralNode NO usa LLM — respuesta determinista.

### Persistencia de Estado

- El estado `NutriVetState` es efímero (in-memory por request).
- Los datos de dominio (pet_profile, active_plan) se cargan desde PostgreSQL al inicio.
- Las trazas acumuladas en `state["agent_traces"]` se persisten al final via
  `IAgentTraceRepository.add()` en el nodo `persist_and_notify`.

### Redis (ARQ)

- El nodo `persist_and_notify` en el plan generation subgraph puede encolar jobs en Redis
  para notificaciones push asíncronas (ARQ worker separado).
- Misma instancia Redis que plan-service.

### Variables de Entorno Requeridas

```bash
# Heredadas de los servicios anteriores — no adicionales para agent-core
OPENROUTER_API_KEY=<clave de OpenRouter>
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrivet
FERNET_KEY=<para desencriptar datos médicos del PetProfile>
```

### FastAPI Endpoint

```
POST /v1/agent/process
  Body: { pet_id, user_message, context? }
  Auth: JWT bearer
  Response: { intent, response?, job_id?, scan_result? }
```

## Notas Arquitecturales

1. **LangGraph in-process**: La decisión de no tener un servidor LangGraph separado
   simplifica el deploy (un contenedor menos) y elimina latencia de red inter-servicios.
   El tradeoff es que escalar el agente requiere escalar el FastAPI container completo.

2. **Estado efímero**: NutriVetState no persiste entre requests. Esto es por diseño —
   la conversación se reconstruye desde DB al inicio de cada request (últimos N mensajes).

3. **Stubs como contratos**: Los stubs de consultation y scanner definen el contrato
   de inputs/outputs que units 06/07 deben cumplir. No cambiar la firma del stub.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- Unit spec: `inception/units/unit-05-agent-core.md`
- ADR-019: LLM routing
