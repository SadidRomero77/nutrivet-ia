# Unit of Work — NutriVet.IA

**Fase**: Inception — Application Design
**Fecha**: 2026-03-16

Definición de las 9 unidades de trabajo implementables e independientemente testeables.
Cada unidad tiene criterios de done verificables, estimación y dependencias explícitas.

---

## Resumen de Unidades

| # | Unidad | Capa | Prioridad | Estimación |
|---|--------|------|-----------|------------|
| U-01 | domain-core | Domain | BLOQUEANTE | 5-7 días |
| U-02 | auth-service | Infra + Presentation | BLOQUEANTE | 4-5 días |
| U-03 | pet-service | Infra + Presentation | BLOQUEANTE | 5-6 días |
| U-04 | plan-service | Application + Infra | CRÍTICA | 8-10 días |
| U-05 | agent-core | Infrastructure (LangGraph) | BLOQUEANTE | 7-9 días |
| U-06 | scanner-service | Infrastructure (Agent) | CRÍTICA | 5-6 días |
| U-07 | conversation-service | Infrastructure (Agent) | CRÍTICA | 5-6 días |
| U-08 | export-service | Application + Infra | CRÍTICA | 4-5 días |
| U-09 | mobile-app | Presentation (Flutter) | ENTREGA FINAL | 14-16 días |

**Total estimado**: 55-70 días | Con paralelización U-06/07/08: reducción de 10-12 días

---

## Matriz de Dependencias

```
U-01 (domain-core)
  └─ U-02 (auth-service)
  └─ U-03 (pet-service) ← depende de U-01, U-02
      └─ U-04 (plan-service) ← depende de U-01, U-02, U-03
          └─ U-05 (agent-core) ← depende de U-01, U-04
              ├─ U-06 (scanner-service) ← depende de U-05
              ├─ U-07 (conversation-service) ← depende de U-05
              └─ U-08 (export-service) ← depende de U-04, U-05
                  └─ U-09 (mobile-app) ← depende de U-01..U-08
```

Ver `unit-of-work-dependency.md` para matriz completa.

---

## U-01: domain-core

**Fase**: A — Fundamentos (sin dependencias externas)
**Prioridad**: BLOQUEANTE — ninguna otra unidad puede iniciar sin esta
**Estimación**: 5-7 días

### Descripción

Implementa el núcleo puro del dominio: cálculo calórico NRC determinístico, listas de toxicidad
hard-coded, motor de restricciones médicas, y todas las entidades y value objects del negocio.
**Cero dependencias externas — solo Python stdlib.**

### User Stories

| Story | Descripción |
|-------|-------------|
| US-06 | RER/DER calculados determinísticamente para mascota sana |
| US-07 | Restricciones médicas hard-coded aplicadas correctamente |
| US-07 | Ningún ingrediente tóxico aparece en ningún plan |
| US-08 | Motor de restricciones valida sustitutos |
| Todas | Entidades PetProfile, NutritionPlan, UserAccount disponibles |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| NRCCalculator | `domain/nutrition/nrc_calculator.py` |
| FoodSafetyChecker | `domain/safety/food_safety_checker.py` |
| MedicalRestrictionEngine | `domain/safety/medical_restriction_engine.py` |
| PetProfile (Aggregate Root) | `domain/aggregates/pet_profile.py` |
| NutritionPlan (Aggregate Root) | `domain/aggregates/nutrition_plan.py` |
| UserAccount (Aggregate Root) | `domain/aggregates/user_account.py` |
| Constantes TOXIC_DOGS / TOXIC_CATS | `domain/safety/toxic_foods.py` |
| Constantes RESTRICTIONS_BY_CONDITION | `domain/safety/restrictions.py` |
| Value Objects | `domain/value_objects/` |

### Estructura de Archivos

```
backend/
└── domain/
    ├── __init__.py
    ├── aggregates/
    │   ├── pet_profile.py
    │   ├── nutrition_plan.py
    │   └── user_account.py
    ├── value_objects/
    │   ├── species.py
    │   ├── size.py
    │   ├── activity_level.py
    │   ├── bcs.py
    │   ├── reproductive_status.py
    │   ├── current_diet.py
    │   ├── plan_status.py
    │   ├── plan_modality.py
    │   ├── plan_type.py
    │   ├── medical_condition.py
    │   ├── user_role.py
    │   └── subscription_tier.py
    ├── nutrition/
    │   └── nrc_calculator.py
    ├── safety/
    │   ├── toxic_foods.py
    │   ├── restrictions.py
    │   ├── food_safety_checker.py
    │   └── medical_restriction_engine.py
    └── exceptions.py

tests/domain/
    ├── test_nrc_calculator.py
    ├── test_food_safety_checker.py
    ├── test_medical_restrictions.py
    ├── test_pet_profile.py
    └── test_nutrition_plan.py
```

