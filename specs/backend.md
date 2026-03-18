# BACKEND-SPEC.md — NutriVet.IA Backend v2
> Documento completo para implementación del backend sin preguntas adicionales.
> Stack: Python 3.12 + FastAPI + LangGraph + PostgreSQL + Hetzner CPX31 + Coolify (ver ADR-022)
> Basado en estándares NRC/AAFCO y validación clínica veterinaria.

---

## Estructura de carpetas COMPLETA

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          ← FastAPI app (Uvicorn — sin Mangum)
│   ├── config.py                        ← Settings con pydantic-settings
│   │
│   ├── domain/                          ← Sin dependencias externas
│   │   ├── user/
│   │   │   ├── entities.py              ← User, UserProfile
│   │   │   └── value_objects.py         ← UserRole (owner/vet/admin)
│   │   ├── pet/
│   │   │   ├── entities.py              ← Pet, Breed
│   │   │   └── value_objects.py         ← Species, Size, ActivityLevel,
│   │   │                                   ReproductiveStatus, BodyConditionScore
│   │   ├── nutrition/
│   │   │   ├── entities.py              ← NutritionPlan, NutritionalRequirements
│   │   │   ├── value_objects.py         ← PlanStatus, Macros, MealItem, DietModality
│   │   │   ├── kcal_calculator.py       ← RER/DER — DETERMINISTA, sin LLM
│   │   │   └── toxicity_db.py           ← ToxicityDatabase (hard-coded)
│   │   ├── food/
│   │   │   ├── entities.py              ← Food, FoodCategory
│   │   │   ├── value_objects.py         ← ToxicityLevel, NutritionalValues
│   │   │   ├── allergy_db.py            ← AllergenReference (hard-coded)
│   │   │   └── restrictions_db.py       ← Restricciones por condición médica
│   │   └── sponsor/
│   │       └── entities.py              ← Sponsor, SponsorProfile
│   │
│   ├── application/
│   │   └── use_cases/
│   │       ├── register_user.py         ← RegisterUserUseCase
│   │       ├── create_pet.py            ← CreatePetUseCase
│   │       ├── update_pet.py            ← UpdatePetUseCase
│   │       ├── add_medical_condition.py ← AddMedicalConditionUseCase
│   │       ├── calculate_kcal.py        ← CalculateKcalUseCase (determinista)
│   │       ├── select_modality.py       ← SelectDietModalityUseCase
│   │       ├── generate_natural_plan.py ← GenerateNaturalPlanUseCase (Tipo A)
│   │       ├── generate_concentrate.py  ← GenerateConcentrateProfileUseCase (Tipo B)
│   │       ├── validate_toxicity.py     ← ValidateToxicityUseCase
│   │       ├── scan_label.py            ← ScanLabelUseCase (solo tabla + ingredientes)
│   │       ├── update_plan.py           ← UpdatePlanUseCase
│   │       └── sign_plan.py             ← SignPlanUseCase (solo rol: vet)
│   │
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── connection.py
│   │   │   ├── models.py                ← ORM models
│   │   │   └── repositories/
│   │   │       ├── user_repository.py
│   │   │       ├── pet_repository.py
│   │   │       ├── plan_repository.py
│   │   │       ├── food_repository.py
│   │   │       └── sponsor_repository.py
│   │   ├── llm/
│   │   │   ├── openai_client.py
│   │   │   ├── agent/
│   │   │   │   ├── graph.py             ← LangGraph StateGraph
│   │   │   │   ├── state.py             ← AgentState TypedDict
│   │   │   │   ├── nodes.py
│   │   │   │   └── tools/
│   │   │   │       ├── nutrition_calculator.py
│   │   │   │       ├── food_toxicity_checker.py
│   │   │   │       ├── plan_generator.py       ← Tipo A y Tipo B
│   │   │   │       ├── product_scanner.py      ← Solo tabla + ingredientes
│   │   │   │       └── concentrate_advisor.py  ← Perfil + sponsors
│   │   │   └── prompts/
│   │   │       ├── plan_generation.py
│   │   │       ├── concentrate_profile.py
│   │   │       └── label_analysis.py
│   │   ├── storage/
│   │   │   └── s3_client.py
│   │   └── observability/
│   │       ├── logging.py
│   │       └── metrics.py
│   │
│   └── presentation/
│       ├── api/v1/
│       │   ├── auth.py           ← register, login, refresh, logout
│       │   ├── users.py          ← perfil del usuario
│       │   ├── pets.py           ← CRUD mascotas + condiciones médicas + alergias
│       │   ├── plans.py          ← modalidad, generar, ajustar, firmar
│       │   ├── foods.py          ← búsqueda, toxicidad, alérgenos
│       │   ├── scanner.py        ← OCR solo tabla nutricional + ingredientes
│       │   └── concentrates.py   ← recomendaciones + sponsors
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── users.py
│       │   ├── pets.py
│       │   ├── plans.py
│       │   ├── foods.py
│       │   ├── scanner.py
│       │   └── concentrates.py
│       └── middleware/
│           ├── auth.py
│           ├── rbac.py
│           ├── logging.py
│           └── cors.py
│
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   │   ├── test_kcal_calculator.py    ← 100% requerido — RER/DER
│   │   │   ├── test_toxicity_db.py        ← 100% requerido
│   │   │   ├── test_restrictions_db.py    ← 100% requerido
│   │   │   └── test_allergy_logic.py
│   │   └── use_cases/
│   │       ├── test_create_pet.py
│   │       ├── test_generate_plan.py
│   │       └── test_sign_plan.py
│   ├── integration/
│   │   ├── test_auth_api.py
│   │   ├── test_pets_api.py
│   │   └── test_plans_api.py
│   └── evals/
│       ├── test_plan_natural_generation.py
│       ├── test_concentrate_profile.py
│       ├── test_toxicity_block.py         ← 100% pass requerido
│       ├── test_vet_escalation.py         ← 100% pass requerido
│       ├── test_allergy_unknown_alert.py  ← 100% pass requerido
│       └── golden_set/
│           ├── plan_natural.json
│           ├── plan_concentrate.json
│           ├── toxicity_block.json
│           └── vet_escalation.json
│
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 001_initial_schema.py
│
├── scripts/
│   ├── seed_toxicity_db.py
│   ├── seed_allergen_reference.py
│   └── seed_foods.py
│
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Endpoints API completos

