# NFR Design Patterns — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Conversation Service

### Patrón 1: SSE con FastAPI StreamingResponse
FastAPI soporta SSE nativamente con `StreamingResponse` y `async generators`.
```python
return StreamingResponse(event_generator(), media_type="text/event-stream")
```
- No requiere WebSocket (más simple para el caso de uso unidireccional).
- Flutter usa `http` o `dio` con stream para consumir SSE.
- Traefik/Nginx debe tener buffering desactivado: `X-Accel-Buffering: no`.

### Patrón 2: Atomic Quota con Redis INCR
El incremento de quota es atómico con `REDIS INCR`.
- Múltiples requests concurrentes del mismo usuario no causan race conditions.
- El TTL automático en Redis resetea el contador a medianoche.
- No requiere locks ni transacciones de BD para el caso común.

### Patrón 3: Gate-First (Fail Fast para Quota)
La verificación de quota es el primer paso del use case.
- Si quota agotada → respuesta inmediata sin cargar contexto ni llamar LLM.
- Ahorra latencia y tokens en el caso de quota excedida.

### Patrón 4: Persist-After-Stream (No Durante)
Los mensajes se persisten en PostgreSQL DESPUÉS de que el stream completa, no durante.
- Si el stream se interrumpe (cliente desconectado) → el mensaje NO se persiste.
- Evita mensajes parciales en el historial.
- La quota se incrementa solo si el mensaje fue respondido completamente.

### Patrón 5: Context Window Limitado (Últimas 10 Conversaciones)
El historial enviado al LLM es las últimas 10 conversaciones del pet_id.
- Previene context overflow (tokens límite del modelo).
- Las conversaciones más antiguas caen fuera del contexto pero permanecen en PostgreSQL.
- Post-MVP: embedding + retrieval para contexto más relevante (RAG).

### Patrón 6: Discriminación de Quota por Tipo de Respuesta
Solo las respuestas nutricionales (LLM) consumen quota:
```python
if intent == IntentType.NUTRITIONAL_QUERY:
    await quota_client.increment_quota(pet_id)
    # Las respuestas de referral o emergencia NO incrementan
```
- Principio de equidad: el free tier solo se consume por el servicio de valor.

### Patrón 7: Desacoplamiento de Quota en Redis vs. PostgreSQL
- Redis: quota del DÍA ACTUAL (fast, TTL automático).
- PostgreSQL: histórico de uso para calcular "días usados" (durable, auditable).
- Evita consultar PostgreSQL en el hot path del streaming.
- En caso de pérdida de Redis → reconstruir del PostgreSQL (eventual consistency aceptable).