### Contratos Clave

```python
# NRCCalculator
def calculate_rer(peso_kg: float) -> float:
    """RER = 70 × peso_kg^0.75"""

def calculate_der(rer: float, factor_edad: float, factor_reproductivo: float,
                  factor_actividad: float, factor_bcs: float) -> float:
    """DER = RER × todos los factores"""

# FoodSafetyChecker
def is_toxic(ingredient_name: str, species: Species) -> tuple[bool, str | None]:
    """Nunca lanza excepción. Determinístico."""

# MedicalRestrictionEngine
def is_restricted(ingredient_name: str,
                  conditions: list[MedicalCondition]) -> tuple[bool, str | None]:
    """Verificación contra RESTRICTIONS_BY_CONDITION."""
```

### Factores NRC

| Etapa | Perro | Gato |
|-------|-------|------|
| Cachorro < 4 meses | 3.0 | 2.5 |
| Cachorro 4-12 meses | 2.0 | 1.8 |
| Adulto (1-7 años) | 1.6 | 1.4 |
| Senior (> 7 años) | 1.4 | 1.2 |

factor_reproductivo: Esterilizado=0.9 · No esterilizado=1.0

factor_actividad Perros: Sedentario=1.2 · Moderado=1.4 · Activo=1.6 · Muy activo=1.8
factor_actividad Gatos: Indoor=1.2 · Indoor/Outdoor=1.4 · Outdoor=1.6

factor_bcs: BCS 1-3=1.2 (aumento) · BCS 4-6=1.0 (mantenimiento) · BCS 7-9=0.8 (reducción)

### Golden Case Sally (BLOQUEANTE)

```python
# French Poodle · 9.6 kg · 8 años · esterilizada · sedentaria · BCS 6/9
# RER esperado: ≈ 396 kcal (±0.5 kcal)
# DER esperado: ≈ 534 kcal (±0.5 kcal)
```

### Definición de Completado

- [ ] `pytest tests/domain/ --cov=backend/domain --cov-fail-under=80` en verde
- [ ] `test_sally_golden_case` pasa con ±0.5 kcal
- [ ] 0 issues HIGH/MEDIUM en `bandit -r backend/domain/`
- [ ] 13 condiciones médicas en RESTRICTIONS_BY_CONDITION
- [ ] TOXIC_DOGS y TOXIC_CATS con al menos: uvas, cebolla, ajo, xilitol, chocolate, macadamia, cafeína, alcohol, aguacate
- [ ] Ninguna dependencia externa en `domain/`

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | Ninguna |
| Bloquea | Todas las demás unidades |

---

## U-02: auth-service

**Fase**: B — Infraestructura de usuarios
**Prioridad**: BLOQUEANTE para pet-service y plan-service
**Estimación**: 4-5 días

### Descripción

Autenticación JWT (access 15min + refresh rotativo), registro y login para owners y vets,
RBAC con roles `owner` / `vet`, y modelo de suscripción freemium con los 4 tiers.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-01 | Registro de owner con email + contraseña |
| US-02 | Login y sesión JWT con refresh rotativo |
| US-03 | Registro de veterinario con datos de clínica |
| US-18 | Límite freemium: 1 plan en tier Free |
| US-19 | Límite freemium: 3 preguntas/día × 3 días en tier Free |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| AuthUseCase | `application/use_cases/auth_use_case.py` |
| PostgreSQLUserRepository | `infrastructure/db/user_repository.py` |
| JWTService | `infrastructure/auth/jwt_service.py` |
| AuthRouter (FastAPI) | `presentation/routers/auth_router.py` |
| RBAC middleware | `presentation/middleware/rbac.py` |
| Pydantic schemas auth | `presentation/schemas/auth_schemas.py` |

### Estructura de Archivos

