# Plan: Code Generation — Unit 04: plan-service

**Unidad**: unit-04-plan-service
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar el plan-service completo con TDD: generación asíncrona (ARQ), máquina de
estados, HITL review, sustitución de ingredientes, LLM routing determinístico y
agent_traces append-only.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.
**Bloqueante**: Golden case Sally debe pasar antes de cualquier merge.

---

## Pasos de Implementación

### Paso 1 — Estructura de Carpetas

- [ ] `backend/application/llm/llm_router.py` — LLMRouter determinístico
- [ ] `backend/application/interfaces/plan_repository.py` — IPlanRepository ABC
- [ ] `backend/application/interfaces/plan_job_repository.py` — IPlanJobRepository ABC
- [ ] `backend/application/interfaces/agent_trace_repository.py` — IAgentTraceRepository ABC (sin update)
- [ ] `backend/application/use_cases/plan_generation_use_case.py`
- [ ] `backend/application/use_cases/hitl_review_use_case.py`
- [ ] `backend/application/use_cases/ingredient_substitution_use_case.py`
- [ ] `backend/infrastructure/llm/openrouter_client.py`
- [ ] `backend/infrastructure/workers/plan_generation_worker.py` (ARQ)
- [ ] `backend/infrastructure/db/plan_repository.py`
- [ ] `backend/infrastructure/db/agent_trace_repository.py`
- [ ] `backend/presentation/routers/plan_router.py`
- [ ] `backend/presentation/schemas/plan_schemas.py`
- [ ] `tests/plan/test_llm_router.py` (vacío)
- [ ] `tests/plan/test_plan_generation_use_case.py` (vacío)
- [ ] `tests/plan/test_hitl_review_use_case.py` (vacío)

### Paso 2 — Tests RED: Golden Case Sally (BLOQUEANTE)

- [ ] Escribir en `tests/domain/test_nrc_calculator.py`:
  - `test_golden_case_sally_rer` — `calculate_rer(9.6) ≈ 396 kcal (±0.5)` — BLOQUEANTE
  - `test_golden_case_sally_der` — `calculate_der(rer=396, ...) ≈ 534 kcal (±0.5)` — BLOQUEANTE
- [ ] Verificar que fallan (RED) — deben haber pasado ya en unit-01, si no → STOP

### Paso 3 — Tests RED: LLM Router

- [ ] Escribir `tests/plan/test_llm_router.py`:
  - `test_free_tier_0_cond_llama` — free + 0 condiciones → llama-3.3-70b
  - `test_basico_tier_gpt4o_mini` — básico + 1 condición → gpt-4o-mini
  - `test_premium_tier_claude` — premium + 2 condiciones → claude-sonnet-4-5
  - `test_llm_router_3_condiciones_override` — free + 3 condiciones → claude-sonnet-4-5
  - `test_llm_router_5_condiciones_override` — free + 5 condiciones → claude-sonnet-4-5
  - `test_llm_router_es_determinista` — mismo input → mismo output siempre
- [ ] Verificar que todos FALLAN (RED)

### Paso 4 — Tests RED: Plan Generation Use Case

- [ ] Escribir `tests/plan/test_plan_generation_use_case.py`:
  - `test_plan_sano_active_directo` — mascota sin condición → plan ACTIVE sin HITL
  - `test_plan_condicion_pending_vet` — mascota con condición → PENDING_VET
  - `test_toxico_en_output_rechaza_plan` — mock LLM retorna tóxico → job FAILED
  - `test_ajuste_dentro_set_no_hitl` — sustituto en set → ACTIVE
  - `test_ajuste_fuera_set_pending_vet` — sustituto fuera → PENDING_VET
  - `test_free_tier_segundo_plan_falla` → 403
  - `test_agent_traces_inmutables` — no existe update() en IAgentTraceRepository
  - `test_job_polling_ready` — job QUEUED → PROCESSING → READY con plan_id

### Paso 5 — Tests RED: HITL Review

- [ ] Escribir `tests/plan/test_hitl_review_use_case.py`:
  - `test_vet_aprueba_plan_standard` → ACTIVE
  - `test_vet_aprueba_con_review_date_temporal_medical` → ACTIVE + review_date
  - `test_vet_aprueba_temporal_sin_review_date_falla` → 422
  - `test_vet_devuelve_requiere_comentario` — comentario vacío → 422
  - `test_vet_devuelve_con_comentario` → PENDING_VET + comentario visible
  - `test_owner_no_puede_aprobar_plan` → 403
  - `test_vet_ajeno_no_puede_aprobar` → 403
- [ ] Verificar que todos FALLAN (RED)

### Paso 6 — GREEN: LLMRouter y OpenRouterClient

- [ ] Implementar `LLMRouter.select_model(tier, conditions_count)` — determinístico
- [ ] Implementar `OpenRouterClient`:
  - `generate(prompt, model, system_prompt)` — async, timeout 30s
  - Retry × 2 con backoff exponencial (2s, 4s)
  - Fallback a modelo inferior si falla tras 3 intentos
  - Registra latencia y tokens en retorno
