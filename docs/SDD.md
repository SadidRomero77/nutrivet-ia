# SDD — Software Design Document
# NutriVet.IA v2.0

**Versión**: 2.0 · **Fecha**: Marzo 2026
**Autores**: Sadid Romero (AI Engineer) · Lady Carolina Castañeda (MV, BAMPYSVET)
**Estado**: Aprobado

---

## 1. Propósito y Alcance

Este documento describe el diseño de software de NutriVet.IA — plataforma agéntica de nutrición veterinaria personalizada para perros y gatos en LATAM. Cubre la arquitectura de componentes, decisiones de diseño, contratos entre capas, y los patrones de resiliencia aplicados.

**No cubre**: instrucciones de despliegue (ver `DEPLOY-SECURITY-SPEC.md`), esquema SQL detallado (ver `DATABASE-SPEC.md`), ni endpoints completos (ver `BACKEND-SPEC.md`).

---

## 2. Principio de Diseño Central

> **Software grueso / Modelo delgado.**

| Responsabilidad | Quién la ejecuta |
|----------------|-----------------|
| Calcular RER/DER (kcal) | Python determinista — `kcal_calculator.py` |
| Verificar toxicidad de alimentos | Python determinista — `toxicity_db.py` |
| Aplicar restricciones por condición médica | Python determinista — `restrictions_db.py` |
| Validar permisos RBAC | Middleware FastAPI — `rbac.py` |
| Calcular fase BCS (reducción / mantenimiento / aumento) | Python determinista — `bcs_logic.py` |
| Sintetizar el plan en lenguaje natural | LLM (Qwen2.5-7B / Groq / GPT-4o) |
| Redactar instrucciones de preparación | LLM |
| OCR de tabla nutricional o ingredientes | LLM visión (Qwen2.5-VL-7B) |
| Adaptar tono al perfil del propietario | LLM |

El LLM **nunca** decide si algo es tóxico, si una restricción médica aplica, o cuántas calorías necesita una mascota.

---

## 3. Arquitectura del Sistema

### 3.1 Vista de Capas (Clean Architecture / Hexagonal)

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                      │
│  FastAPI routers · Pydantic schemas · JWT/RBAC middleware│
└────────────────────────┬────────────────────────────────┘
                         │ depende de ↓
┌────────────────────────▼────────────────────────────────┐
│                 APPLICATION LAYER                        │
│  Use Cases · Ports (interfaces) · Domain Events         │
└────────────────────────┬────────────────────────────────┘
                         │ depende de ↓
┌────────────────────────▼────────────────────────────────┐
│                   DOMAIN LAYER                           │
│  Entities · Value Objects · Domain Services             │
│  ToxicityDB · RestrictionsDB · KcalCalculator           │
│  (sin dependencias externas — Python puro)              │
└─────────────────────────────────────────────────────────┘
                         ▲ implementado por ↑
┌─────────────────────────────────────────────────────────┐
│               INFRASTRUCTURE LAYER                       │
│  PostgreSQL repositories · LLM clients · R2Storage · FCM │
│  LangGraph agent · OpenRouter adapter · ARQ job queue   │
└─────────────────────────────────────────────────────────┘
```

**Regla de oro**: las dependencias apuntan hacia adentro. El domain layer no importa nada de infrastructure ni de FastAPI.

### 3.2 Vista de Componentes del Sistema

```
Flutter App (iOS/Android)
        │
        │ HTTPS / JSON
        ▼
Cloudflare CDN + DNS
        │
        ▼
Caddy (reverse proxy — Coolify en Hetzner CPX31)
        │
        ▼
FastAPI + Uvicorn (proceso persistente — 2 workers)
   ├── Auth Router           → JWT issue / refresh / revoke
   ├── Pets Router           → CRUD + condiciones + alergias
   ├── Plans Router          → generar / ajustar / firmar / rechazar
   ├── Scanner Router        → OCR etiquetas nutricionales
   ├── Concentrates Router   → perfil ideal + sponsors
   ├── Foods Router          → búsqueda + toxicidad
   ├── Jobs Router           → polling generación asíncrona
   └── Health Router         → liveness + readiness
        │
        ├── PostgreSQL 16 (Docker)    → usuarios, mascotas, planes, trazas
        ├── Redis 7 (Docker)          → ARQ job queue + caché (TTLs)
        ├── Cloudflare R2             → imágenes OCR (lifecycle 90 días)
        ├── Coolify env vars          → JWT secret, API keys, DB password
        └── Sentry + Coolify logs     → errores + métricas estructuradas
