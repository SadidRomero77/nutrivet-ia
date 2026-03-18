# Plan: Infrastructure Design — Unit 04: plan-service

**Unidad**: unit-04-plan-service
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| PlanRouter (FastAPI) | Contenedor Docker — FastAPI + Uvicorn en Hetzner CPX31 |
| PlanGenerationWorker | ARQ worker — mismo contenedor o contenedor worker separado |
| LLMRouter | `application/llm/llm_router.py` — determinístico, sin red |
| OpenRouterClient | `infrastructure/llm/openrouter_client.py` — httpx async |
| PlanGenerationUseCase | `application/use_cases/plan_generation_use_case.py` |
| HitlReviewUseCase | `application/use_cases/hitl_review_use_case.py` |
| IngredientSubstitutionUseCase | `application/use_cases/ingredient_substitution_use_case.py` |

### Storage — Tablas PostgreSQL

**Tabla `plans`**:
```sql
CREATE TABLE plans (
    plan_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID REFERENCES pets(pet_id),
    owner_id        UUID REFERENCES users(user_id),
    assigned_vet_id UUID REFERENCES users(user_id) NULL,
    status          VARCHAR(20) NOT NULL,   -- PENDING_VET / ACTIVE / UNDER_REVIEW / ARCHIVED
    plan_type       VARCHAR(30) NOT NULL,   -- estandar / temporal_medical / life_stage
    modality        VARCHAR(20) NOT NULL,   -- natural / concentrado
    rer_kcal        NUMERIC(8,2) NOT NULL,
    der_kcal        NUMERIC(8,2) NOT NULL,
    llm_model_used  VARCHAR(100),
    has_transition_protocol BOOLEAN DEFAULT FALSE,
    review_date     DATE NULL,             -- solo temporal_medical
    vet_comment     TEXT NULL,
    approved_at     TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

**Tabla `plan_sections`** (5 secciones por plan — ADR-020):
```sql
CREATE TABLE plan_sections (
    section_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID REFERENCES plans(plan_id),
    section_number  SMALLINT NOT NULL,  -- 1-5
    section_type    VARCHAR(30) NOT NULL,
    content_json    JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_plan_sections_plan_id ON plan_sections(plan_id, section_number);
```

**Tabla `plan_jobs`**:
```sql
CREATE TABLE plan_jobs (
    job_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID REFERENCES pets(pet_id),
    owner_id        UUID REFERENCES users(user_id),
    status          VARCHAR(20) DEFAULT 'QUEUED',  -- QUEUED / PROCESSING / READY / FAILED
    plan_id         UUID NULL,
    error_code      VARCHAR(50) NULL,
    error_message   TEXT NULL,
    enqueued_at     TIMESTAMP DEFAULT NOW(),
    started_at      TIMESTAMP NULL,
    completed_at    TIMESTAMP NULL
);
```

**Tabla `substitute_sets`**:
```sql
CREATE TABLE substitute_sets (
    set_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID REFERENCES plans(plan_id),
    original_ingredient VARCHAR(200) NOT NULL,
    approved_substitutes JSONB NOT NULL,  -- lista de sustitutos aprobados
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**Tabla `agent_traces`** (append-only):
```sql
CREATE TABLE agent_traces (
    trace_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID NOT NULL,   -- anónimo, sin FK para evitar JOIN accidental
    plan_id         UUID NULL,
    model_used      VARCHAR(100) NOT NULL,
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    latency_ms      INTEGER,
    result          VARCHAR(20) NOT NULL,  -- success / failed
    error_code      VARCHAR(50) NULL,
    parent_trace_id UUID NULL,   -- referencia a traza original si es corrección
    created_at      TIMESTAMP DEFAULT NOW()
    -- SIN updated_at — append-only por diseño
);
```

### Alembic Migrations

```
006_plans.py           → tablas plans + plan_sections + índices
007_plan_jobs.py       → tabla plan_jobs
008_substitute_sets.py → tabla substitute_sets
009_agent_traces.py    → tabla agent_traces (sin updated_at)
```

### Queue — Redis (ARQ)

- **Instancia**: Redis Docker en Hetzner CPX31 (mismo host).
- **Config ARQ**: `max_jobs=10` por worker — si cola > 50 jobs → agregar réplica.
- **Queue name**: `nutrivet_plan_generation`.
- **Job TTL en Redis**: 24 horas (resultados en DB, no en Redis).

### LLM — OpenRouter

- **Proveedor unificado**: un solo cliente HTTP para todos los modelos.
- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`.
- **Autenticación**: `Authorization: Bearer ${OPENROUTER_API_KEY}`.
- **Timeout**: 30s por request LLM.

### Variables de Entorno Requeridas

```bash
OPENROUTER_API_KEY=<clave de OpenRouter>
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrivet
# No se requiere R2 en esta unidad — export-service maneja PDFs
```

## Notas Arquitecturales

1. **R2 no requerido**: Esta unidad no genera PDFs. El export-service (unit-08) maneja R2.

2. **agent_traces sin FK a pets**: La tabla `agent_traces` usa `pet_id` como UUID
   pero sin foreign key — esto es intencional para evitar JOINs accidentales que
   podrían exponer datos de mascota junto con traces de LLM.

3. **ARQ vs Celery**: ARQ se eligió por su simplicidad con async Python y Redis
   (ADR-022). Si se necesita mayor escala → migrar a Celery sin cambiar el domain.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- ADR-019: LLM routing + OpenRouter
- ADR-020: estructura 5 secciones del plan
- ADR-022: async jobs con ARQ