```
backend/
├── application/
│   ├── interfaces/
│   │   ├── user_repository.py
│   │   └── jwt_service.py
│   └── use_cases/
│       └── auth_use_case.py
├── infrastructure/
│   ├── db/
│   │   ├── models.py
│   │   ├── session.py
│   │   └── user_repository.py
│   └── auth/
│       └── jwt_service.py
├── presentation/
│   ├── routers/
│   │   └── auth_router.py
│   ├── middleware/
│   │   └── rbac.py
│   └── schemas/
│       └── auth_schemas.py
└── main.py

alembic/versions/
└── 001_create_users_table.py

tests/auth/
    ├── test_auth_use_case.py
    ├── test_jwt_service.py
    └── test_auth_router.py
```

### Contratos Clave

```python
async def register(email: str, password: str, role: UserRole,
                   vet_data: VetRegistrationData | None = None) -> TokenResponse: ...

async def login(email: str, password: str) -> TokenResponse: ...

async def refresh(refresh_token: str) -> TokenResponse: ...
```

### Endpoints

| Método | Ruta | Auth |
|--------|------|------|
| POST | `/v1/auth/register` | Público |
| POST | `/v1/auth/login` | Público |
| POST | `/v1/auth/refresh` | Refresh token |
| POST | `/v1/auth/logout` | Bearer token |

### Límites Freemium

```python
TIER_LIMITS = {
    FREE:    { max_pets: 1, max_plans_total: 1, agent_questions_per_day: 3, agent_days_limit: 3 },
    BASICO:  { max_pets: 1, max_plans_per_month: 1, agent_questions_per_day: None },
    PREMIUM: { max_pets: 3, max_plans_per_month: None, agent_questions_per_day: None },
    VET:     { max_pets: None, max_plans_per_month: None, agent_questions_per_day: None },
}
```

### Definición de Completado

- [ ] Endpoints /register, /login, /refresh funcionando
- [ ] JWT access token expira en exactamente 15 minutos
- [ ] Refresh token rotativo — token anterior invalidado
- [ ] RBAC middleware bloquea acceso cruzado de roles
- [ ] Contraseñas almacenadas con bcrypt (nunca plaintext)
- [ ] Bloqueo por 5 intentos fallidos de login (15min)
- [ ] Migración Alembic 001 ejecutada correctamente
- [ ] Tests con cobertura ≥ 80%

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-01 domain-core |
| Bloquea | U-03 pet-service · U-04 plan-service |

---

## U-03: pet-service

**Fase**: C — Datos de mascotas
**Prioridad**: BLOQUEANTE para plan-service
**Estimación**: 5-6 días

### Descripción

CRUD completo de perfiles de mascota (13 campos obligatorios), registro de peso/BCS append-only,
ClinicPet (creada por el vet con owner_name + owner_phone), y reclamación mediante código TTL 30 días.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-04 | Wizard 6 pasos con 13 campos + BCS visual + actividad por especie |
| US-05 | Actualización de peso (append-only, visible en dashboard) |
| US-20 | Vet crea ClinicPet con owner_name + owner_phone |
| US-21 | Owner reclama ClinicPet con código TTL 30 días |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| PetProfileUseCase | `application/use_cases/pet_profile_use_case.py` |
| WeightTrackingUseCase | `application/use_cases/weight_tracking_use_case.py` |
| PetClaimUseCase | `application/use_cases/pet_claim_use_case.py` |
| PostgreSQLPetRepository | `infrastructure/db/pet_repository.py` |
| PostgreSQLClaimCodeRepository | `infrastructure/db/claim_code_repository.py` |
| PetRouter (FastAPI) | `presentation/routers/pet_router.py` |

### Estructura de Archivos

```
backend/
├── application/
│   ├── interfaces/
│   │   ├── pet_repository.py
│   │   ├── weight_repository.py
│   │   └── claim_code_repository.py
│   └── use_cases/
│       ├── pet_profile_use_case.py
│       ├── weight_tracking_use_case.py
│       └── pet_claim_use_case.py
├── infrastructure/db/
│   ├── pet_repository.py
│   ├── weight_repository.py
│   └── claim_code_repository.py
└── presentation/
    ├── routers/pet_router.py
    └── schemas/pet_schemas.py

alembic/versions/
├── 002_create_pets_table.py
├── 003_create_weight_records_table.py
└── 004_create_claim_codes_table.py
```

### Endpoints

| Método | Ruta | Rol |
|--------|------|-----|
| POST | `/v1/pets` | owner |
| GET | `/v1/pets/{id}` | owner / vet |
| PATCH | `/v1/pets/{id}` | owner |
| POST | `/v1/pets/clinic` | vet |
| POST | `/v1/pets/claim` | owner |
| POST | `/v1/pets/{id}/weight` | owner / vet |
| GET | `/v1/pets/{id}/weight` | owner / vet |
| POST | `/v1/pets/{id}/claim-code` | vet |

