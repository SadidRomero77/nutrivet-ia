# Deployment Architecture — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Deployment del Agent Core

El agent core (LangGraph) vive dentro del contenedor `nutrivet-backend`. Los subgrafos son importados como módulos Python, no como servicios separados.

```
Hetzner CPX31 (Ashburn VA)
└── Coolify
    ├── nutrivet-backend (FastAPI + LangGraph, puerto 8000)
    │   └── app/
    │       ├── infrastructure/agent/
    │       │   ├── langgraph_orchestrator.py    ← StateGraph principal
    │       │   ├── nodes/
    │       │   │   ├── load_context.py
    │       │   │   ├── intent_classifier.py
    │       │   │   ├── referral_node.py
    │       │   │   └── hitl_router.py
    │       │   └── subgraphs/
    │       │       ├── plan_generation_subgraph.py
    │       │       ├── consultation_subgraph.py
    │       │       └── scanner_subgraph.py
    │       └── presentation/agent/
    │           └── agent_router.py             ← POST /agent/chat
    │
    ├── Redis (contenedor, puerto 6379)
    │   ├── ARQ job queue (unit-04)
    │   ├── Agent quota counters (conversation service)
    │   └── LangGraph checkpointer state (opcional)
    │
    └── PostgreSQL (contenedor, puerto 5432)
        └── agent_traces table (append-only)
```

## Endpoint del Agent

```
POST /agent/chat
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "pet_id": "uuid",
  "message": "¿Qué cantidad de pollo le doy a mi perro?",
  "session_id": "uuid"  // opcional, generado si no se provee
}

Response: text/event-stream (SSE) o application/json
```

## Redis para Estado del Agente

```
agent:quota:{pet_id}:{date}  → INCR, TTL 24h   (quota conversacional)
agent:state:{session_id}     → JSON, TTL 1h    (estado transitorio de sesión)
```

## LangGraph Checkpointer

Para sessions de larga duración, LangGraph puede persistir el state en Redis:
```python
from langgraph.checkpoint.redis import RedisCheckpointer
checkpointer = RedisCheckpointer(redis_url=settings.REDIS_URL)
graph = StateGraph(NutriVetState)
compiled = graph.compile(checkpointer=checkpointer)
```

## Consideraciones de Deployment

- El LangGraph orchestrator se inicializa una vez al startup del servidor (singleton).
- Cada request crea una nueva invocación del grafo con estado propio.
- No hay estado compartido entre requests en el grafo (stateless por invocación).
- El grafo compilado puede ejecutar nodos en paralelo cuando LangGraph lo permite.