```

### 3.3 Vista del Agente LangGraph

```
POST /api/v1/plans  ──→  GeneratePlanUseCase
                              │
                              ▼
                    [LangGraph StateGraph]
                              │
                    ┌─────────▼──────────┐
                    │  load_pet_profile  │ ← carga 12 campos + condiciones + alergias
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────────┐
                    │ validate_medical_context│ ← aplica RESTRICTIONS_BY_CONDITION
                    └─────────┬──────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  calculate_kcal    │ ← RER × factores (determinista)
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   check_modality   │
                    └──────┬──────┬──────┘
                           │      │
               natural ────┘      └──── concentrate
                    │                       │
         ┌──────────▼──────┐    ┌───────────▼──────┐
         │select_ingredients│   │ generate_profile  │
         └──────────┬───────┘   └───────────┬───────┘
                    │                       │
                    └──────────┬────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  validate_toxicity  │ ← TOXIC_DOGS / TOXIC_CATS (hard-coded)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  validate_allergies │ ← lista alérgenos del paciente
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  check_hitl_required│ ← condición médica? → PENDING_VET
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  format_plan_output │ ← LLM: redacción natural (único punto LLM)
                    └──────────┬──────────┘
                               │
                             [END]
```

**NutriVetState** (TypedDict compartido por todos los nodos):

```python
class NutriVetState(TypedDict):
    pet_id: str
    pet_profile: dict          # 12 campos del wizard
    medical_conditions: list   # condiciones activas
    food_allergies: list       # alérgenos del paciente
    nutritional_requirements: dict  # rer, der, macros
    modality: str              # natural | concentrate
    approved_ingredients: dict
    forbidden_ingredients: list
    plan_draft: dict           # plan antes de síntesis LLM
    plan_final: dict           # plan sintetizado por LLM
    plan_status: str           # DRAFT | PENDING_VET | ACTIVE
    hitl_required: bool
    agent_trace: dict          # trazabilidad de cada nodo
    llm_provider: str          # ollama | groq | openai
    error: str | None
```

---

## 4. Diseño de Componentes por Capa

### 4.1 Domain Layer

Módulos con cero dependencias externas. Sólo Python estándar.

#### 4.1.1 KcalCalculator

```
Entrada : weight_kg, species, reproductive_status, activity_level,
          age_years, body_condition_score, physiological_state, medical_conditions
Proceso : RER = 70 × weight_kg^0.75
          factor = FACTOR_TABLE[(species, reproductive_status, activity_level)]
          factor × BCS_ADJUSTMENTS[bcs] × AGE_ADJUSTMENTS[state]
          factor × CONDITION_ADJUSTMENTS[condition] (si aplica)
          DER = RER × factor_final
Salida  : rer_kcal, der_kcal, factor_applied, meals_per_day, macros_g_day
Garantía: resultado determinista y reproducible — mismo input → mismo output
```

Caso de referencia validado por Lady Carolina (MV):
- Sally: 9.6 kg, esterilizada, baja actividad, 8 años, hepática/diabética → DER ≈ 534 kcal

#### 4.1.2 ToxicityDatabase

```python
TOXIC_DOGS: frozenset[str]  # inmutable — nunca editable en runtime
TOXIC_CATS: frozenset[str]  # inmutable — nunca editable en runtime

class ToxicityDatabase:
    def check(self, food_name: str, species: str) -> ToxicityResult: ...
    # Normaliza: lowercase, sin tildes, aliases regionales
    # Retorna: is_safe, risk_level, reason, safe_alternatives
```

Aliases regionales soportados: `cebolla = cebolla de verdeo = spring onion`, `aguacate = palta`, etc.

#### 4.1.3 RestrictionsDatabase

```python
RESTRICTIONS_BY_CONDITION: dict[str, ConditionRestriction]
# Hard-coded — requiere validación veterinaria para modificar

