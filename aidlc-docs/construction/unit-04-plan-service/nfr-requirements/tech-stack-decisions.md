# Tech Stack Decisions — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Plan Service

### ARQ como Job Queue (ADR-022)
**Decisión**: `arq==0.25.x` con Redis como broker.
**Razón**: Ligero, async-native (asyncio), sin overhead de Celery. Suficiente para el volumen esperado del piloto BAMPYSVET (< 100 planes/día). Coolify puede escalar el contenedor worker independientemente del API.
**Alternativas rechazadas**: Celery (síncrono por defecto, más complejo), FastAPI BackgroundTasks (no persiste si el servidor reinicia), RQ (menos features que ARQ para async Python).

### OpenRouter como Proveedor Unificado (ADR-019)
**Decisión**: OpenRouter API para todos los modelos (llama, gpt-4o-mini, claude-sonnet-4-5).
**Razón**: Un solo endpoint, una sola API key, routing entre modelos sin cambiar el cliente. Permite cambiar el modelo sin modificar el código del cliente.
**Alternativas rechazadas**: Múltiples clientes (OpenAI SDK + Anthropic SDK + Groq SDK) — complejidad operacional mayor, múltiples secrets.

### httpx para Llamadas a OpenRouter
**Decisión**: `httpx==0.27.x` async para el OpenRouterClient.
**Razón**: HTTP client async nativo, compatible con FastAPI y ARQ (asyncio). Soporte streaming para SSE (usado en conversation service).
**Alternativas rechazadas**: `aiohttp` (menos ergonómico), `requests` (síncrono, incompatible con asyncio).

### tenacity para Retry Logic
**Decisión**: `tenacity==8.x` para decorar las llamadas a OpenRouter.
**Razón**: Librería estándar de retry en Python. Exponential backoff configurable. Compatible con async.
**Alternativas rechazadas**: retry manual con `for i in range(3)` (menos robusto, no maneja jitter).

### PostgreSQL Rule para Append-Only AgentTrace
**Decisión**: `CREATE RULE no_update_agent_traces AS ON UPDATE TO agent_traces DO INSTEAD NOTHING`
**Razón**: Prevención a nivel de base de datos — incluso si hay un bug en el código, el UPDATE no ocurre. Layer adicional de seguridad sobre la garantía de código.
**Alternativas rechazadas**: Solo confiar en el código (puede tener bugs), trigger que lanza excepción (más costoso que DO INSTEAD NOTHING para auditoría silenciosa vs. ruidosa — preferir ruidosa, ver nota).
**Nota**: En producción usar trigger que lanza `EXCEPTION` (ruidoso) para detectar bugs. En esta decisión, usar `RAISE EXCEPTION 'agent_traces is append-only'`.

### Dependencias del Plan Service

```
arq==0.25.0
httpx==0.27.0
tenacity==8.2.3
redis==5.0.3             # cliente Redis para ARQ
sqlalchemy[asyncio]==2.0.28
asyncpg==0.29.0
firebase-admin==6.4.0    # FCM push notifications
pydantic==2.6.x
```

### Variables de Entorno

```env
REDIS_URL=redis://localhost:6379
OPENROUTER_API_KEY=<api_key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
FCM_CREDENTIALS_JSON=/secrets/firebase-credentials.json
ARQ_MAX_JOBS=10
PLAN_GENERATION_TIMEOUT_S=120
```
