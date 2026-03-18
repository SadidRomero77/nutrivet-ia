# Application Design — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10
**Estado**: Draft — Gate 4 pendiente

---

## Resumen Ejecutivo

NutriVet.IA es una aplicación agéntica de planes nutricionales veterinarios construida sobre **Clean Architecture / Hexagonal** en el backend (Python + FastAPI) y **Flutter** en el cliente móvil.

El sistema tiene tres flujos principales:
1. **Generación de plan**: owner completa wizard → agente LangGraph calcula RER/DER + valida seguridad + llama LLM via OpenRouter → plan ACTIVE (mascota sana) o PENDING_VET (condición médica)
2. **Revisión veterinaria (HITL)**: vet revisa plan + valida set de sustitutos → aprueba o devuelve con comentario
3. **Agente conversacional + OCR**: consultas nutricionales respondidas por LLM; consultas médicas remitidas al vet; escaneo de etiquetas nutricionales via GPT-4o Vision

---

## Decisiones Arquitecturales Clave

### 1. Generación de plan asíncrona (job_id + polling)

La generación de plan toma hasta 25-30 segundos — demasiado para una respuesta HTTP síncrona. Se usa el patrón async con ARQ (job queue sobre Redis):

```
POST /v1/plans → { job_id: "abc123" }
GET  /v1/plans/jobs/abc123 → { status: "PROCESSING" }
GET  /v1/plans/jobs/abc123 → { status: "READY", plan_id: "xyz" }
GET  /v1/plans/xyz → { plan completo }
```

Flutter hace polling cada 3 segundos mostrando indicador de progreso. Tiempo máximo: 60 segundos.

### 2. OpenRouter como proveedor unificado de LLMs

Un solo cliente (`OpenRouterClient`), routing determinístico por tier + condiciones (ADR-019):
- Free → `meta-llama/llama-3.3-70b`
- Básico → `openai/gpt-4o-mini`
- Premium/Vet → `anthropic/claude-sonnet-4-5`
- 3+ condiciones (cualquier tier) → `anthropic/claude-sonnet-4-5`
- OCR → `openai/gpt-4o` (vision)

### 3. Guardarraíles determinísticos en domain layer

El LLM decide el plan nutricional, pero tres componentes en domain layer son inviolables y se ejecutan ANTES del LLM:
- `NRCCalculator`: RER/DER siempre Python — nunca LLM
- `FoodSafetyChecker`: TOXIC_DOGS/TOXIC_CATS — siempre hard-coded
- `MedicalRestrictionEngine`: RESTRICTIONS_BY_CONDITION — siempre hard-coded

### 4. LangGraph con PostgreSQL checkpointer

El estado del agente (`NutriVetState`) se persiste en PostgreSQL via checkpointer nativo de LangGraph. Esto permite:
- Continuar conversaciones entre sesiones
- Trazabilidad completa de decisiones del agente
- `agent_traces` como tabla append-only (sin UPDATE post-inserción)

### 5. Offline-first con Hive en Flutter + Riverpod

Flutter gestiona estado con Riverpod (providers async). Hive provee caché local para:
- Plan activo (lectura offline)
- Historial de conversaciones (solo lectura)
- Registros de peso/BCS pendientes de sync
- Perfil de mascota

Estrategia de sync: unidireccional — el servidor siempre gana en conflictos (MVP).

### 6. ClinicPet — dos tipos de mascota

```python
class PetOrigin(str, Enum):
    APP_PET = "app_pet"        # Owner con cuenta activa
    CLINIC_PET = "clinic_pet"  # Creada por vet, propietario sin app
```

ClinicPet tiene campos adicionales: `owner_name` y `owner_phone` para contacto y envío del PDF. Código de reclamación (TTL 30 días) permite conversión a AppPet con historial preservado.

### 7. Versionado de API desde el día 1

Todas las rutas usan prefijo `/v1/`. Permite introducir `/v2/` sin romper clientes de la versión anterior.

---

## Estructura de Directorios (Backend)