### Reglas Críticas

1. Límite de mascotas por tier: Free → 1 · Básico → 1 · Premium → 3 · Vet → ilimitadas
2. Talla obligatoria solo para perros — None para gatos
3. activity_level según especie (perros vs. gatos)
4. Condición médica + plan ACTIVE → plan pasa a PENDING_VET
5. medical_conditions y allergies encriptados AES-256
6. Código de reclamación: TTL 30 días, 8 caracteres alfanumérico, uso único

### Definición de Completado

- [ ] Todos los endpoints con JWT + RBAC
- [ ] medical_conditions y allergies encriptados AES-256
- [ ] Límites de tier correctos en create_pet
- [ ] ClinicPet → AppPet preserva historial
- [ ] Código de reclamación: TTL 30 días, uso único
- [ ] Tests ≥ 80% cobertura

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-01 domain-core · U-02 auth-service |
| Bloquea | U-04 plan-service · U-09 mobile-app |

---

## U-04: plan-service

**Fase**: D — Core del negocio
**Prioridad**: CRÍTICA — corazón de la propuesta de valor
**Estimación**: 8-10 días

### Descripción

Generación async de planes nutricionales (job_id + polling), ciclo de vida completo del plan
(máquina de estados), flujo HITL para mascotas con condición médica, set de sustitutos
pre-aprobados, y dashboard clínico del vet.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-06 | Generación de plan para mascota sana → ACTIVE directo |
| US-07 | Generación de plan con condición médica → PENDING_VET |
| US-08 | Ajuste de ingrediente dentro del set pre-aprobado |
| US-09 | Vet aprueba plan con review_date → ACTIVE |
| US-10 | Vet devuelve plan con comentario → PENDING_VET |
| US-16 | Dashboard owner: estado del plan + días activo |
| US-17 | Dashboard vet: todos sus pacientes con estado de plan |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| PlanGenerationUseCase | `application/use_cases/plan_generation_use_case.py` |
| HitlReviewUseCase | `application/use_cases/hitl_review_use_case.py` |
| LLMRouter | `infrastructure/llm/llm_router.py` |
| OpenRouterClient | `infrastructure/llm/openrouter_client.py` |
| PostgreSQLPlanRepository | `infrastructure/db/plan_repository.py` |
| PlanRouter (FastAPI) | `presentation/routers/plan_router.py` |
| VetDashboardRouter | `presentation/routers/vet_dashboard_router.py` |

### Estructura de Archivos

```
backend/
├── application/
│   ├── interfaces/
│   │   ├── plan_repository.py
│   │   ├── job_repository.py
│   │   └── notification_service.py
│   └── use_cases/
│       ├── plan_generation_use_case.py
│       └── hitl_review_use_case.py
├── infrastructure/
│   ├── llm/
│   │   ├── llm_router.py
│   │   └── openrouter_client.py
│   └── db/plan_repository.py
└── presentation/
    ├── routers/plan_router.py
    ├── routers/vet_dashboard_router.py
    └── schemas/plan_schemas.py

alembic/versions/
├── 005_create_plans_table.py
├── 006_create_plan_jobs_table.py
├── 007_create_substitute_sets_table.py
└── 008_create_agent_traces_table.py
```

### LLM Routing (ADR-019)

```python
def route(tier: SubscriptionTier, conditions_count: int) -> str:
    # Free tier                → "meta-llama/llama-3.3-70b"
    # Básico tier              → "openai/gpt-4o-mini"
    # Premium / Vet tier       → "anthropic/claude-sonnet-4-5"
    # 3+ condiciones (any tier)→ "anthropic/claude-sonnet-4-5"  ← override no negociable
```

### Endpoints

| Método | Ruta | Rol |
|--------|------|-----|
| POST | `/v1/plans` | owner / vet |
| GET | `/v1/plans/jobs/{job_id}` | owner / vet |
| GET | `/v1/plans/{id}` | owner / vet |
| PATCH | `/v1/plans/{id}/ingredient` | owner |
| POST | `/v1/plans/{id}/approve` | vet |
| POST | `/v1/plans/{id}/return` | vet |
| GET | `/v1/vet/patients` | vet |
| GET | `/v1/vet/patients/{id}/tracking` | vet |

### Reglas Críticas

