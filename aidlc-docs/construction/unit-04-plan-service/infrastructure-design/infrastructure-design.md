# Infrastructure Design — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura del Plan Service

### OpenRouterClient

```python
# infrastructure/plans/openrouter_client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenRouterClient:
    """Cliente HTTP para OpenRouter API. Implementa retry con backoff."""

    BASE_URL = "https://openrouter.ai/api/v1"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def complete(self, model: str, messages: list[dict], timeout: int = 60) -> str:
        """Llamada a OpenRouter con retry × 3 y exponential backoff."""
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": model, "messages": messages},
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
```

### ARQ Worker Configuration

```python
# workers/plan_worker.py
from arq import cron
from arq.connections import RedisSettings

async def generate_plan_worker(ctx: dict, job_id: str) -> None:
    """Worker ARQ para generación asíncrona de planes nutricionales."""
    # Importar use case y ejecutar flujo completo
    ...

class WorkerSettings:
    functions = [generate_plan_worker]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 10
    job_timeout = 120  # segundos máximos por job
    health_check_interval = 30
```

### AgentTraceRepository (Insert-Only)

```python
# infrastructure/plans/pg_agent_trace_repository.py
class PostgreSQLAgentTraceRepository(AgentTraceRepositoryPort):
    """Repositorio de trazas de agente. INSERT only — nunca UPDATE."""

    async def insert(self, trace: AgentTrace) -> None:
        """Insertar traza. Único método disponible."""
        model = AgentTraceModel(
            trace_id=trace.trace_id,
            plan_id=trace.plan_id,
            pet_id=trace.pet_id,  # UUID anónimo
            llm_model=trace.llm_model,
            prompt_tokens=trace.prompt_tokens,
            completion_tokens=trace.completion_tokens,
            latency_ms=trace.latency_ms,
            node_name=trace.node_name,
        )
        self._session.add(model)
        await self._session.flush()

    # NO existe update(), delete(), ni ningún método de modificación
```

### Push Notifications (FCM via Firebase)

```python
# infrastructure/notifications/fcm_client.py
class FCMClient:
    """Notificaciones push via Firebase Cloud Messaging."""

    async def send_plan_ready(self, fcm_token: str, plan_id: UUID) -> None:
        """Notificar al owner que su plan está listo."""
        ...

    async def send_plan_approved(self, fcm_token: str, plan_id: UUID) -> None:
        """Notificar al owner que el vet aprobó el plan."""
        ...
```

## Dependencias del Plan Service

```
arq==0.25.x              # Queue worker Redis
httpx==0.27.x            # HTTP client async para OpenRouter
tenacity==8.x            # Retry logic
redis==5.x               # Redis client para ARQ
firebase-admin==6.x      # FCM push notifications (opcional, puede ser httpx directo)
sqlalchemy[asyncio]==2.0.x
```

## Flujo de Datos en la Generación

```
FastAPI handler
    → PlanJob INSERT (PostgreSQL)
    → ARQ enqueue (Redis)
    ↓ [async]
ARQ Worker
    → NRCCalculator (domain, Python puro)
    → LLMRouter (domain, Python puro)
    → OpenRouterClient.complete() (httpx → OpenRouter API)
    → AgentTrace INSERT (PostgreSQL)
    → FoodSafetyChecker (domain)
    → MedicalRestrictionEngine (domain)
    → NutritionPlan INSERT (PostgreSQL)
    → FCM push notification
```