class ConditionRestriction:
    forbidden: list[str]       # alimentos siempre prohibidos
    max_fat_pct: float | None
    max_protein_pct: float | None
    max_carbs_pct: float | None
    max_fasting_hours: int | None  # gastritis → 12h max
    meals_per_day_min: int | None
    supplements: list[str]
    meal_frequency_note: str | None
```

#### 4.1.4 Entidades del Dominio

| Entidad | Invariantes clave |
|---------|------------------|
| `Pet` | `weight_kg > 0`, `bcs ∈ [1,9]`, `species ∈ {dog, cat}` |
| `NutritionPlan` | `plan_content != {}`, `status` sigue FSM válida |
| `User` | `role ∈ {owner, vet, admin}`, vets tienen `professional_card` |
| `MedicalCondition` | `cancer` requiere `cancer_location_encrypted` |
| `Sponsor` | `is_active=True` requiere `verified_by_vet_id IS NOT NULL` |

### 4.2 Application Layer — Use Cases

Cada caso de uso recibe sus dependencias por inyección (puertos). No instancia infraestructura directamente.

```
GenerateNaturalPlanUseCase
  Dependencias: IPetRepository, IKcalCalculator, IToxicityDatabase,
                IRestrictionsDatabase, ILLMClient, IPlanRepository,
                INotificationService, IJobRepository
  Flujo:
    1. Validar que mascota pertenece al owner autenticado
    2. Calcular RER/DER (determinista)
    3. Aplicar restricciones por condición médica
    4. Seleccionar ingredientes permitidos
    5. Validar toxicidad de cada ingrediente
    6. Generar borrador de plan (Python puro)
    7. Invocar LLM solo para síntesis de texto
    8. Determinar status: PENDING_VET si hay condición médica
    9. Persistir plan + emitir evento de dominio
    10. Retornar job_id para polling asíncrono
```

```
SignPlanUseCase
  Precondición: usuario autenticado con role = vet
  Flujo:
    1. Verificar que plan.status == PENDING_VET
    2. Registrar firma (professional_card, signed_at, notes)
    3. Cambiar status → ACTIVE
    4. Emitir PlanSignedEvent → notificación al owner
    5. Registrar en plan_changes (inmutable)
```

```
ValidateToxicityUseCase
  Entrada: food_name, species, medical_conditions
  Flujo:
    1. Normalizar food_name (lowercase, remover tildes)
    2. Buscar en TOXIC_DOGS o TOXIC_CATS
    3. Si tóxico → BLOCK inmediato (no continuar)
    4. Si no tóxico → verificar RESTRICTIONS_BY_CONDITION
    5. Retornar ToxicityResult con risk_level y safe_alternatives
```

### 4.3 Infrastructure Layer

#### 4.3.1 LLM Client Abstraction

```
ILLMClient (Protocol)
    ├── OllamaClient        → Qwen2.5-7B local ($0, 0 condiciones médicas)
    ├── GroqClient          → Llama-70B ($0 free tier, 1-2 condiciones)
    └── OpenAIClient        → GPT-4o ($0.01/plan, 3+ condiciones)

LLMClientFactory
    select_llm(pet: Pet) → ILLMClient
    Criterio: len(pet.active_conditions) → 0 | 1-2 | 3+

VisionClient (separado del texto)
    └── OllamaVisionClient  → Qwen2.5-VL-7B ($0, siempre para OCR)
```

Circuit breaker por proveedor:
```
0 condiciones: Ollama → timeout → Groq fallback → 503
1-2 cond.:     Groq   → rate limit → GPT-4o → 503
3+ cond.:      GPT-4o → 3 reintentos con backoff → 503
OCR:           Qwen-VL → timeout → 503 (no fallback a texto)
```

#### 4.3.2 Repositories (Patrón Repository)

Cada repositorio implementa su interface del application layer:

```
IPetRepository → PetSQLRepository (SQLAlchemy async)
    find_by_owner(owner_id: UUID) → list[Pet]
    find_by_id(pet_id: UUID) → Pet | None
    save(pet: Pet) → Pet
    soft_delete(pet_id: UUID) → None