1. LLM nunca calcula RER/DER — solo NRCCalculator
2. LLM nunca decide toxicidad — FoodSafetyChecker valida POST-LLM
3. Si LLM genera ingrediente tóxico → rechazar, reintentar max 2 veces → error
4. HITL: mascotas sanas → ACTIVE · con condición → PENDING_VET
5. agent_traces: INSERT only — sin UPDATE
6. Prompts al LLM: solo pet_id UUID, nunca nombre ni especie
7. Plan respuesta incluye 5 secciones (REQ-010 / ADR-020)

### Definición de Completado

- [ ] Golden case Sally: RER ≈ 396, DER ≈ 534 (±0.5 kcal)
- [ ] 0 tóxicos en planes — validación post-LLM siempre activa
- [ ] HITL correcto: sanas → ACTIVE · con condición → PENDING_VET
- [ ] LLM routing según ADR-019 (override 3+ condiciones)
- [ ] Plan devuelve 5 secciones (REQ-010)
- [ ] agent_traces: solo INSERT, sin UPDATE
- [ ] Prompts sin PII (solo pet_id UUID)
- [ ] Tests ≥ 80% cobertura

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-01 · U-02 · U-03 |
| Bloquea | U-05 agent-core · U-08 export-service · U-09 mobile-app |

---

## U-05: agent-core

**Fase**: E — Inteligencia artificial
**Prioridad**: BLOQUEANTE para scanner, conversation, export-service
**Estimación**: 7-9 días

### Descripción

Orquestador central LangGraph con 4 subgrafos especializados. Estado compartido `NutriVetState`.
Implementa Plan Generation Subgraph completo. Stubs para scanner y conversation.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-06 | Subgrafo Plan Generation: plan mascota sana |
| US-07 | Subgrafo Plan Generation: plan con condición médica |
| US-09 | Subgrafo Plan Generation: HITL routing correcto |
| US-12 | Referral Node: detección de emergencia |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| LangGraphOrchestrator | `infrastructure/agent/orchestrator.py` |
| NutriVetState | `infrastructure/agent/state.py` |
| IntentClassifier node | `infrastructure/agent/nodes/intent_classifier.py` |
| Plan Generation Subgraph | `infrastructure/agent/subgraphs/plan_generation.py` |
| Referral Node | `infrastructure/agent/nodes/referral_node.py` |
| HITLRouter node | `infrastructure/agent/nodes/hitl_router.py` |

### Estructura de Archivos

```
backend/infrastructure/agent/
├── orchestrator.py
├── state.py
├── nodes/
│   ├── intent_classifier.py
│   ├── hitl_router.py
│   └── referral_node.py
└── subgraphs/
    ├── plan_generation.py
    ├── consultation.py     # Stub — implementar en U-07
    └── scanner.py          # Stub — implementar en U-06

tests/agent/
    ├── test_orchestrator.py
    ├── test_intent_classifier.py
    ├── test_plan_generation_subgraph.py
    └── test_referral_node.py
```

### NutriVetState

```python
class NutriVetState(TypedDict):
    user_id: str; pet_id: str; user_role: str; subscription_tier: str
    intent: str              # plan_generation / consultation / scanner / referral / emergency
    pet_species: str; pet_conditions: list[str]; conditions_count: int
    plan_modality: str | None; plan_status: str | None; plan_id: str | None
    rer_kcal: float | None; der_kcal: float | None; llm_model_selected: str | None
    conversation_history: list[dict]; user_message: str; agent_response: str | None
    is_emergency: bool; requires_vet_referral: bool
    agent_traces: list[dict]   # append-only
    next_node: str | None; error: str | None
```

### Flujo del Orquestador

```
START → load_pet_context → intent_classifier → [routing condicional]
  "plan_generation" → plan_generation_subgraph → hitl_router → END
  "consultation"    → consultation_subgraph → END  (U-07)
  "scanner"         → scanner_subgraph → END       (U-06)
  "referral"        → referral_node → END
  "emergency"       → referral_node (is_emergency=True) → END
```

### Referral Node

```python
EMERGENCY_KEYWORDS = {
    "convulsión", "desmayo", "no respira", "sangre",
    "envenenamiento", "intoxicación", "trauma", "atropellado", "parálisis"
}
# Detección de emergencia: hard-coded, nunca LLM
# Emergencias no consumen cuota del tier Free
```

### Definición de Completado