### Auth
```
POST /api/v1/auth/register
  Body: { full_name, email, password, city, country }
  Returns: { user_id, message: "Verifica tu correo electrónico" }

POST /api/v1/auth/verify-email
  Body: { token }
  Returns: { message }

POST /api/v1/auth/login
  Body: { email, password }
  Returns: { access_token, refresh_token, token_type, user: { id, full_name, role } }

POST /api/v1/auth/refresh
  Body: { refresh_token }
  Returns: { access_token }

POST /api/v1/auth/logout
  Headers: Authorization: Bearer <token>
  Returns: { message }
```

### Usuarios
```
GET  /api/v1/users/me
  Returns: { id, full_name, email, city, country, role }

PUT  /api/v1/users/me
  Body: { full_name?, city?, country? }
```

### Mascotas
```
POST /api/v1/pets
  Roles: owner
  Body:
    name, species (dog|cat), breed, sex (male|female),
    age_years, weight_kg,
    size (mini|small|medium|large|giant),
    reproductive_status (sterilized|intact|unknown),
    activity_level,           ← dog: none|low|moderate|high|very_high
                                 cat: indoor|outdoor
    body_condition_score,     ← 1-9
    physiological_state?      ← normal|pregnant|lactating|puppy|senior|geriatric

GET  /api/v1/pets
  Roles: owner (sus mascotas), vet (pacientes asignados)

GET  /api/v1/pets/{pet_id}
GET  /api/v1/pets/{pet_id}/history        ← historial de planes

PUT  /api/v1/pets/{pet_id}
  Roles: owner (su mascota)

DELETE /api/v1/pets/{pet_id}              ← soft delete (is_active = false)

POST /api/v1/pets/{pet_id}/conditions
  Roles: owner o vet
  Body:
    condition_code,           ← diabetic|hypothyroid|cancer|articular|renal|
                                 hepatic|pancreatic|neurodegenerative|dental|
                                 skin|gastric|cardiac|food_allergy
    cancer_location?,         ← OBLIGATORIO si condition_code = 'cancer'
    severity?,
    notes?,
    diagnosed_date?
  Returns: { condition_id, dietary_restrictions_applied }

POST /api/v1/pets/{pet_id}/allergies
  Roles: owner
  Body:
    allergens: [
      { allergen_code, confirmed? }
      |
      { unknown: true }        ← "No sabe" → genera alerta + requiere aceptación
    ]
  Returns:
    Si unknown = true:
      { requires_confirmation: true,
        alert: "Se recomienda realizar un test de alérgenos...",
        disclaimer: "Si continúas, el plan se generará bajo tu responsabilidad." }
    Si confirmado:
      { allergies_registered: [...] }

POST /api/v1/pets/{pet_id}/allergies/accept-risk
  Roles: owner
  Body: { accepted: true }
  Returns: { owner_accepted_risk: true }

GET  /api/v1/foods/allergens?species={dog|cat}
  Returns: lista de alérgenos comunes del catálogo
```

