# Tech Stack Decisions — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Agent Core

### LangGraph como Orquestador
**Decisión**: `langgraph==0.1.x` para el StateGraph del agente.
**Razón**: Framework diseñado para agentes con estado compartido, nodos condicionales y subgrafos. Compatible con LangChain tools y checkpointers. Mantenido por LangChain Inc.
**Alternativas rechazadas**: LangChain chains (lineal, sin grafo), Crew.AI (orientado a múltiples agentes autónomos — no aplica), código custom (reinventar la rueda con más bugs).

### LangChain-OpenAI para ChatOpenAI via OpenRouter
**Decisión**: `langchain-openai` configurado con `base_url=https://openrouter.ai/api/v1`.
**Razón**: OpenRouter es compatible con la API de OpenAI. Usar el SDK de LangChain-OpenAI permite routing a cualquier modelo de OpenRouter sin cambiar el código del cliente.
**Configuración**:
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(
    model=resolved_model,
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)
```

### TypedDict para NutriVetState
**Decisión**: `TypedDict` de Python typing para el estado del grafo.
**Razón**: LangGraph requiere TypedDict o Pydantic BaseModel para el estado. TypedDict es más ligero y sin validación en runtime (la validación ocurre en los nodos). Compatible con el requisito de cero dependencias externas en domain.

### Redis para Checkpointer y Quota
**Decisión**: Redis para dos propósitos distintos:
1. LangGraph checkpointer (estado de sesión de larga duración)
2. Quota counters para free tier (INCR + TTL)
**Razón**: Redis ya es parte del stack (ARQ). Reutilizar el mismo servicio.

### frozenset para Keywords de Emergencia/Médica
**Decisión**: `frozenset[str]` para EMERGENCY_KEYWORDS y MEDICAL_KEYWORDS.
**Razón**: Búsqueda O(1). Inmutable en runtime. Consistente con el patrón de constantes de seguridad del domain layer.

### Dependencias del Agent Core

```
langgraph==0.1.x
langchain-core==0.1.x
langchain-openai==0.1.x
redis==5.x                # checkpointer + quota
```

### Lo que NO se usa en Agent Core

| Tecnología | Razón |
|------------|-------|
| LangChain Agents (ReAct) | El orquestador es un grafo explícito, no un agente autónomo. El flujo es determinista en los puntos críticos |
| Crew.AI | Multi-agent framework — overkill para este caso de uso |
| Vector stores / RAG | No se hace retrieval de documentos en el orquestador (puede agregarse en ConsultationSubgraph post-MVP) |
| AutoGPT / OpenAI Assistants API | Vendor lock-in + falta de control en guardarraíles de seguridad |
| Semantic Kernel | No es parte del ecosistema Python LangChain — cambio de paradigma innecesario |