- [ ] Orquestador enruta correctamente los 4 intents + emergency
- [ ] Plan Generation Subgraph: RER/DER determinístico (Golden case Sally)
- [ ] Validación de toxicidad post-LLM siempre ejecuta
- [ ] Detección de emergencia por keywords (no LLM)
- [ ] Referral Node: mensaje estructurado con contacto vet
- [ ] Stubs de consultation y scanner listos
- [ ] agent_traces: solo append
- [ ] Tests ≥ 80% cobertura

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-01 domain-core · U-04 plan-service |
| Bloquea | U-06 scanner-service · U-07 conversation-service · U-08 export-service |

---

## U-06: scanner-service

**Fase**: E — Inteligencia artificial (paralelo con U-07 y U-08)
**Prioridad**: CRÍTICA — diferenciador clave
**Estimación**: 5-6 días

### Descripción

Pipeline OCR para etiquetas nutricionales. Acepta imagen de tabla nutricional o lista de ingredientes.
Procesa via OpenRouter (gpt-4o vision) para todos los tiers.
Evalúa resultado contra el perfil de la mascota → semáforo verde/amarillo/rojo.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-13 | Escanear tabla nutricional → semáforo + evaluación vs. perfil mascota |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| Scanner Subgraph | `infrastructure/agent/subgraphs/scanner.py` |
| ImageValidator node | `infrastructure/agent/nodes/image_validator.py` |
| NutritionalProfileEvaluator node | `infrastructure/agent/nodes/nutritional_evaluator.py` |
| Endpoint `/v1/agent/scan` | `presentation/routers/agent_router.py` |

### Flujo del Scanner Subgraph

```
image_validator          ← rechaza logos/marca/empaque frontal
  ↓ (valid)
ocr_extraction           ← OpenRouterClient.complete_with_vision(model="openai/gpt-4o")
  ↓
parse_ocr_output
  ↓
check_toxic_ingredients  ← FoodSafetyChecker (determinístico)
  ↓
check_medical_restrictions ← MedicalRestrictionEngine (determinístico)
  ↓
evaluate_nutritional_fit ← LLM evalúa adecuación calórico + macro
  ↓
generate_semaphore_result → verde / amarillo / rojo + justificación
```

### Reglas Críticas

1. **NUNCA** aceptar imagen de logo, marca o empaque frontal
2. **SIEMPRE** usar `openai/gpt-4o` para OCR — todos los tiers
3. **NUNCA** mostrar nombre de marca en el resultado
4. Rojo: ingrediente tóxico O prohibido por condición médica
5. Amarillo: perfil nutricional subóptimo O alergia potencial
6. Verde: sin tóxicos, sin restricciones, perfil adecuado al DER

### Definición de Completado

- [ ] Imágenes no nutricionales rechazadas
- [ ] OCR siempre usa `openai/gpt-4o`
- [ ] Semáforo rojo para tóxicos y restricciones (determinístico)
- [ ] Nombre de marca nunca aparece en el resultado
- [ ] Tests ≥ 80% cobertura en scanner subgraph

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-05 agent-core |
| Bloquea | U-09 mobile-app |

---

## U-07: conversation-service

**Fase**: E — Inteligencia artificial (paralelo con U-06 y U-08)
**Prioridad**: CRÍTICA — diferenciador de retención y conversión
**Estimación**: 5-6 días

### Descripción

Agente conversacional nutricional. Responde consultas sobre alimentación usando el perfil
de la mascota como contexto. Detecta consultas médicas → remite al vet. Aplica límites freemium.
SSE streaming de tokens. Historial persistente por mascota.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-11 | Consulta nutricional respondida con contexto del perfil |
| US-12 | Detección de emergencia → mensaje de acción urgente |
| US-19 | Gate Free → Básico al agotar 9 preguntas |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| Consultation Subgraph | `infrastructure/agent/subgraphs/consultation.py` |
| QueryClassifier node | `infrastructure/agent/nodes/query_classifier.py` |
| NutritionalResponder node | `infrastructure/agent/nodes/nutritional_responder.py` |
| FreemiumGateChecker | `infrastructure/agent/nodes/freemium_gate.py` |
| PostgreSQLConversationRepository | `infrastructure/db/conversation_repository.py` |

### Flujo del Consultation Subgraph

```
freemium_gate_check
  ↓ (cuota disponible o tier >= Básico)
query_classifier
  ↓
  ├── "nutritional" → nutritional_responder → format_response → SSE stream → END
  └── "medical" / "emergency" → referral_node (U-05) → END
```

### Reglas Críticas (ADR-021)