### Planes
```
POST /api/v1/plans/modality
  Roles: owner
  Body: { pet_id, modality: "natural" | "concentrate" }
  Returns: { modality_confirmed, next_step: "/api/v1/plans" }

POST /api/v1/plans
  Roles: owner
  Body: { pet_id, preferences? }
  Process:
    1. Calcular RER/DER (determinista)
    2. Aplicar restricciones por condición médica
    3. Si unknown_allergy y no aceptó riesgo → 400 error
    4. Generar plan Tipo A o Tipo B según modality
    5. Validar toxicidad (hard-coded)
    6. Si tiene condición médica → status = PENDING_VET
    7. Si no → status = DRAFT (puede activar owner)
  Returns: { plan_id, status, modality, content, nutritional_requirements, disclaimer }

GET  /api/v1/plans/{plan_id}
GET  /api/v1/plans/pet/{pet_id}            ← planes de una mascota

PUT  /api/v1/plans/{plan_id}/adjust
  Roles: owner
  Body: { changes_requested }
  Returns: { plan_id, status }              ← vuelve a PENDING_VET si hay condición médica

POST /api/v1/plans/{plan_id}/sign
  Roles: vet ONLY
  Body: { professional_card, notes? }
  Returns: { plan_id, status: "ACTIVE", signature }

POST /api/v1/plans/{plan_id}/reject
  Roles: vet ONLY
  Body: { rejection_notes }
  Returns: { plan_id, status: "REJECTED" }

GET  /api/v1/plans/{plan_id}/trace
  Roles: vet, admin
  Returns: historial completo de cambios y trazabilidad
```

### Scanner OCR
```
POST /api/v1/scanner/label
  Roles: owner
  Body: { image_base64, image_format, pet_id,
          image_type: "nutritional_table" | "ingredients_list" }
  Validación:
    - Solo se acepta nutritional_table o ingredients_list
    - NO se procesa imagen con marca/logo
    - GPT-4o Vision extrae valores
    - Se evalúan contra perfil del paciente
  Returns:
    { adequacy: "adequate|caution|not_recommended",
      extracted_values: { protein_pct, fat_pct, carbs_pct, fiber_pct,
                          phosphorus_mg, sodium_mg, ingredients_ordered },
      concerns: [...],
      positives: [...],
      recommendation: "...",
      disclaimer: "..." }
```

### Concentrados y Sponsors
```
GET  /api/v1/concentrates/profile/{pet_id}
  Roles: owner
  Returns: perfil nutricional ideal para la mascota (sin marcas si no hay sponsor)

GET  /api/v1/concentrates/sponsored/{pet_id}
  Roles: owner
  Returns: sponsors verificados que coinciden con el perfil (máx 3, tag "Patrocinado")

POST /api/v1/admin/sponsors
  Roles: admin ONLY
  Body: { brand_name, nutritional_profile, suitable_conditions,
          contraindicated_conditions, verified_by_vet_id, disclosure_text }

PUT  /api/v1/admin/sponsors/{sponsor_id}/activate
  Roles: admin ONLY
  Requiere: verified_by_vet_id ya asignado

GET  /api/v1/admin/sponsors
  Roles: admin ONLY
```