IPlanRepository → PlanSQLRepository
    find_active_by_pet(pet_id: UUID) → NutritionPlan | None
    find_pending_vet() → list[NutritionPlan]
    save(plan: NutritionPlan) → NutritionPlan
    append_change(change: PlanChange) → None  # append-only, nunca UPDATE
```

#### 4.3.3 Notification Dispatcher

```
INotificationService → NotificationDispatcher
    notify_plan_pending_vet(event)  → FCM push (owner) + SES email (vet si asignado)
    notify_plan_signed(event)       → FCM push (owner)
    notify_plan_rejected(event)     → FCM push (owner)
    notify_toxicity_blocked(event)  → FCM push (owner) + alerta de seguridad
```

### 4.4 Presentation Layer

#### 4.4.1 RBAC Middleware

```
@require_role("vet")
async def sign_plan(plan_id: UUID, ...) -> APIResponse[PlanDTO]:
    ...

# El middleware extrae el rol del JWT y valida antes de llegar al handler.
# Nunca verificar rol dentro del router — siempre en middleware.
```

#### 4.4.2 Envelope de Respuesta Estándar

Toda respuesta sigue el mismo contrato:

```json
{
  "success": true | false,
  "data": { ... } | null,
  "error": { "code": "NV-XXX-001", "message": "...", "field": null } | null,
  "meta": { "page": 1, "per_page": 10, "total": 50 } | null,
  "request_id": "uuid"
}
```

---

## 5. Diseño de Flujos Críticos

### 5.1 Flujo de Generación de Plan (Asíncrono)

```
[1] POST /api/v1/plans
    ├── Validar JWT + RBAC (role=owner)
    ├── Validar Pydantic schema
    ├── Verificar Idempotency-Key (24h window)
    ├── CalculateKcalUseCase (< 5ms, determinista)
    ├── ValidateToxicityUseCase (< 5ms, hard-coded)
    ├── Crear async_job en DB (status=pending)
    ├── Encolar job en Redis via ARQ (async, no await)
    └── Retornar { job_id, plan_id, status: "processing", estimated_seconds: 30 }

[2] ARQ Worker — generación LangGraph
    ├── load_pet_profile
    ├── validate_medical_context
    ├── calculate_kcal (determinista)
    ├── select_ingredients
    ├── validate_toxicity × cada ingrediente
    ├── validate_allergies
    ├── check_hitl_required
    ├── format_plan_output (LLM — único punto de LLM en este flujo)
    ├── Actualizar plan en DB con contenido final
    └── Actualizar job status → completed

[3] Flutter polling GET /api/v1/jobs/{job_id} (cada 3s con backoff)
    └── Cuando status=completed → GET /api/v1/plans/{plan_id}
```

### 5.2 Flujo de Revisión Veterinaria (HITL)

```
Plan con condición médica
         │
         ▼ status = PENDING_VET
Notificación → FCM al owner + Email al vet (si asignado)
         │
         ▼ Vet abre dashboard
GET /api/v1/plans/{id}/trace  ← trazabilidad completa: cada nodo LangGraph
         │
         ▼ Vet revisa y decide
POST /api/v1/plans/{id}/sign    → status = ACTIVE → FCM al owner
POST /api/v1/plans/{id}/reject  → status = REJECTED → FCM al owner con notas
         │
         ▼ Owner ajusta (si fue rechazado)
PUT /api/v1/plans/{id}/adjust → vuelve a PENDING_VET (si aún tiene condición médica)
```

### 5.3 Flujo OCR (Scanner)

```
ScannerScreen
    │ Captura foto
    │ ImageProcessor.prepareForOCR() — comprime a < 4MB
    │ Valida dimensiones mínimas (500px)
    ▼
POST /api/v1/scanner/label
    ├── Validar image_type ∈ {nutritional_table, ingredients_list}
    ├── Si imagen parece ser marca/logo → 400 NV-OCR-001
    ├── Upload imagen a Cloudflare R2 (lifecycle 90 días)
    ├── Qwen2.5-VL-7B extrae valores nutricionales
    ├── Evaluar vs perfil del paciente (determinista)
    └── Retornar { adequacy, extracted_values, concerns, positives, confidence }