1. Solo responde consultas nutricionales — jamás diagnósticos o medicamentos
2. Consultas médicas → Referral Node siempre
3. Emergencias NO consumen cuota del tier Free
4. Cuota Free: 3 preguntas/día × 3 días = 9 total
5. Historial persistente por mascota (no por sesión) — últimas 10 conversaciones como contexto
6. SSE streaming: endpoint `POST /v1/agent/chat` → `text/event-stream`
7. System prompt contextualizado con nombre, especie, condiciones y plan de la mascota
8. Respuestas en prosa natural — no listas para preguntas simples

### System Prompt Contextualizado

```
Eres el asistente nutricional de {pet_name}, {species} de {age}.
Condiciones médicas activas: {conditions_summary}.
Plan activo: {plan_type}, {der_kcal} kcal/día, modalidad {plan_modality}.
LÍMITES ABSOLUTOS: síntomas/medicamentos/diagnósticos → derivar al vet siempre.
```

### Definición de Completado

- [ ] Agente nunca responde consultas médicas
- [ ] Cuota Free: 3/día × 3 días → bloqueo correcto
- [ ] Emergencias no consumen cuota
- [ ] Disclaimer incluido en toda respuesta
- [ ] SSE streaming funcional (text/event-stream)
- [ ] Historial persistido por pet_id (no por sesión)
- [ ] Tests ≥ 80% cobertura

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-05 agent-core |
| Bloquea | U-09 mobile-app |

---

## U-08: export-service

**Fase**: E — Inteligencia artificial (paralelo con U-06 y U-07)
**Prioridad**: CRÍTICA — canal de entrega del plan
**Estimación**: 4-5 días

### Descripción

Generación de PDF del plan nutricional activo (WeasyPrint server-side), subida a Cloudflare R2
y pre-signed URL con TTL 1 hora. Solo planes ACTIVE son exportables.

### User Stories

| Story | Descripción |
|-------|-------------|
| US-14 | Exportar plan ACTIVE como PDF con pre-signed URL 1h |
| US-15 | Compartir PDF por WhatsApp / email desde la app |

### Componentes en Scope

| Componente | Archivo |
|-----------|---------|
| ExportPlanUseCase | `application/use_cases/export_plan_use_case.py` |
| PDFGenerator | `infrastructure/pdf/pdf_generator.py` |
| R2StorageClient | `infrastructure/storage/r2_client.py` |
| ExportRouter (FastAPI) | `presentation/routers/export_router.py` |
| Plantilla HTML | `infrastructure/pdf/templates/plan_template.html` |

### Estructura de Archivos

```
backend/
├── application/
│   ├── interfaces/
│   │   ├── pdf_generator.py
│   │   └── storage_client.py
│   └── use_cases/export_plan_use_case.py
├── infrastructure/
│   ├── pdf/
│   │   ├── pdf_generator.py
│   │   └── templates/plan_template.html
│   └── storage/r2_client.py
└── presentation/
    ├── routers/export_router.py
    └── schemas/export_schemas.py
```

### Contratos Clave

```python
async def export_to_pdf(plan_id: UUID, user_id: UUID) -> ExportResult:
    """Solo planes ACTIVE. Genera PDF, sube a R2, retorna presigned URL 1h."""

class ExportResult(BaseModel):
    download_url: str     # Cloudflare R2 presigned URL
    expires_at: datetime  # now + 1 hora
    plan_id: UUID
```

### Contenido Obligatorio del PDF

- Nombre y especie de la mascota
- DER en kcal/día
- Plan completo (ingredientes + porciones + instrucciones)
- Sustitutos aprobados
- Protocolo de transición (si aplica)
- Vet que aprobó + fecha (si aplica)
- Disclaimer completo en todas las páginas

### Reglas Críticas

1. Solo planes ACTIVE exportables — otro estado → PlanNotActiveError
2. Disclaimer obligatorio en el PDF — nunca omitir
3. R2 key: `pdfs/{plan_id}/{content_hash}.pdf` (cache-friendly)
4. Exportación gratuita para todos los tiers

### Definición de Completado

- [ ] Endpoint `/v1/plans/{id}/export` funcional
- [ ] Solo planes ACTIVE exportables
- [ ] Disclaimer en todos los PDFs generados
- [ ] Pre-signed URL con TTL 1 hora
- [ ] PDF subido a R2 con key `pdfs/{plan_id}/{hash}.pdf`
- [ ] Tests ≥ 80% cobertura

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | U-04 plan-service · U-05 agent-core |
| Bloquea | U-09 mobile-app |