### Alimentos
```
GET  /api/v1/foods/search?q={query}&species={dog|cat}
POST /api/v1/foods/toxicity
  Body: { food_name, species }
  Returns: { is_safe, risk_level, reason, alternatives }
GET  /api/v1/foods/allergens?species={dog|cat}
```

---

## Lógica de Cálculo de Kcal (Determinista)

```python
# app/domain/nutrition/kcal_calculator.py

def calculate_rer(weight_kg: float) -> float:
    """Requerimiento Energético en Reposo (NRC).
    Ejemplo: Sally 9.6 kg → RER = 70 × 9.6^0.75 ≈ 404 kcal
    """
    return 70 * (weight_kg ** 0.75)

FACTOR_TABLE: dict[tuple, float] = {
    # (especie, estado_reproductivo, actividad)
    ("dog", "sterilized", "none"):      1.2,
    ("dog", "sterilized", "low"):       1.4,
    ("dog", "sterilized", "moderate"):  1.6,
    ("dog", "sterilized", "high"):      1.8,
    ("dog", "intact",     "none"):      1.4,
    ("dog", "intact",     "low"):       1.6,
    ("dog", "intact",     "moderate"):  1.8,
    ("dog", "intact",     "high"):      2.0,
    ("dog", "any",        "very_high"): 2.5,
    ("cat", "sterilized", "indoor"):    1.2,
    ("cat", "sterilized", "outdoor"):   1.4,
    ("cat", "intact",     "indoor"):    1.4,
    ("cat", "intact",     "outdoor"):   1.6,
}

BCS_ADJUSTMENTS: dict[int, float] = {
    1: 1.30, 2: 1.20, 3: 1.10,   # Bajo peso → aumentar calorías
    4: 1.00, 5: 1.00,              # Ideal
    6: 0.90, 7: 0.80,              # Sobrepeso → reducir
    8: 0.70, 9: 0.60,              # Obesidad
}

AGE_ADJUSTMENTS = {
    "senior":    0.85,    # >7 años (perro) / >10 años (gato)
    "geriatric": 0.75,    # >10 años (perro) / >15 años (gato)
    "puppy_4":   3.0,     # < 4 meses
    "puppy_12":  2.0,     # 4-12 meses
}

CONDITION_ADJUSTMENTS = {
    "diabetic":   0.90,   # Control metabólico
    "hepatic":    1.00,   # Mantener peso, no engordar
    "renal":      0.95,
    "pancreatic": 0.80,   # Restricción severa de grasa
}
```

---

## pyproject.toml

```toml
[tool.poetry]
name = "nutrivet-backend"
version = "0.2.0"
python = "^3.12"

[tool.poetry.dependencies]
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.32"}
mangum = "^0.19"
pydantic = "^2.9"
pydantic-settings = "^2.6"
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}
asyncpg = "^0.30"
alembic = "^1.14"
langgraph = "^0.2"
langchain-openai = "^0.2"
openai = "^1.54"
boto3 = "^1.35"
structlog = "^24.4"
cryptography = "^43.0"
python-jose = {extras = ["cryptography"], version = "^3.3"}
passlib = {extras = ["bcrypt"], version = "^1.7"}
httpx = "^0.27"
python-multipart = "^0.0.12"   # Para upload de imágenes OCR

[tool.poetry.group.dev.dependencies]
pytest = "^8.3"
pytest-asyncio = "^0.24"
pytest-cov = "^6.0"
ruff = "^0.8"
bandit = "^1.8"
safety = "^3.2"
mypy = "^1.13"
httpx = "^0.27"
factory-boy = "^3.3"

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"

[tool.mypy]
python_version = "3.12"
strict = true
```

---

## Variables de entorno (.env.example)

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nutrivet

# JWT
SECRET_KEY=cambia-esto-por-al-menos-32-caracteres-aleatorios
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_VISION_MODEL=gpt-4o

# Cloudflare R2 (S3-compatible storage)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=nutrivet-storage-dev
R2_ENDPOINT_URL=https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com