- [ ] Verificar que tests LLMRouter PASAN

### Paso 7 — GREEN: Plan Generation Use Case

- [ ] Implementar `IPlanRepository` y `IPlanJobRepository` ABC
- [ ] Implementar `IAgentTraceRepository` ABC (sin update())
- [ ] Implementar `PlanGenerationUseCase`:
  - `enqueue(request, user)` → crea PlanJob + encola en ARQ
  - `get_job(job_id, user_id)` → retorna status del job
- [ ] Implementar `HitlReviewUseCase`:
  - `approve(plan_id, vet_id, review_date?)` → ACTIVE
  - `return_to_owner(plan_id, vet_id, comment)` → PENDING_VET + comentario

### Paso 8 — ARQ Worker: PlanGenerationWorker

- [ ] Implementar `infrastructure/workers/plan_generation_worker.py`:
  - Paso 1: Carga PetProfile desde DB
  - Paso 2: Calcula RER/DER (NRCCalculator — domain, no LLM)
  - Paso 3: Obtiene restricciones (MedicalRestrictionEngine)
  - Paso 4: Valida alergias
  - Paso 5: Selecciona modelo (LLMRouter)
  - Paso 6: Genera plan con LLM (OpenRouterClient)
  - Paso 7: Valida output — FoodSafetyChecker (post-LLM)
  - Paso 8: Genera sustitutos aprobados (substitute_set)
  - Paso 9: Determina HITL (requires_vet_review)
  - Paso 10: Persiste plan + 5 secciones + agent_trace
  - Paso 11: Actualiza job READY + plan_id / FAILED + error

### Paso 9 — Alembic Migrations

- [ ] `alembic revision -m "006_plans"` → plans + plan_sections
- [ ] `alembic revision -m "007_plan_jobs"` → plan_jobs
- [ ] `alembic revision -m "008_substitute_sets"` → substitute_sets
- [ ] `alembic revision -m "009_agent_traces"` → agent_traces (sin updated_at)
- [ ] Revisar migraciones — verificar que `agent_traces` NO tiene `updated_at`
- [ ] Confirmar con Sadid antes de `alembic upgrade head` en staging

### Paso 10 — FastAPI Endpoints (9 endpoints)

- [ ] `POST /v1/plans/generate` — encola job, retorna job_id
- [ ] `GET /v1/plans/jobs/{job_id}` — polling status
- [ ] `GET /v1/plans/{plan_id}` — obtener plan con 5 secciones
- [ ] `GET /v1/plans` — listar planes del owner
- [ ] `PATCH /v1/plans/{plan_id}/approve` — HITL approve (vet only)
- [ ] `PATCH /v1/plans/{plan_id}/return` — HITL return (vet only)
- [ ] `GET /v1/plans/{plan_id}/substitutes` — listar substitute set
- [ ] `POST /v1/plans/{plan_id}/substitutes` — solicitar sustitución
- [ ] `GET /v1/vet/plans/pending` — lista PENDING_VET para vet dashboard

### Paso 11 — Plan Response con 5 Secciones (ADR-020)

- [ ] Implementar schema `PlanResponse` con 5 secciones anidadas
- [ ] Verificar que sección 4 (transición) solo aparece si `has_transition_protocol=True`
- [ ] Verificar que nombre del vet aparece en respuesta si plan fue aprobado

### Paso 12 — Cobertura y Calidad

- [ ] `pytest --cov=backend/application tests/plan/ --cov-fail-under=80`
- [ ] `ruff check backend/` → 0 errores
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM
- [ ] Golden case Sally pasa: RER ≈ 396, DER ≈ 534 (±0.5)
- [ ] Test de golden set: 0 tóxicos en 60 casos

---

## Criterios de Done

- [ ] Golden case Sally pasa en CI (BLOQUEANTE)
- [ ] 0 tóxicos en planes generados (golden set 60 casos)
- [ ] HITL correcto: mascotas sanas → ACTIVE, con condición → PENDING_VET
- [ ] LLM routing por ADR-019: override 3+ condiciones funcional
- [ ] agent_traces append-only — no existe endpoint ni método update()
- [ ] Generación asíncrona funcional (POST → job_id → polling → plan)
- [ ] 9 endpoints funcionales con tests
- [ ] Cobertura ≥ 80%, ruff + bandit sin errores

## Tiempo Estimado

6-7 días (TDD completo + ARQ worker + LLM integration)

## Dependencias

- Unit 01: NRCCalculator, FoodSafetyChecker, MedicalRestrictionEngine, NutritionPlan aggregate
- Unit 02: JWT middleware, RBAC
- Unit 03: PetProfile (para cargar datos en worker)

## Referencias

- Unit spec: `inception/units/unit-04-plan-service.md`
- ADR-019, ADR-020, ADR-022
- Business logic model: `_shared/business-logic-model.md`
- Constitution: REGLA 1, 2, 3, 4, 5, 6