---

## U-09: mobile-app

**Fase**: F — Interfaz móvil
**Prioridad**: ENTREGA FINAL — consume todas las APIs del backend
**Estimación**: 14-16 días

### Descripción

Aplicación Flutter (iOS + Android) que consume todas las APIs del backend. Offline-first con Hive.
Riverpod para gestión de estado. GoRouter para navegación por rol.

### User Stories Cubiertas

US-01 a US-21 (todas)

### Screens en Scope

| Screen | Archivo |
|--------|---------|
| AuthScreen | `lib/features/auth/screens/auth_screen.dart` |
| WizardScreen | `lib/features/pet/screens/wizard_screen.dart` |
| ClinicPetWizardScreen | `lib/features/pet/screens/clinic_pet_wizard_screen.dart` |
| PlanScreen | `lib/features/plan/screens/plan_screen.dart` |
| ChatScreen | `lib/features/agent/screens/chat_screen.dart` |
| OCRScreen | `lib/features/scanner/screens/ocr_screen.dart` |
| DashboardScreen | `lib/features/dashboard/screens/dashboard_screen.dart` |
| VetDashboardScreen | `lib/features/vet/screens/vet_dashboard_screen.dart` |
| UpgradeGateScreen | `lib/features/freemium/screens/upgrade_gate_screen.dart` |
| ClaimCodeScreen | `lib/features/pet/screens/claim_code_screen.dart` |

### Stack Flutter

```yaml
flutter_riverpod: ^2.x      # Estado global async
dio: ^5.x                    # HTTP client + JWT interceptors
go_router: ^13.x             # Navegación por rol
hive_flutter: ^1.x           # Offline cache
image_picker: ^1.x           # OCR camera
fl_chart: ^0.x               # Gráficas peso/BCS
share_plus: ^7.x             # Share sheet nativo
flutter_secure_storage: ^9.x # JWT storage cifrado
http: ^1.x                   # SSE streaming chat
flutter_animate: ^4.x        # Typing indicator + animaciones
```

### UX Crítica

**WizardScreen**:
- Talla: visible solo si especie == perro
- Nivel actividad: opciones según especie
- BCS: selector visual con imágenes de silueta (1-9)
- Draft en Hive entre pasos

**PlanScreen — 5 secciones colapsables (ADR-020)**:
- ⚠️ Sección 1 — Alimentos Prohibidos: siempre expandida al abrir
- 🔄 Sección 2 — Protocolo de Transición: si plan es nuevo
- 🏥 Sección 3 — Cuidados de Salud: por condición + señales de alerta
- 📅 Sección 4 — Plan por Días: tabs Lun→Dom; desayuno/almuerzo/cena/snack
- 📊 Sección 5 — Resumen Nutricional: macros vs. requerimiento NRC

**ChatScreen — Agente Fluido (ADR-021)**:
- Header: mascota activa siempre visible
- SSE streaming: tokens progresivos + typing indicator
- Chips contextuales bajo respuestas
- Historial persistente por mascota
- Contador de preguntas (tier Free)

### Flujos Offline (Hive)

| Dato | Estrategia |
|------|-----------|
| Wizard en progreso | Draft en Hive — nunca enviado hasta completar 13 campos |
| Plan activo | Cacheado en Hive — disponible offline |
| Historial de chat | Últimas 50 conversaciones en Hive |
| Dashboard | Snapshot del último sync |
| JWT tokens | flutter_secure_storage cifrado |

### Definición de Completado

- [ ] Login/registro funcional para owner y vet
- [ ] Wizard: 13 campos con draft en Hive
- [ ] PlanScreen: 5 secciones colapsables (ADR-020)
- [ ] Sección 1 siempre expandida al abrir
- [ ] ChatScreen: SSE streaming tokens en tiempo real (ADR-021)
- [ ] Polling job_id con timeout 60s + skeleton
- [ ] Gate de upgrade funcional en Free
- [ ] OCRScreen con semáforo
- [ ] Dashboard con fl_chart (peso/BCS)
- [ ] VetDashboard con flujo HITL completo
- [ ] Share sheet nativo con presigned URL
- [ ] Offline: plan y chat disponibles sin conexión

### Dependencias

| Tipo | Detalle |
|------|---------|
| Depende de | Todas las unidades U-01..U-08 |
| Bloquea | Piloto BAMPYSVET (OPERATIONS) |
