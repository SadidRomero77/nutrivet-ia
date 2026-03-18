# Infrastructure Design — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura

### OpenRouterStreamingClient

```python
# infrastructure/conversation/openrouter_streaming_client.py
import httpx

class OpenRouterStreamingClient:
    """Cliente httpx async para streaming SSE desde OpenRouter."""

    async def stream_complete(
        self, model: str, messages: list[dict], timeout: int = 60
    ) -> AsyncIterator[str]:
        """Stream chunks de respuesta del LLM via SSE."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": model, "messages": messages, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        data = json.loads(line[6:])
                        chunk = data["choices"][0]["delta"].get("content", "")
                        if chunk:
                            yield chunk
```

### FastAPI SSE Endpoint

```python
# presentation/agent/agent_router.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

@router.post("/agent/chat")
async def agent_chat(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user)
) -> StreamingResponse:
    """Endpoint SSE para el agente conversacional."""

    async def event_generator():
        async for chunk in conversation_use_case.stream_response(
            pet_id=request.pet_id,
            owner_id=current_user.user_id,
            message=request.message,
            tier=current_user.tier,
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # desactivar buffering de Nginx/Traefik
        }
    )
```

### RedisQuotaClient

```python
# infrastructure/conversation/redis_quota_client.py
import redis.asyncio as aioredis
from datetime import date

class RedisQuotaClient:
    """Gestión de quota con Redis INCR atómico."""

    async def increment_quota(self, pet_id: UUID) -> int:
        """Incrementar uso de quota y retornar el nuevo valor. Thread-safe."""
        today = date.today().isoformat()
        key = f"quota:{pet_id}:{today}"
        count = await self._redis.incr(key)
        await self._redis.expire(key, 86400)  # TTL 24h
        # Registrar día de uso para tracking de días
        await self._redis.sadd(f"quota:days:{pet_id}", today)
        return count

    async def get_quota(self, pet_id: UUID) -> tuple[int, int]:
        """Retornar (questions_used_today, total_days_used)."""
        today = date.today().isoformat()
        questions_today = int(await self._redis.get(f"quota:{pet_id}:{today}") or 0)
        days_used = await self._redis.scard(f"quota:days:{pet_id}")
        return questions_today, days_used
```

## Dependencias del Conversation Service

```
httpx==0.27.x       # streaming client
redis==5.x          # quota counters async
sqlalchemy[asyncio]==2.0.x
fastapi==0.110.x
```