# Redis (ARQ job queue + caché)
REDIS_URL=redis://redis:6379/0

# Email (para verificación de cuenta)
EMAIL_PROVIDER=sendgrid        # sendgrid | ses
EMAIL_API_KEY=SG....
EMAIL_FROM=no-reply@nutrivetia.com

# Cifrado de datos médicos
MEDICAL_DATA_ENCRYPTION_KEY=clave-de-32-bytes-base64

# App
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Feature flags
FEATURE_SCAN_ENABLED=true
FEATURE_SPONSORS_ENABLED=false    # activar cuando haya sponsors verificados
```

---

## Reglas de implementación

1. **Siempre TDD** — test primero, código después
2. **Type hints obligatorios** en todas las funciones públicas
3. **Docstrings en español** en clases y métodos públicos
4. **Nunca lógica de negocio** en routers FastAPI — todo en use cases
5. **Nunca cálculos nutricionales** en LLM — solo en domain layer
6. **Siempre Pydantic** para validar inputs de endpoints
7. **Siempre RBAC** verificado en middleware, nunca en el endpoint
8. **Nunca secrets** en código — solo `settings.X` via `config.py`
9. **Logs con structlog**, campos específicos, sin objetos completos, sin PII
10. **OCR**: rechazar imágenes que no sean tabla nutricional o ingredientes
11. **Sponsors**: nunca mostrar si no coincide con perfil del paciente
12. **Disclaimer**: incluir en todo output de plan — no opcional

---

## Diseño API-First

> El contrato API (OpenAPI 3.1) es la fuente de verdad. Se genera automáticamente
> desde FastAPI y está disponible para el equipo de mobile antes de implementar.

### OpenAPI y Documentación

```python
# app/main.py
app = FastAPI(
    title="NutriVet.IA API",
    version="1.0.0",
    description="API de nutrición veterinaria personalizada con IA",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    openapi_url="/openapi.json" if settings.environment != "production" else None,
)
```

- En **desarrollo**: Swagger UI en `/docs`, ReDoc en `/redoc`
- En **producción**: documentación deshabilitada (seguridad), exportar OpenAPI en CI/CD
- El spec `openapi.json` se publica como artefacto en cada PR para revisión

### Estrategia de Versionado de API

- URL-based versioning: `/api/v1/`, `/api/v2/`
- Nueva versión **solo** si hay breaking change (campo renombrado, tipo cambiado, endpoint eliminado)
- Versión anterior soportada por mínimo **6 meses** tras deprecación
- Endpoints deprecados incluyen headers: `Deprecation: true` + `Sunset: 2026-09-01`
- Compatibilidad hacia atrás: agregar campos opcionales nunca rompe la versión

### Envelope de Respuesta Estándar

Todas las respuestas siguen el mismo formato sin excepción:

```python
# app/presentation/schemas/common.py
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    """Envelope estándar para todas las respuestas de la API."""
    success: bool
    data: Optional[T] = None
    error: Optional["ErrorDetail"] = None
    meta: Optional["ResponseMeta"] = None
    request_id: str  # Correlation ID — trazabilidad distribuida

class ErrorDetail(BaseModel):
    code: str         # NV-AUTH-001, NV-PLAN-002, NV-TOXICITY-001
    message: str      # En español, para mostrar al usuario
    field: Optional[str] = None  # Para errores de validación de campo

class ResponseMeta(BaseModel):
    page: Optional[int] = None
    per_page: Optional[int] = None
    total: Optional[int] = None
    has_next: bool = False
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "data": { "plan_id": "uuid", "status": "PENDING_VET" },
  "meta": null,
  "request_id": "req-abc123"
}
```

**Error de negocio:**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "NV-PLAN-TOXICITY-001",
    "message": "El plan contiene un ingrediente tóxico para perros: uvas",
    "field": null
  },
  "request_id": "req-abc123"
}
```

