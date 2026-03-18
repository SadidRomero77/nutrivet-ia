# Plan: Infrastructure Design — Unit 07: conversation-service

**Unidad**: unit-07-conversation-service
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| ConsultationSubgraph (reemplaza stub) | `infrastructure/agent/subgraphs/consultation.py` |
| QueryClassifier node | `infrastructure/agent/nodes/query_classifier.py` |
| NutritionalResponder node | `infrastructure/agent/nodes/nutritional_responder.py` |
| FreemiumGateChecker node | `infrastructure/agent/nodes/freemium_gate.py` |
| ConversationRepository | `infrastructure/db/conversation_repository.py` |
| AgentQuotaRepository | `infrastructure/db/agent_quota_repository.py` |

**SSE**: FastAPI `StreamingResponse` con `media_type="text/event-stream"`.
No requiere API Gateway ni proxy especial — Uvicorn soporta SSE directamente (ADR-021).

**Servidor**: Hetzner CPX31 — in-process dentro del contenedor FastAPI.

### Storage — PostgreSQL

**Tabla `conversations`**:
```sql
CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID NOT NULL,   -- anónimo, sin FK explícita
    owner_id        UUID REFERENCES users(user_id),
    role            VARCHAR(10) NOT NULL,  -- user / assistant
    message         TEXT NOT NULL,
    query_type      VARCHAR(20),     -- NUTRITIONAL / MEDICAL / EMERGENCY / NULL
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_conversations_pet_id ON conversations(pet_id, created_at DESC);
```

**Tabla `agent_quotas`**:
```sql
CREATE TABLE agent_quotas (
    quota_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(user_id) UNIQUE,
    daily_count     INTEGER DEFAULT 0,
    daily_reset_at  DATE DEFAULT CURRENT_DATE,
    total_count     INTEGER DEFAULT 0,
    total_limit     INTEGER DEFAULT 9,   -- Free tier: 9 preguntas total
    daily_limit     INTEGER DEFAULT 3,   -- Free tier: 3 preguntas/día
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### Alembic Migrations

```
014_conversations.py  → tabla conversations + índice
015_agent_quotas.py   → tabla agent_quotas (UNIQUE en user_id)
```

### LLM — OpenRouter (Routing por Tier)

- El agente conversacional usa el mismo routing de tier que el plan-service.
- Modelo seleccionado por `LLMRouter.select_model(tier, conditions_count=0)`.
- El QueryClassifier puede usar un modelo más económico (llama-3.3-70b siempre).

### SSE — FastAPI StreamingResponse

```python
# presentation/routers/agent_router.py
@router.post("/v1/agent/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Chat con SSE streaming. Content-Type: text/event-stream."""
    return StreamingResponse(
        generate_response_stream(request, current_user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

async def generate_response_stream(request, user):
    """Async generator para SSE. Cada yield es un evento SSE."""
    async for token in nutritional_responder.stream(request, user):
        yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
    yield f"data: {json.dumps({'done': True, 'disclaimer': DISCLAIMER})}\n\n"
```

### Variables de Entorno Requeridas

```bash
# Heredadas — no adicionales para conversation-service
OPENROUTER_API_KEY=<clave de OpenRouter>
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrivet
FERNET_KEY=<para desencriptar condiciones médicas del PetProfile>
```

### No se Requieren Servicios Externos Adicionales

- Sin Redis: el historial y cuotas están en PostgreSQL.
- Sin WebSockets: SSE es suficiente para streaming unidireccional.
- Sin CDN: el streaming va directamente de Uvicorn al cliente.

## Notas Arquitecturales

1. **SSE vs WebSockets**: SSE elegido por simplicidad (ADR-021). El chat es
   unidireccional (server → client streaming). WebSockets agrega complejidad
   innecesaria para este caso de uso.

2. **Historial en PostgreSQL (no Redis)**: El historial de conversación persiste
   entre dispositivos — necesita ser en DB persistente, no cache.

3. **Caddy y SSE**: El reverse proxy Caddy en Hetzner debe configurarse con
   `flush_interval -1` o `flush_interval 0` para SSE. Verificar en deploy.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- Unit spec: `inception/units/unit-07-conversation-service.md`
- ADR-021: SSE streaming (sin API Gateway)