```
backend/
├── domain/
│   ├── nutrition/
│   │   └── nrc_calculator.py
│   ├── safety/
│   │   ├── toxic_foods.py          # TOXIC_DOGS, TOXIC_CATS — nunca modificar sin validación vet
│   │   └── medical_restrictions.py # RESTRICTIONS_BY_CONDITION
│   ├── aggregates/
│   │   ├── pet_profile.py
│   │   ├── nutrition_plan.py
│   │   └── user_account.py
│   └── events/
│       └── domain_events.py
├── application/
│   ├── use_cases/
│   │   ├── plan_generation.py
│   │   ├── hitl_review.py
│   │   ├── pet_profile.py
│   │   ├── weight_tracking.py
│   │   ├── export_plan.py
│   │   ├── pet_claim.py
│   │   └── auth.py
│   └── ports/                      # Interfaces de repositorios
│       ├── pet_repository.py
│       ├── plan_repository.py
│       └── user_repository.py
├── infrastructure/
│   ├── db/
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── repositories/
│   ├── llm/
│   │   ├── openrouter_client.py
│   │   └── llm_router.py
│   ├── agent/
│   │   ├── orchestrator.py         # LangGraph orchestrator
│   │   ├── state.py                # NutriVetState
│   │   └── subgraphs/
│   │       ├── plan_generation.py
│   │       ├── consultation.py
│   │       ├── scanner.py
│   │       └── referral.py
│   ├── storage/
│   │   ├── r2_client.py            # Cloudflare R2 (boto3 con endpoint personalizado)
│   │   └── pdf_generator.py
│   └── notifications/
│       ├── fcm_service.py
│       └── email_service.py
└── presentation/
    ├── routers/
    │   ├── v1/
    │   │   ├── plans.py
    │   │   ├── pets.py
    │   │   ├── auth.py
    │   │   ├── export.py
    │   │   ├── agent.py
    │   │   └── vet_dashboard.py
    ├── schemas/                    # Pydantic request/response models
    ├── middleware/
    │   ├── jwt_auth.py
    │   └── rbac.py
    └── main.py                     # FastAPI app (Uvicorn — sin Mangum)
```

---

## Estructura de Directorios (Flutter)

```
mobile/
├── lib/
│   ├── domain/
│   │   └── models/                 # Dart models (PetProfile, NutritionPlan, etc.)
│   ├── data/
│   │   ├── repositories/           # Implementaciones con API + Hive
│   │   └── datasources/
│   │       ├── remote/             # HTTP clients FastAPI
│   │       └── local/              # Hive adapters
│   ├── application/
│   │   └── providers/              # Riverpod providers
│   └── presentation/
│       ├── screens/
│       │   ├── wizard/
│       │   ├── plan/
│       │   ├── chat/
│       │   ├── ocr/
│       │   ├── dashboard/
│       │   └── vet_dashboard/
│       └── widgets/
└── test/
```

---

## Flujo de Datos — Generación de Plan

```
Flutter WizardScreen
  → POST /v1/plans { pet_id, modality }
  → PlanRouter → PlanGenerationUseCase
      → NRCCalculator.calculate_rer/der(pet)
      → FoodSafetyChecker.validate(ingredients)
      → MedicalRestrictionEngine.get_restrictions(conditions)
      → LLMRouter.route(tier, conditions_count) → model_id
      → Job creado en DB con status=PENDING
      → Retorna { job_id }

Flutter (polling cada 3s)
  → GET /v1/plans/jobs/{job_id}
  → ARQ Worker background: LangGraphOrchestrator.process(state)
      → Plan Generation Subgraph
          → OpenRouterClient.complete(model_id, prompt_con_guardarraíles)
          → LLM genera plan + set de sustitutos
          → FoodSafetyChecker valida output del LLM
          → hitl_router: conditions > 0 → PENDING_VET, else → ACTIVE
      → agent_traces INSERT (inmutable)
      → Job status = READY
  → GET /v1/plans/{plan_id} → plan completo
Flutter muestra plan + habilita exportar PDF
```

---

## NFRs Críticos

| NFR | Valor | Implementación |
|-----|-------|----------------|
| Generación de plan | ≤ 60s | Async + polling + OpenRouter timeout 55s |
| Uptime | 99.9% | Hetzner CPX31 + Docker restart:always + Coolify health check |
| Datos en reposo | AES-256 | EncryptedColumn SQLAlchemy (clave en env var via cryptography lib) |
| Trazas agente | Inmutables | Tabla `agent_traces` sin UPDATE |
| API versioning | /v1/* desde día 1 | FastAPI prefix |
| Offline | Plan + historial + peso/BCS | Hive + Riverpod |
