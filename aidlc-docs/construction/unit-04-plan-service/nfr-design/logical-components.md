# Logical Components — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Plan Service

### PlanGenerationUseCase
**Responsabilidad**: Enqueue del job de generación y gestión del ciclo de vida del plan.
**Capa**: application/plans/
**Dependencias**: PlanJobRepositoryPort, ARQQueuePort, PetRepositoryPort, TierLimitsChecker
**Métodos**:
```
request_plan(pet_id, owner_id, modalidad, tier) → PlanJob
get_job_status(job_id, owner_id) → PlanJob
get_plan(plan_id, requester_id) → NutritionPlan
list_plans_by_pet(pet_id, owner_id) → list[NutritionPlan]
```

### HitlReviewUseCase
**Responsabilidad**: Flujos de firma, aprobación y devolución de planes por vet.
**Capa**: application/plans/
**Dependencias**: PlanRepositoryPort, ClinicPetRepositoryPort, NotificationPort
**Métodos**:
```
approve_plan(plan_id, vet_id, review_date?) → NutritionPlan
return_plan_with_comment(plan_id, vet_id, comment) → NutritionPlan
list_pending_plans(vet_id) → list[NutritionPlan]
```

### PlanGenerationWorker (ARQ)
**Responsabilidad**: Ejecución del pipeline completo de generación: NRC → LLM → validate → persist.
**Capa**: workers/
**Dependencias**: NRCCalculator, LLMRouter, OpenRouterClient, FoodSafetyChecker, MedicalRestrictionEngine, PlanRepository, AgentTraceRepository
**Función principal**: `generate_plan_worker(ctx, job_id) → None`

### OpenRouterClient
**Responsabilidad**: Llamadas HTTP a OpenRouter con retry y timeout.
**Capa**: infrastructure/plans/
**Dependencias**: httpx, tenacity
**Implementa**: LLMClientPort

### PostgreSQLPlanRepository
**Responsabilidad**: Persistencia de NutritionPlan y PlanSections.
**Capa**: infrastructure/plans/
**Implementa**: PlanRepositoryPort

### PostgreSQLAgentTraceRepository
**Responsabilidad**: Insert-only de AgentTrace.
**Capa**: infrastructure/plans/
**Regla**: No tiene método update() ni delete().

### PlansRouter
**Responsabilidad**: Endpoints HTTP del plan service.
**Capa**: presentation/plans/
**Endpoints**:
```
POST   /plans/generate              → 202 { job_id }
GET    /plans/jobs/{job_id}         → 200 PlanJob
GET    /plans/{plan_id}             → 200 NutritionPlan
GET    /pets/{pet_id}/plans         → 200 list[NutritionPlan]
PATCH  /plans/{plan_id}/approve     → 200 NutritionPlan (vet only)
PATCH  /plans/{plan_id}/return      → 200 NutritionPlan (vet only)
GET    /vet/pending-plans           → 200 list[NutritionPlan] (vet only)
```

## Diagrama de Dependencias

```
PlansRouter (presentation)
    ↓
PlanGenerationUseCase / HitlReviewUseCase (application)
    ↓
PlanJobRepositoryPort ←── PostgreSQLPlanJobRepository
PlanRepositoryPort    ←── PostgreSQLPlanRepository
ARQQueuePort          ←── ARQQueue (Redis)
NotificationPort      ←── FCMClient
    ↓ (en worker)
NRCCalculator         (domain)
LLMRouter             (domain)
FoodSafetyChecker     (domain)
MedicalRestrictionEngine (domain)
OpenRouterClient      (infrastructure) → OpenRouter API
AgentTraceRepository  (infrastructure) → PostgreSQL
```

## Manejo de Errores del Worker

| Error | Acción | Job Status |
|-------|--------|------------|
| Ingrediente tóxico detectado | Stop, no persistir plan | "failed" |
| LLM timeout (60s) | Retry × 2, luego fallback model | "failed" si persiste |
| Restricción médica violada | Re-prompt × 2 | "failed" si persiste |
| OpenRouter 429/500 | Retry con exponential backoff | "failed" si agota reintentos |
| NRC error (peso inválido) | Error inmediato, no retry | "failed" |