**Catálogo de códigos de error:**
```
NV-AUTH-001   Token inválido o expirado
NV-AUTH-002   Email no verificado
NV-AUTH-003   Credenciales incorrectas
NV-RBAC-001   Rol insuficiente para esta operación
NV-PET-001    Mascota no encontrada
NV-PET-002    Límite de mascotas del tier alcanzado
NV-PLAN-001   Plan no encontrado
NV-PLAN-002   Plan ya tiene condición médica — requiere vet
NV-PLAN-003   Idempotency-Key duplicada — plan ya creado
NV-TOXICITY-001   Ingrediente tóxico detectado
NV-ALLERGY-001    Riesgo de alergia no confirmado
NV-OCR-001    Tipo de imagen no permitido
NV-OCR-002    Confianza del OCR muy baja
NV-LLM-001    Proveedor LLM no disponible (circuit open)
NV-JOB-001    Job no encontrado
```

### Correlation ID (Request Tracing)

```python
# app/presentation/middleware/correlation.py
import uuid
from fastapi import Request

async def correlation_id_middleware(request: Request, call_next):
    """Agrega X-Request-ID a cada solicitud para trazabilidad distribuida."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

El `request_id` se incluye en:
- Header de respuesta `X-Request-ID`
- Todos los logs structlog: `log.bind(request_id=request.state.request_id)`
- Tabla `agent_traces.trace_id` cuando hay operación LLM
- Envelope de respuesta JSON

### Idempotencia para Operaciones Críticas

`POST /api/v1/plans` acepta `Idempotency-Key` header:

```
POST /api/v1/plans
Headers:
  Idempotency-Key: <client-generated-uuid>
```

- Si se recibe la misma key dentro de **24h** → retorna el resultado anterior sin crear duplicado
- Guardado en tabla `idempotency_keys(key, response_body, expires_at)`
- Solo aplica a endpoints de creación (`POST /plans`, `POST /pets`)

---

## Endpoints Adicionales: Salud y Observabilidad

```
GET /health   → { status: "ok", timestamp }  — liveness probe (siempre 200)
GET /ready    → { status: "ok", db: "ok" }   — readiness probe (check dependencias)
```

```python
# app/presentation/api/v1/health.py

@router.get("/health")
async def health() -> dict:
    """Liveness probe — responde si el proceso está vivo."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)) -> dict:
    """Readiness probe — verifica conexión a DB antes de recibir tráfico."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    overall = "ok" if db_status == "ok" else "degraded"
    return {"status": overall, "db": db_status}
```

---

## Patrones de Resiliencia

### Circuit Breaker y Retry para LLM

Los proveedores LLM pueden fallar, exceder rate limits o tener latencias altas.
Se implementa retry con backoff exponencial usando `tenacity`:

```python
# app/infrastructure/llm/resilience.py
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type
)
from openai import RateLimitError, APITimeoutError, APIConnectionError

def llm_retry(func):
    """Retry con backoff exponencial para llamadas a LLM externos."""
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        reraise=True
    )
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper
```

**Cadena de fallback por proveedor:**
```
0 condiciones médicas:
  Ollama Qwen2.5-7B → timeout → Groq Llama-8B → error → 503 con mensaje claro

1-2 condiciones:
  Groq Llama-70B → rate limit → GPT-4o → timeout → 503

3+ condiciones:
  GPT-4o → timeout (3 reintentos) → 503 con mensaje "Servicio temporalmente no disponible"

OCR (siempre Ollama):
  Qwen2.5-VL-7B → timeout → Groq vision (si disponible) → 503
```

### Timeouts por Operación

```python
# app/infrastructure/llm/timeouts.py
OPERATION_TIMEOUTS_SECONDS: dict[str, float] = {
    "plan_generation_simple":   30.0,   # 0 condiciones, Ollama local
    "plan_generation_moderate": 60.0,   # 1-2 condiciones, Groq
    "plan_generation_complex":  120.0,  # 3+ condiciones, GPT-4o
    "ocr_scan":                 20.0,   # Qwen2.5-VL
    "toxicity_check":           0.05,   # determinista — microsegundos
    "kcal_calculation":         0.01,   # determinista — microsegundos
    "db_query":                 5.0,
    "s3_upload":                15.0,
}
```

---

## Arquitectura de Jobs Asíncronos (Plan Generation)

La generación de planes toma 20-120 segundos con LLM. Para evitar timeouts HTTP
y proveer mejor UX (spinner progresivo en app), se implementa patrón job asíncrono:

### Flujo

```
[1] POST /api/v1/plans
    → Valida input (Pydantic)
    → Calcula RER/DER determinista (<50ms)
    → Verifica toxicidad hard-coded (<5ms)
    → Guarda plan en DB con status DRAFT + job_id
    → Encola job en Redis via ARQ para generación LLM
    → Retorna inmediatamente (200ms total):
      { job_id, plan_id, status: "processing", estimated_seconds: 30 }