adequacy: "adequate" | "caution" | "not_recommended"
```

---

## 6. Diseño de Seguridad

### 6.1 Capas de Seguridad

```
Capa 1 — Red:         Cloudflare basic (DDoS + rate limiting) + Hetzner Firewall
Capa 2 — Transporte:  HTTPS/TLS 1.3 forzado via Caddy (Let's Encrypt automático)
Capa 3 — Auth:        JWT HS256 (access 15min + refresh 30 días rotativo)
Capa 4 — Autorización: RBAC en middleware (owner / vet)
Capa 5 — Validación:  Pydantic en todos los endpoints (input validation)
Capa 6 — Datos:       AES-256 para datos médicos en reposo (cryptography lib + env var)
Capa 7 — Secretos:    Coolify env vars — nunca en código ni en .env committed
Capa 8 — Auditoría:   plan_changes (append-only) + agent_traces (inmutables)
Capa 9 — SAST:        bandit + safety en cada PR (falla en HIGH findings)
```

### 6.2 JWT Strategy

```
Access Token:  30 minutos — payload: { user_id, role, email_verified }
Refresh Token: 7 días — rotativo (cada uso genera nuevo token)
               hash almacenado en refresh_tokens table
               revocado en logout + en refresh exitoso

Regla: access token NO contiene datos clínicos ni médicos
```

### 6.3 Cifrado de Datos Médicos

Campos cifrados AES-256 antes de INSERT:
- `medical_conditions.cancer_location_encrypted`
- `medical_conditions.notes_encrypted`

El domain layer nunca recibe los bytes cifrados — la infraestructura descifra antes de construir la entidad.

### 6.4 Logs — Zero PII Policy

```python
# CORRECTO
log.info("plan_generated", plan_id=plan_id, species=species, modality=modality)

# INCORRECTO — NUNCA en logs
log.info("plan_generated", owner_email=email, pet_name=name, condition=notes)
```

Campos excluidos de todos los logs: `email`, `full_name`, `password`, `token`, `cancer_location`, `notes`.

---

## 7. Diseño de Resiliencia

### 7.1 Timeouts por Operación

| Operación | Timeout | Justificación |
|-----------|---------|---------------|
| Cálculo kcal (determinista) | 10ms | Python puro |
| Verificación toxicidad | 5ms | Lookup en dict |
| Query PostgreSQL | 5s | asyncpg pool |
| Upload R2 | 15s | Imagen 4MB — boto3 con R2 endpoint |
| LLM plan simple (llama-3.3-70b) | 30s | OpenRouter |
| LLM plan moderado (gpt-4o-mini) | 60s | OpenRouter |
| LLM plan complejo (claude-sonnet-4-5) | 120s | 3+ condiciones |
| OCR gpt-4o vision | 20s | OpenRouter |

### 7.2 Retry Policy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError))
)
async def call_llm(...): ...
```

Solo reintentar en: timeout, rate limit, connection error.
**Nunca** reintentar en: 4xx (error del cliente), toxicity block, validación fallida.

### 7.3 Cache Strategy (Redis disponible vía ARQ)

| Dato | Estrategia | TTL |
|------|-----------|-----|
| ToxicityDB | In-memory Python (hard-coded, process lifetime) | Permanente |
| RestrictionsDB | In-memory Python (hard-coded, process lifetime) | Permanente |
| Plan activo | Redis `plan_active:{pet_id}` | 1 hora |
| Perfil mascota | Redis `pet_profile:{pet_id}` | 15 min |
| Plan activo (mobile) | Hive local en Flutter | 7 días |

---

## 8. Patrones de Diseño Aplicados

| Patrón | Dónde | Por qué |
|--------|-------|---------|
| Repository | Infrastructure → Application | Aislar persistencia del dominio |
| Factory | `LLMClientFactory` | Seleccionar proveedor LLM por complejidad |
| Strategy | Cada `ILLMClient` | Intercambiar modelos sin cambiar lógica |
| Observer | Domain Events + NotificationDispatcher | Desacoplar generación de plan de notificaciones |
| Circuit Breaker | Cadena de fallback LLM | Resiliencia ante proveedores externos |
| Decorator | `@llm_retry` | Retry sin modificar la función objetivo |
| CQRS parcial | `plan_changes` append-only | Separar escritura de auditoría de lectura de estado |
| Idempotency Key | `POST /plans` | Prevenir planes duplicados por retry del cliente |
| Correlation ID | `X-Request-ID` header | Trazabilidad distribuida entre Uvicorn + DB + LLM |

---

## 9. Non-Functional Requirements (NFR)

| NFR | Objetivo | Cómo se mide |
|-----|---------|-------------|
| Latencia API (p95) | < 500ms (sin LLM) | Sentry + structlog |
| Latencia generación plan (p95) | < 30s (simple) · < 120s (complejo) | Polling job_status |
| Latencia OCR (p95) | < 20s | agent_traces.latency_ms |
| Disponibilidad | > 99.5% | Coolify health check + Sentry |
| Cobertura de tests | ≥ 80% total · 100% domain layer | pytest-cov |
| Seguridad | 0 findings HIGH en bandit | CI/CD gate |
| Correctitud clínica | 0 tóxicos en planes (G1) | golden set 60 casos |
| Reproducibilidad | Caso Sally → 534 kcal ±0.5 | `test_kcal_calculator.py` |

---

## 10. Decisiones de Diseño Clave (Rationale)

### Por qué Clean Architecture sobre MVC tradicional

El domain layer de NutriVet.IA contiene lógica de seguridad clínica crítica (`ToxicityDB`, `RestrictionsDB`, `KcalCalculator`). Con Clean Architecture, estos módulos se pueden testear al 100% con unit tests puros, sin levantar base de datos ni servidor. En MVC, la lógica de negocio tiende a mezclarse con el framework, dificultando el testing determinista requerido por los quality gates (G1, G2, G5).

### Por qué LangGraph sobre LangChain directa

LangGraph ofrece HITL nativo como un punto de interrupción en el grafo de estados — esto es exactamente el mecanismo que necesita el flujo `PENDING_VET`. Con LangChain directa, implementar HITL requeriría lógica custom de estado y orquestación que LangGraph provee out-of-the-box.

### Por qué generación de planes asíncrona (jobs)

La generación de un plan complejo (3+ condiciones, claude-sonnet-4-5) puede tomar hasta 120 segundos. El patrón job asíncrono con ARQ + Redis permite UX fluido (spinner con progreso) sin bloquear la conexión HTTP. FastAPI retorna inmediatamente con `job_id`, el ARQ worker procesa en background.

### Por qué datos médicos cifrados pero no el plan completo

Los datos médicos (`cancer_location`, notas clínicas) son PII sensible que requiere AES-256 por Ley 1581/2012. El `plan_content` JSONB no contiene datos del propietario — solo ingredientes, kcal, y macros — por lo que el cifrado a nivel de columna no es necesario para el plan.

---

## 11. Diagrama de Dependencias entre Módulos

```
presentation/api/v1/plans.py
    → application/use_cases/generate_natural_plan.py
        → domain/nutrition/kcal_calculator.py          (sin deps)
        → domain/food/toxicity_db.py                   (sin deps)
        → domain/food/restrictions_db.py               (sin deps)
        → application/ports/llm_port.py (ILLMClient)
            ← infrastructure/llm/ollama_client.py
            ← infrastructure/llm/groq_client.py
            ← infrastructure/llm/openai_client.py
        → application/ports/notification_port.py (INotificationService)
            ← infrastructure/notifications/dispatcher.py
        → infrastructure/llm/agent/graph.py (LangGraph)
            → infrastructure/llm/agent/tools/nutrition_calculator.py
            → infrastructure/llm/agent/tools/food_toxicity_checker.py
            → infrastructure/llm/agent/tools/plan_generator.py
```

Flecha `→` = "depende de". Flecha `←` = "implementado por".

---

*Documento complementado por: `DATABASE-SPEC.md` · `BACKEND-SPEC.md` · `DEPLOY-SECURITY-SPEC.md` · `DDD.md` · `BDD.md` · `AI-DLC.md`*
