# Tech Stack Decisions — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Conversation Service

### FastAPI StreamingResponse para SSE
**Decisión**: `FastAPI.StreamingResponse` con `media_type="text/event-stream"`.
**Razón**: SSE es el mecanismo más simple para streaming unidireccional server→client. No requiere WebSocket (bidireccional — innecesario para este caso). FastAPI soporta generators async nativas.
**Alternativas rechazadas**: WebSocket (más complejo, estado bidireccional innecesario), Long polling (latencia mayor, más requests), HTTP/2 Server Push (soporte limitado en clientes móviles Flutter).

### httpx async para Streaming de OpenRouter
**Decisión**: `httpx.AsyncClient` con `client.stream()` para consumir el stream de OpenRouter.
**Razón**: httpx es el cliente HTTP async más maduro en Python. El método `stream()` maneja chunked transfer encoding y SSE natively. Ya es dependencia del proyecto (OpenRouterClient en plan service).
**Alternativas rechazadas**: `aiohttp` (diferente API, inconsistencia en el proyecto), `requests` (síncrono, bloquea).

### Redis INCR para Quota (Atomic)
**Decisión**: `REDIS INCR` para incrementos atómicos de quota diaria.
**Razón**: INCR es atómico en Redis — no hay race conditions con múltiples requests concurrentes. TTL automático resetea el contador sin job de limpieza.
**Alternativas rechazadas**: PostgreSQL UPDATE + SELECT (más lento, requiere transacción), contador en memoria (no persiste entre reinicios).

### SADD + SCARD para Días Usados
**Decisión**: Redis SADD `{YYYY-MM-DD}` para tracking de días con uso, SCARD para contar.
**Razón**: Evitar duplicados automáticamente (set). O(1) para membership check y count.
**Persistencia dual**: Redis para velocidad + PostgreSQL `agent_quotas` para durabilidad.

### LLM Routing Igual que Plan Service
**Decisión**: El modelo del agente conversacional sigue el mismo routing que el plan service (LLMRouter del domain).
**Razón**: Consistencia de experiencia. Un usuario premium siempre usa claude-sonnet-4-5, tanto en planes como en conversaciones. Override clínico de 3+ condiciones aplica también en chat.

### Dependencias del Conversation Service

```
httpx==0.27.x        # streaming client
redis==5.x           # quota async
sqlalchemy[asyncio]  # persistence
fastapi==0.110.x
```

### Consideraciones de Escalado

- Uvicorn async handles múltiples streams concurrentes sin threads.
- Cada conexión SSE mantiene un generator async abierto durante el stream.
- En CPX31 con 2 workers: capacidad estimada 50-100 streams concurrentes.
- Si se supera capacidad: escalar workers o agregar réplica del contenedor.
- Los streams son stateless en el servidor (el estado está en el generator, no en el worker).