[2] Flutter polling cada 3 segundos:
    GET /api/v1/jobs/{job_id}
    → { status: "processing", progress_pct: 45 }
    → { status: "processing", progress_pct: 80 }
    → { status: "completed", plan_id: "uuid" }

[3] Cuando status = "completed":
    GET /api/v1/plans/{plan_id}
    → Plan completo con contenido LLM y disclaimer
```

### Endpoints de Jobs

```
GET /api/v1/jobs/{job_id}
  Roles: owner (solo sus jobs)
  Returns:
    { job_id, status: "pending|processing|completed|failed",
      plan_id?, error_message?, progress_pct, created_at, estimated_seconds }
```

### Tabla de Jobs (agregar a DATABASE-SPEC.md)

```sql
CREATE TABLE async_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_type VARCHAR(50) NOT NULL,   -- 'generate_plan', 'scan_label'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- pending | processing | completed | failed
    related_id UUID,                 -- plan_id cuando aplica
    progress_pct SMALLINT DEFAULT 0,
    error_code VARCHAR(30),          -- NV-LLM-001, NV-TOXICITY-001
    error_message TEXT,
    idempotency_key VARCHAR(100) UNIQUE,  -- para deduplicar
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);
CREATE INDEX idx_jobs_user ON async_jobs(user_id, created_at DESC);
CREATE INDEX idx_jobs_status ON async_jobs(status) WHERE status IN ('pending', 'processing');
```

---

## Estrategia de Caché

Redis está disponible desde el inicio (requerido por ARQ job queue). Se usa para caché de datos calientes:

| Dato | Estrategia | TTL |
|------|-----------|-----|
| ToxicityDB | In-memory Python (hard-coded) | Permanente (process lifetime) |
| RestrictionsDB | In-memory Python (hard-coded) | Permanente (process lifetime) |
| Plan activo | Redis key `plan_active:{pet_id}` | 1 hora |
| Perfil mascota | Redis key `pet_profile:{pet_id}` | 15 min |
| User tier | Redis key `user_tier:{user_id}` | 15 min |
| Rate limit | Redis INCR `ratelimit:{user_id}:{minute}` | 60s |
| Resultados OCR | Redis key `scan_result:{scan_id}` | 24h |

---

## Arquitectura de Eventos y Notificaciones

### Domain Events

```python
# app/domain/events.py
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class PlanPendingVetEvent:
    """Disparado cuando un plan requiere firma veterinaria."""
    plan_id: str
    pet_id: str
    pet_name: str
    owner_id: str
    vet_id: str | None  # None si no hay vet asignado aún

@dataclass(frozen=True)
class PlanSignedEvent:
    """Disparado cuando un vet aprueba un plan."""
    plan_id: str
    vet_id: str
    owner_id: str
    pet_name: str

@dataclass(frozen=True)
class PlanRejectedEvent:
    """Disparado cuando un vet rechaza un plan con notas."""
    plan_id: str
    vet_id: str
    owner_id: str
    pet_name: str
    rejection_notes: str

@dataclass(frozen=True)
class ToxicityBlockedEvent:
    """Disparado cuando se bloquea un plan por ingrediente tóxico."""
    plan_id: str
    pet_id: str
    owner_id: str
    toxic_ingredient: str
    species: str
```

### Dispatcher de Notificaciones (Puerto Hexagonal)

```python
# app/application/ports/notification_port.py
from abc import ABC, abstractmethod

class INotificationService(ABC):
    """Puerto de notificaciones — implementado en infrastructure layer."""

    @abstractmethod
    async def notify_plan_pending_vet(self, event: PlanPendingVetEvent) -> None: ...

    @abstractmethod
    async def notify_plan_signed(self, event: PlanSignedEvent) -> None: ...

    @abstractmethod
    async def notify_plan_rejected(self, event: PlanRejectedEvent) -> None: ...

