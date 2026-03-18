# Deployment Architecture — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Deployment del Plan Service

```
Hetzner CPX31 (Ashburn VA)
└── Coolify (Docker orchestrator)
    ├── nutrivet-backend (contenedor FastAPI, puerto 8000)
    │   ├── presentation/plans/router.py    ← endpoints HTTP
    │   ├── application/plans/
    │   │   ├── plan_generation_use_case.py
    │   │   └── hitl_review_use_case.py
    │   └── infrastructure/plans/
    │       ├── openrouter_client.py
    │       ├── pg_plan_repository.py
    │       └── pg_agent_trace_repository.py
    │
    ├── nutrivet-worker (contenedor ARQ, mismo Docker image)
    │   └── workers/plan_worker.py         ← ejecuta generate_plan_worker()
    │
    ├── Redis (contenedor, puerto 6379)    ← broker de ARQ + job state
    │
    └── PostgreSQL (contenedor, puerto 5432) ← plans, plan_jobs, agent_traces
```

## PostgreSQL Schema del Plan Service

```sql
CREATE TABLE nutrition_plans (
    plan_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    owner_id UUID NOT NULL REFERENCES users(user_id),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING_VET',
    modalidad VARCHAR(20) NOT NULL,
    plan_type VARCHAR(30) NOT NULL DEFAULT 'estandar',
    rer_kcal DECIMAL(8,2) NOT NULL,
    der_kcal DECIMAL(8,2) NOT NULL,
    llm_model_used VARCHAR(100) NOT NULL,
    review_date DATE NULL,
    vet_id UUID NULL REFERENCES users(user_id),
    vet_comment TEXT NULL,
    disclaimer TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL
);

CREATE TABLE plan_sections (
    section_id UUID PRIMARY KEY,
    plan_id UUID NOT NULL REFERENCES nutrition_plans(plan_id),
    "order" INT NOT NULL CHECK ("order" BETWEEN 1 AND 5),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    UNIQUE (plan_id, "order")
);

CREATE TABLE plan_jobs (
    job_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    owner_id UUID NOT NULL REFERENCES users(user_id),
    modalidad VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    arq_job_id VARCHAR(100) NULL,
    result_plan_id UUID NULL REFERENCES nutrition_plans(plan_id),
    error_message TEXT NULL,
    enqueued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL
);

CREATE TABLE agent_traces (
    trace_id UUID PRIMARY KEY,
    plan_id UUID NULL REFERENCES nutrition_plans(plan_id),
    pet_id UUID NOT NULL,              -- UUID anónimo, nunca nombre
    llm_model VARCHAR(100) NOT NULL,
    prompt_tokens INT NOT NULL,
    completion_tokens INT NOT NULL,
    latency_ms INT NOT NULL,
    node_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    -- SIN columnas actualizables: append-only
);

-- Trigger que previene UPDATE en agent_traces
CREATE RULE no_update_agent_traces AS ON UPDATE TO agent_traces DO INSTEAD NOTHING;

CREATE INDEX idx_plans_pet ON nutrition_plans(pet_id);
CREATE INDEX idx_plans_status ON nutrition_plans(status) WHERE status IN ('PENDING_VET','ACTIVE');
CREATE INDEX idx_plan_jobs_owner ON plan_jobs(owner_id, status);
```

## Variables de Entorno

```env
REDIS_URL=redis://localhost:6379
OPENROUTER_API_KEY=<api_key>  # NUNCA en código
ARQ_MAX_JOBS=10
PLAN_GENERATION_TIMEOUT_S=60
```
