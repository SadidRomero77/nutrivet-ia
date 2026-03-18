# Plan: NFR Design — Unit 07: conversation-service

**Unidad**: unit-07-conversation-service
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a conversation-service

### Patrón: SSE Streaming (FastAPI async generator)

**Contexto**: El usuario debe ver los tokens aparecer progresivamente (< 1s primer token).
SSE es la tecnología más simple para streaming unidireccional server → client.

**Diseño**:
```python
# infrastructure/agent/nodes/nutritional_responder.py
async def stream_response(
    messages: list[dict],
    model: str,
    openrouter_client: OpenRouterClient
) -> AsyncGenerator[str, None]:
    """Genera tokens via SSE. Cada yield envía un token al cliente."""
    async for chunk in openrouter_client.stream(messages, model):
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# presentation/routers/agent_router.py
async def sse_generator(tokens: AsyncGenerator) -> AsyncGenerator[str, None]:
    """Formatea tokens como eventos SSE."""
    async for token in tokens:
        yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
    yield f"data: {json.dumps({'done': True, 'disclaimer': DISCLAIMER_TEXT})}\n\n"
```

### Patrón: Quota-First (Verificar cuota ANTES de llamar al LLM)

**Contexto**: No desperdiciar cuota del LLM si el usuario ya agotó su límite.
Las emergencias siempre pasan — nunca bloquear una emergencia.

**Diseño**:
```python
# infrastructure/agent/nodes/freemium_gate.py
async def freemium_gate(state: NutriVetState) -> NutriVetState:
    """Verifica cuota ANTES de LLM. Emergencias pasan siempre."""
    if state["intent"] == "emergency":
        return state  # Bypass incondicional

    if state["subscription_tier"] != "free":
        return state  # Tier pagado — sin límite

    quota = await quota_repo.get_or_create(state["user_id"])

    # Reset diario
    if quota.daily_reset_at < date.today():
        await quota_repo.reset_daily(state["user_id"])
        quota = await quota_repo.get(state["user_id"])

    if quota.daily_count >= quota.daily_limit:
        return {**state, "quota_exceeded": "daily", "intent": "upgrade_gate"}

    if quota.total_count >= quota.total_limit:
        return {**state, "quota_exceeded": "total", "intent": "upgrade_gate"}

    # Decrementar ANTES del LLM (no después)
    await quota_repo.increment(state["user_id"])
    return state
```

**Atomicidad**:
```sql
-- Incremento atómico para evitar race conditions
UPDATE agent_quotas
SET daily_count = daily_count + 1,
    total_count = total_count + 1,
    updated_at = NOW()
WHERE user_id = $1
  AND daily_count < daily_limit
  AND total_count < total_limit
RETURNING daily_count, total_count;
-- Si 0 filas afectadas → cuota agotada
```

### Patrón: Context-Window (Historial como contexto LLM)

**Contexto**: El agente necesita contexto de conversaciones anteriores para respuestas coherentes.

**Diseño**:
```python
# application/use_cases/conversation_use_case.py
async def build_conversation_context(pet_id: UUID, pet_profile: dict) -> list[dict]:
    """Construye contexto LLM con system prompt + últimos 10 mensajes."""
    history = await conversation_repo.get_recent(pet_id, limit=10)

    messages = [
        {"role": "system", "content": build_system_prompt(pet_profile)},
        *[{"role": m.role, "content": m.message} for m in history]
    ]
    return messages

def build_system_prompt(pet_profile: dict) -> str:
    """System prompt contextualizado con datos del pet."""
    return f"""Eres el asistente nutricional de {pet_profile['name']},
un {pet_profile['species']} de raza {pet_profile['breed']}.
Plan activo: {pet_profile.get('plan_summary', 'Sin plan activo')}.
Alergias: {', '.join(pet_profile.get('allergies', [])) or 'Ninguna conocida'}.
IMPORTANTE: Responde SOLO consultas nutricionales. Para consultas médicas, remite al vet."""
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `nodes/query_classifier.py` | 90% | Unit tests — G3 test set 100 casos |
| `nodes/freemium_gate.py` | 100% | Unit tests — cuota + emergencias |
| `nodes/nutritional_responder.py` | 80% | Integration tests con mock SSE |
| `subgraphs/consultation.py` | 80% | Integration tests |
| `infrastructure/db/agent_quota_repository.py` | 90% | Unit tests — atomicidad |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- ADR-021: SSE streaming
- Constitution: REGLA 8 (disclaimer), REGLA 9 (límite nutricional/médico)
- Quality Gates: G3