# app/infrastructure/notifications/dispatcher.py
class NotificationDispatcher(INotificationService):
    def __init__(self, fcm: FCMClient, ses: SESClient):
        self._fcm = fcm
        self._ses = ses

    async def notify_plan_pending_vet(self, event: PlanPendingVetEvent) -> None:
        # Push al owner: "Tu plan está siendo revisado"
        await self._fcm.send(
            user_id=event.owner_id,
            title="Plan en revisión",
            body=f"El plan de {event.pet_name} está siendo revisado por el veterinario"
        )
        # Email al vet si hay uno asignado
        if event.vet_id:
            await self._ses.send_template(
                to=event.vet_id,
                template="plan_pending_vet",
                data={"pet_name": event.pet_name}
            )

    async def notify_plan_signed(self, event: PlanSignedEvent) -> None:
        await self._fcm.send(
            user_id=event.owner_id,
            title="Plan aprobado ✓",
            body=f"El plan de {event.pet_name} fue aprobado. ¡Ya puede comenzar!"
        )

    async def notify_plan_rejected(self, event: PlanRejectedEvent) -> None:
        await self._fcm.send(
            user_id=event.owner_id,
            title="Plan con ajustes sugeridos",
            body=f"El veterinario sugirió cambios al plan de {event.pet_name}"
        )
```

---

## Puertos Hexagonales (Interfaces de Infraestructura)

El domain/application layer nunca importa clases de infrastructure. Se comunican
vía interfaces (puertos):

```python
# app/application/ports/
# ├── notification_port.py  ← INotificationService
# ├── llm_port.py           ← ILLMClient
# ├── storage_port.py       ← IStorageService (R2/S3-compatible)
# └── email_port.py         ← IEmailService

# app/application/ports/llm_port.py
from typing import Protocol

class ILLMClient(Protocol):
    """Interfaz del cliente LLM — agnóstica al proveedor."""
    async def complete(self, prompt: str, max_tokens: int = 2000) -> str: ...
    async def complete_vision(self, prompt: str, image_b64: str) -> str: ...
    def get_provider_name(self) -> str: ...

# Implementaciones concretas en infrastructure/llm/:
# OllamaClient, GroqClient, OpenAIClient — todas implementan ILLMClient
```

---

## Archivos Adicionales en la Estructura

```
backend/app/
├── domain/
│   └── events.py                    ← Domain events (inmutables, frozen dataclasses)
│
├── application/
│   └── ports/                       ← Interfaces de puertos (Hexagonal)
│       ├── notification_port.py     ← INotificationService
│       ├── llm_port.py              ← ILLMClient (Protocol)
│       ├── storage_port.py          ← IStorageService
│       └── email_port.py            ← IEmailService
│
├── infrastructure/
│   ├── cache/
│   │   └── redis_cache.py           ← Redis cache service (via ARQ's Redis connection)
│   ├── notifications/
│   │   ├── fcm_client.py            ← Firebase Cloud Messaging (push)
│   │   ├── email_client.py          ← Resend / SMTP (emails transaccionales)
│   │   └── dispatcher.py            ← NotificationDispatcher
│   ├── jobs/
│   │   └── job_repository.py        ← AsyncJob CRUD
│   └── llm/
│       └── resilience.py            ← llm_retry decorator, fallback chain
│
└── presentation/
    └── api/v1/
        ├── health.py                ← GET /health, GET /ready
        ├── jobs.py                  ← GET /jobs/{job_id}
        └── push_tokens.py           ← POST /users/me/push-token
```

**Tabla adicional requerida:**
```sql
-- Tokens de dispositivo para push notifications (FCM)
CREATE TABLE push_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    platform VARCHAR(10) NOT NULL CHECK (platform IN ('ios', 'android')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_push_tokens_user ON push_tokens(user_id);

-- Tabla de idempotencia para POST /plans
CREATE TABLE idempotency_keys (
    key VARCHAR(100) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    endpoint VARCHAR(100) NOT NULL,
    response_body JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);
CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);
```
