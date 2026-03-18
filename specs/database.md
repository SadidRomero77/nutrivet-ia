# DATABASE-SPEC.md — NutriVet.IA PostgreSQL v2
> Esquema completo con perfil de usuario ampliado, perfil clínico de mascota,
> dos modalidades de dieta, sistema de sponsors y trazabilidad completa.
> Basado en estándares NRC/AAFCO y validación clínica veterinaria.

---

## Esquema completo

```sql
-- ════════════════════════════════════════
-- USUARIOS Y AUTENTICACIÓN
-- ════════════════════════════════════════
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'vet', 'admin')),
    full_name VARCHAR(255) NOT NULL,
    city VARCHAR(100),                         -- ciudad de residencia
    country VARCHAR(100),                      -- país de residencia
    professional_card VARCHAR(50),             -- solo para vets (COMVEZCOL)
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════
-- MASCOTAS — Perfil clínico completo
-- ════════════════════════════════════════
CREATE TABLE pets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    species VARCHAR(10) NOT NULL CHECK (species IN ('dog', 'cat')),
    breed VARCHAR(100) NOT NULL DEFAULT 'mestizo',
    sex VARCHAR(10) NOT NULL CHECK (sex IN ('male', 'female')),
    age_years DECIMAL(4,1) NOT NULL CHECK (age_years >= 0),
    weight_kg DECIMAL(5,2) NOT NULL CHECK (weight_kg > 0),

    -- Clasificación por tamaño corporal
    -- mini    = < 5 kg   (chihuahua, toy poodle)
    -- small   = 5-10 kg  (french poodle, beagle)
    -- medium  = 10-25 kg (labrador joven, border collie)
    -- large   = 25-45 kg (labrador adulto, golden)
    -- giant   = > 45 kg  (gran danés, mastín)
    size VARCHAR(10) CHECK (size IN ('mini', 'small', 'medium', 'large', 'giant')),

    -- Estado reproductivo
    reproductive_status VARCHAR(20) DEFAULT 'unknown'
        CHECK (reproductive_status IN ('sterilized', 'intact', 'unknown')),

    -- Nivel de actividad física
    -- Para perros: none / low / moderate / high / very_high
    -- Para gatos: indoor / outdoor
    activity_level VARCHAR(20) DEFAULT 'low',

    -- Condición corporal BCS (Body Condition Score) Escala 1-9 NRC/AAFCO
    -- 1-3 : Bajo peso / Delgado (costillas y vértebras visibles)
    -- 4-5 : Peso ideal (costillas palpables con ligera cobertura)
    -- 6-7 : Sobrepeso (costillas difíciles de palpar)
    -- 8-9 : Obesidad grave (depósitos de grasa evidentes)
    body_condition_score SMALLINT CHECK (body_condition_score BETWEEN 1 AND 9),

    -- Estado fisiológico especial
    physiological_state VARCHAR(30) DEFAULT 'normal'
        CHECK (physiological_state IN (
            'normal', 'pregnant', 'lactating', 'puppy', 'senior', 'geriatric'
        )),

    photo_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════
-- ANTECEDENTES MÉDICOS (Multi-condición por mascota)
-- ════════════════════════════════════════
CREATE TABLE medical_conditions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    registered_by_vet_id UUID REFERENCES users(id),   -- null si lo registra owner
    registered_by_role VARCHAR(20) NOT NULL,           -- 'owner' o 'vet'

    condition_code VARCHAR(30) NOT NULL CHECK (condition_code IN (
        'diabetic',          -- Diabetes Mellitus
        'hypothyroid',       -- Hipotiroidismo
        'cancer',            -- Antecedentes cancerígenos
        'articular',         -- Problemas articulares / artrosis
        'renal',             -- Enfermedad renal crónica
        'hepatic',           -- Hepatopatía / Hiperlipidemia / Hipercolesterolemia
        'pancreatic',        -- Pancreatitis / Enfermedad pancreática exocrina
        'neurodegenerative', -- Síndrome cognitivo / neurodegenerativo
        'dental',            -- Enfermedad periodontal / problemas bucales
        'skin',              -- Dermatitis / problemas de piel
        'gastric',           -- Gastritis / Síndrome de mala absorción
        'cardiac',           -- Enfermedad cardíaca
        'food_allergy'       -- Alergias alimentarias (ver pet_food_allergies)
    )),

    -- Solo para condition_code = 'cancer' — campo obligatorio en ese caso
    cancer_location_encrypted BYTEA,               -- cifrado AES-256

    severity VARCHAR(20) CHECK (severity IN ('mild', 'moderate', 'severe')),
    notes_encrypted BYTEA,                          -- notas clínicas, AES-256
    dietary_restrictions JSONB DEFAULT '[]',        -- restricciones específicas adicionales
    is_active BOOLEAN DEFAULT TRUE,
    diagnosed_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════
-- ALERGIAS ALIMENTARIAS
-- ════════════════════════════════════════
CREATE TABLE pet_food_allergies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    allergen_code VARCHAR(50) NOT NULL,      -- referencia a allergen_reference.code
    allergen_name VARCHAR(100) NOT NULL,
    confirmed BOOLEAN DEFAULT FALSE,          -- TRUE si confirmado por test alérgenos
    unknown_flag BOOLEAN DEFAULT FALSE,       -- TRUE si owner eligió "no sabe"
    owner_accepted_risk BOOLEAN DEFAULT FALSE, -- TRUE si aceptó disclaimer de responsabilidad
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Catálogo de alérgenos frecuentes para perros y gatos (seed data)
CREATE TABLE allergen_reference (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name_es VARCHAR(100) NOT NULL,
    species VARCHAR(10) CHECK (species IN ('dog', 'cat', 'both')) DEFAULT 'both',
    frequency VARCHAR(10) DEFAULT 'common' CHECK (frequency IN ('common', 'occasional', 'rare'))
);
-- Seed: pollo, res, cerdo, cordero, pescado, huevo, trigo, maíz, soja,
--       lácteos, arroz, avena, papa, yuca

-- ════════════════════════════════════════
-- ALIMENTOS
-- ════════════════════════════════════════
CREATE TABLE foods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    name_normalized VARCHAR(200) NOT NULL,    -- lowercase sin acentos para búsqueda
    category VARCHAR(50),
    -- 'protein' / 'carb' / 'vegetable' / 'fruit' / 'supplement' / 'snack'
    source VARCHAR(20) DEFAULT 'usda'
        CHECK (source IN ('usda', 'local', 'commercial')),
    usda_id VARCHAR(50),

    -- Valores nutricionales por 100g
    kcal_per_100g DECIMAL(8,2),
    protein_g DECIMAL(8,2),
    fat_g DECIMAL(8,2),
    carbs_g DECIMAL(8,2),
    fiber_g DECIMAL(8,2),
    calcium_mg DECIMAL(8,2),
    phosphorus_mg DECIMAL(8,2),
    sodium_mg DECIMAL(8,2),
    omega3_mg DECIMAL(8,2),

    -- Toxicidad
    toxicity_dogs VARCHAR(20) DEFAULT 'safe'
        CHECK (toxicity_dogs IN ('safe', 'caution', 'high_risk', 'toxic')),
    toxicity_cats VARCHAR(20) DEFAULT 'safe'
        CHECK (toxicity_cats IN ('safe', 'caution', 'high_risk', 'toxic')),
    toxicity_notes TEXT,
    safe_alternatives JSONB DEFAULT '[]',

    -- Restricciones por condición médica
    -- Ej: {"diabetic": "forbidden", "hepatic": "caution", "renal": "limit_50pct"}
    condition_restrictions JSONB DEFAULT '{}',

    validated_by_vet BOOLEAN DEFAULT FALSE,
    is_common_allergen BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════
-- PLANES NUTRICIONALES
-- ════════════════════════════════════════
CREATE TABLE nutrition_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id),
    created_by_user_id UUID NOT NULL REFERENCES users(id),

    -- Modalidad elegida por el usuario al iniciar el plan
    modality VARCHAR(20) NOT NULL CHECK (modality IN ('natural', 'concentrate')),

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN (
            'DRAFT',       -- generado, pendiente de revisión
            'PENDING_VET', -- requiere firma veterinaria (condición médica presente)
            'ACTIVE',      -- aprobado y vigente
            'MODIFIED',    -- ajustado por owner después de activación
            'REJECTED',    -- rechazado por vet con notas
            'BLOCKED',     -- bloqueado por toxicidad o restricción crítica
            'ARCHIVED'     -- histórico / reemplazado por versión nueva
        )),

    -- Contenido del plan (generado por agente + validado por reglas)
    plan_content JSONB NOT NULL,
    -- modalidad 'natural':
    -- { daily_kcal, meals_per_day, macros_per_meal:{protein_g, carbs_g, vegetables_g},
    --   approved_proteins, approved_carbs, approved_vegetables, approved_fruits,
    --   forbidden_foods, preparation_notes, snacks,
    --   transition_protocol, emergency_protocol, supplements_reference, disclaimer }
    -- modalidad 'concentrate':
    -- { daily_kcal, ideal_profile:{protein_pct_min, fat_pct_max, fiber_pct_min},
    --   must_have_ingredients, avoid_ingredients, food_type,
    --   meals_per_day, sponsored_options, transition_protocol, disclaimer }

    -- Requerimientos nutricionales calculados (determinista)
    nutritional_requirements JSONB NOT NULL,
    -- { rer_kcal, der_kcal, factor, protein_g_day, fat_g_day,
    --   carbs_g_day, fiber_g_day, water_ml_day }

    -- Firma veterinaria (solo cuando status = ACTIVE con condición médica)
    vet_signature JSONB,
    -- { vet_id, professional_card, signed_at, notes }

    block_reason TEXT,
    rejection_notes TEXT,

    version INTEGER NOT NULL DEFAULT 1,
    parent_plan_id UUID REFERENCES nutrition_plans(id),  -- trazabilidad de versiones

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Historial de cambios del plan (inmutable — append only)
CREATE TABLE plan_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES nutrition_plans(id),
    changed_by_user_id UUID NOT NULL REFERENCES users(id),
    change_type VARCHAR(50) NOT NULL,
    -- 'created', 'modality_selected', 'ingredient_added', 'ingredient_removed',
    -- 'kcal_adjusted', 'vet_signed', 'vet_rejected', 'owner_confirmed_risk',
    -- 'blocked', 'archived'
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    change_details JSONB,
    triggered_alert BOOLEAN DEFAULT FALSE,
    alert_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════
-- ESCANEOS OCR
-- ════════════════════════════════════════
CREATE TABLE label_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id UUID NOT NULL REFERENCES pets(id),
    user_id UUID NOT NULL REFERENCES users(id),
    image_s3_key VARCHAR(500) NOT NULL,

    -- Tipo de imagen aceptada (NUNCA marca/logo/empaque frontal)
    image_type VARCHAR(30) DEFAULT 'nutritional_table'
        CHECK (image_type IN ('nutritional_table', 'ingredients_list')),

    -- Valores extraídos por GPT-4o Vision
    extracted_values JSONB,
    -- { protein_pct, fat_pct, carbs_pct, fiber_pct, moisture_pct,
    --   phosphorus_mg_100g, sodium_mg_100g,
    --   ingredients_ordered: ["pollo", "arroz", "maíz", ...] }

    -- Evaluación vs perfil del paciente
    adequacy VARCHAR(20) CHECK (adequacy IN ('adequate', 'caution', 'not_recommended')),
    concerns JSONB DEFAULT '[]',     -- problemas encontrados con el producto
    positives JSONB DEFAULT '[]',    -- aspectos positivos
    recommendation TEXT,             -- texto para el usuario
    confidence DECIMAL(3,2),         -- confianza del OCR 0.0-1.0

    created_at TIMESTAMPTZ DEFAULT NOW()
    -- Las imágenes en Cloudflare R2 se eliminan a los 90 días (lifecycle rule)
);

-- ════════════════════════════════════════
-- SISTEMA DE SPONSORS (Concentrados Comerciales)
-- ════════════════════════════════════════
CREATE TABLE sponsors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_name VARCHAR(200) NOT NULL,
    brand_logo_url VARCHAR(500),
    contact_info JSONB,                  -- { email, phone, website }

    -- Perfil nutricional del producto que el sponsor ofrece
    nutritional_profile JSONB NOT NULL,
    -- { protein_pct_min, fat_pct_max, fiber_pct_min,
    --   main_protein_source, food_type: "dry|wet|mixed",
    --   life_stage: ["adult", "senior", "puppy"] }

    -- Condiciones médicas para las que aplica
    suitable_conditions VARCHAR(30)[] DEFAULT '{}',
    contraindicated_conditions VARCHAR(30)[] DEFAULT '{}',

    -- Verificación veterinaria OBLIGATORIA antes de activar
    verified_by_vet_id UUID NOT NULL REFERENCES users(id),
    verified_at TIMESTAMPTZ,

    disclosure_text VARCHAR(200) DEFAULT 'Contenido patrocinado',
    sponsored_since TIMESTAMPTZ DEFAULT NOW(),
    sponsored_until TIMESTAMPTZ,         -- null = vigencia indefinida
    is_active BOOLEAN DEFAULT FALSE,     -- activar explícitamente post-verificación
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ════════════════════════════════════════
-- OBSERVABILIDAD (Trazas del agente LangGraph)
-- ════════════════════════════════════════
CREATE TABLE agent_traces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trace_id UUID UNIQUE NOT NULL,
    job VARCHAR(60) NOT NULL,
    -- 'generate_plan_natural', 'generate_concentrate_profile',
    -- 'scan_label', 'validate_toxicity', 'validate_allergies'
    pet_id UUID REFERENCES pets(id),
    user_role VARCHAR(20),
    modality VARCHAR(20),
    final_status VARCHAR(20),
    latency_ms INTEGER,
    total_tokens_input INTEGER,
    total_tokens_output INTEGER,
    estimated_cost_usd DECIMAL(10,6),
    tool_calls JSONB DEFAULT '[]',       -- [{name, duration_ms, status}]
    output_schema_valid BOOLEAN,
    rbac_violations INTEGER DEFAULT 0,
    toxicity_checks INTEGER DEFAULT 0,
    allergy_checks INTEGER DEFAULT 0,
    hitl_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Índices

```sql
CREATE INDEX idx_pets_owner     ON pets(owner_id) WHERE is_active = TRUE;
CREATE INDEX idx_pets_species   ON pets(species, owner_id);
CREATE INDEX idx_conditions_pet ON medical_conditions(pet_id) WHERE is_active = TRUE;
CREATE INDEX idx_allergies_pet  ON pet_food_allergies(pet_id);
CREATE INDEX idx_plans_pet      ON nutrition_plans(pet_id, status);
CREATE INDEX idx_plans_pending  ON nutrition_plans(status) WHERE status = 'PENDING_VET';
CREATE INDEX idx_plans_modality ON nutrition_plans(modality, status);
CREATE INDEX idx_foods_name     ON foods(name_normalized);
CREATE INDEX idx_foods_toxicity ON foods(toxicity_dogs, toxicity_cats);
CREATE INDEX idx_foods_allergen ON foods(is_common_allergen) WHERE is_common_allergen = TRUE;
CREATE INDEX idx_changes_plan   ON plan_changes(plan_id, created_at DESC);
CREATE INDEX idx_scans_pet      ON label_scans(pet_id, created_at DESC);
CREATE INDEX idx_sponsors_active ON sponsors(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_traces_job     ON agent_traces(job, created_at DESC);
CREATE INDEX idx_tokens_hash    ON refresh_tokens(token_hash) WHERE revoked_at IS NULL;
```

---

## Datos Semilla (Seed Data)

### Alérgenos de referencia
```sql
INSERT INTO allergen_reference (code, name_es, species, frequency) VALUES
  ('chicken',  'Pollo',           'both', 'common'),
  ('beef',     'Res / Carne vacuna', 'both', 'common'),
  ('pork',     'Cerdo',           'both', 'common'),
  ('lamb',     'Cordero',         'both', 'occasional'),
  ('fish',     'Pescado',         'both', 'occasional'),
  ('egg',      'Huevo',           'both', 'common'),
  ('wheat',    'Trigo',           'both', 'common'),
  ('corn',     'Maíz',            'both', 'common'),
  ('soy',      'Soja',            'both', 'common'),
  ('dairy',    'Lácteos',         'both', 'common'),
  ('rice',     'Arroz',           'both', 'occasional'),
  ('oats',     'Avena',           'both', 'rare'),
  ('potato',   'Papa',            'both', 'rare'),
  ('cassava',  'Yuca',            'dog',  'rare');
```

---

## Reglas de Migración

- NUNCA `DROP COLUMN` en producción sin periodo de deprecación
- NUNCA `ALTER COLUMN` que cambie tipo sin migración de datos
- Siempre `alembic revision --autogenerate` — nunca SQL manual
- Cada migración tiene `upgrade()` y `downgrade()`
- Datos médicos cifrados (AES-256) antes de insertar
- Columnas `_encrypted` son BYTEA — nunca texto plano
- Migrations en staging antes de producción

---

## Configuración del Pool de Conexiones

```python
# app/infrastructure/db/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    # Pool sizing: proceso persistente Uvicorn (2 workers)
    # DB_POOL_SIZE configurable via env var — default 10
    pool_size=10,
    max_overflow=20,      # Conexiones extra bajo pico de carga
    pool_timeout=30,      # Esperar hasta 30s si el pool está lleno antes de fallar
    pool_recycle=3600,    # Reciclar conexiones cada hora (proceso persistente — no Lambda)
    pool_pre_ping=True,   # Verificar conexión antes de usar
    echo=settings.environment == "development",  # Log SQL solo en desarrollo
)

AsyncSession = async_sessionmaker(
    engine,
    expire_on_commit=False,  # No expirar objetos al hacer commit (mejor UX en async)
)

async def get_db():
    """Dependency de FastAPI para obtener sesión de base de datos."""
    async with AsyncSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Consideración para escala:** Con proceso persistente Uvicorn el pool nativo es suficiente.
Si se agregan múltiples réplicas del contenedor backend, considerar PgBouncer:
```
# Con PgBouncer: múltiples instancias pueden compartir un pool centralizado
# Configurar en docker-compose como servicio adicional en Hetzner
DATABASE_URL=postgresql+asyncpg://user:pass@pgbouncer:5432/nutrivet
```

---

## Roles de Base de Datos (Principio de Mínimo Privilegio)

Separación estricta de roles. El runtime de la aplicación nunca tiene permisos DDL.

```sql
-- ==================================================
-- ROLES DE BASE DE DATOS
-- ==================================================

-- Rol para el runtime de FastAPI (operaciones CRUD únicas)
CREATE ROLE nutrivet_app WITH LOGIN PASSWORD '${APP_DB_PASSWORD}';
GRANT CONNECT ON DATABASE nutrivet TO nutrivet_app;
GRANT USAGE ON SCHEMA public TO nutrivet_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO nutrivet_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO nutrivet_app;
-- nutrivet_app NO tiene: DROP, ALTER, TRUNCATE, CREATE

-- Rol para migraciones Alembic (solo usado en CI/CD, nunca en runtime)
CREATE ROLE nutrivet_migrations WITH LOGIN PASSWORD '${MIGRATIONS_DB_PASSWORD}';
GRANT CONNECT ON DATABASE nutrivet TO nutrivet_migrations;
GRANT ALL PRIVILEGES ON SCHEMA public TO nutrivet_migrations;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nutrivet_migrations;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nutrivet_migrations;

-- Rol solo lectura (analytics, dashboards de observabilidad, BI)
CREATE ROLE nutrivet_readonly WITH LOGIN PASSWORD '${READONLY_DB_PASSWORD}';
GRANT CONNECT ON DATABASE nutrivet TO nutrivet_readonly;
GRANT USAGE ON SCHEMA public TO nutrivet_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO nutrivet_readonly;

-- Revocar permisos del rol público (PostgreSQL predeterminado)
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE nutrivet FROM PUBLIC;
```

**Variables de entorno por rol:**
```bash
# .env — runtime FastAPI
DATABASE_URL=postgresql+asyncpg://nutrivet_app:${APP_DB_PASSWORD}@host:5432/nutrivet

# Solo en CI/CD pipeline (GitHub Secrets) — nunca en runtime
DATABASE_MIGRATIONS_URL=postgresql://nutrivet_migrations:${MIGRATIONS_DB_PASSWORD}@host:5432/nutrivet

# Para dashboards de observabilidad — nunca expuesto a internet
DATABASE_READONLY_URL=postgresql://nutrivet_readonly:${READONLY_DB_PASSWORD}@host:5432/nutrivet
```

---

## Tablas Adicionales

Requeridas por BACKEND-SPEC.md (async jobs, push tokens, idempotencia):

```sql
-- ==================================================
-- JOBS ASÍNCRONOS (generación de planes con LLM)
-- ==================================================
CREATE TABLE async_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_type VARCHAR(50) NOT NULL
        CHECK (job_type IN ('generate_plan', 'scan_label')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    related_id UUID,                              -- plan_id cuando job_type = 'generate_plan'
    progress_pct SMALLINT DEFAULT 0
        CHECK (progress_pct BETWEEN 0 AND 100),
    error_code VARCHAR(30),                       -- NV-LLM-001, NV-TOXICITY-001
    error_message TEXT,
    idempotency_key VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);
CREATE INDEX idx_jobs_user_status ON async_jobs(user_id, status, created_at DESC);
CREATE INDEX idx_jobs_active ON async_jobs(status, created_at)
    WHERE status IN ('pending', 'processing');
CREATE INDEX idx_jobs_expires ON async_jobs(expires_at)
    WHERE status = 'completed'; -- Para limpieza periódica

-- ==================================================
-- TOKENS PUSH (FCM - Firebase Cloud Messaging)
-- ==================================================
CREATE TABLE push_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE,
    platform VARCHAR(10) NOT NULL CHECK (platform IN ('ios', 'android')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_push_tokens_user ON push_tokens(user_id);

-- ==================================================
-- IDEMPOTENCIA (prevenir planes duplicados)
-- ==================================================
CREATE TABLE idempotency_keys (
    key VARCHAR(100) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    endpoint VARCHAR(100) NOT NULL,
    response_body JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);
CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);

-- ==================================================
-- CONSENTIMIENTO INFORMADO (Ley 1581/2012 Colombia)
-- ==================================================
CREATE TABLE user_consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type VARCHAR(50) NOT NULL
        CHECK (consent_type IN ('data_processing', 'medical_data', 'marketing', 'allergy_risk')),
    consented BOOLEAN NOT NULL,
    consent_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    ip_address_hash VARCHAR(64),  -- hash SHA-256 de la IP, nunca IP en texto plano
    user_agent VARCHAR(500),
    consented_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_consents_user ON user_consents(user_id, consent_type);
```

---

## Índices JSONB Adicionales

```sql
-- Índice GIN para búsquedas en plan_content
-- Permite: WHERE plan_content @> '{"modality": "natural"}'
CREATE INDEX idx_plans_content_gin ON nutrition_plans USING GIN (plan_content);

-- Índice GIN para restricciones por condición médica en foods
-- Permite: WHERE condition_restrictions @> '{"diabetic": "forbidden"}'
CREATE INDEX idx_foods_conditions_gin ON foods USING GIN (condition_restrictions);

-- Índice GIN para tool_calls en agent_traces (consultas de observabilidad)
CREATE INDEX idx_traces_tools_gin ON agent_traces USING GIN (tool_calls);

-- Índice GIN para sponsors por condiciones adecuadas (array PostgreSQL)
CREATE INDEX idx_sponsors_conditions_gin ON sponsors USING GIN (suitable_conditions);
CREATE INDEX idx_sponsors_contraindicated_gin ON sponsors USING GIN (contraindicated_conditions);

-- Índice parcial para planes que requieren revisión vet (dashboard veterinario)
CREATE INDEX idx_plans_pending_vet ON nutrition_plans(created_at DESC)
    WHERE status = 'PENDING_VET';

-- Índice para búsqueda de alimentos seguros por categoría
CREATE INDEX idx_foods_safe_by_category ON foods(category, name_normalized)
    WHERE toxicity_dogs NOT IN ('toxic', 'high_risk')
    AND toxicity_cats NOT IN ('toxic', 'high_risk');

-- Índice para trazabilidad de versiones de planes
CREATE INDEX idx_plans_versions ON nutrition_plans(parent_plan_id, version)
    WHERE parent_plan_id IS NOT NULL;
```

---

## Particionamiento de Tablas de Alta Escritura

`agent_traces` acumulará millones de registros en meses. Se particiona por mes:

```sql
-- Convertir agent_traces a tabla particionada por rango de fecha
CREATE TABLE agent_traces (
    id UUID NOT NULL,
    trace_id UUID UNIQUE NOT NULL,
    job VARCHAR(60) NOT NULL,
    pet_id UUID,           -- No REFERENCES en tablas particionadas (limitación PostgreSQL)
    user_role VARCHAR(20),
    modality VARCHAR(20),
    final_status VARCHAR(20),
    latency_ms INTEGER,
    total_tokens_input INTEGER,
    total_tokens_output INTEGER,
    estimated_cost_usd DECIMAL(10,6),
    tool_calls JSONB DEFAULT '[]',
    output_schema_valid BOOLEAN,
    rbac_violations INTEGER DEFAULT 0,
    toxicity_checks INTEGER DEFAULT 0,
    allergy_checks INTEGER DEFAULT 0,
    hitl_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Crear particiones mensuales (crear con antelación en job mensual)
CREATE TABLE agent_traces_2026_03 PARTITION OF agent_traces
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE agent_traces_2026_04 PARTITION OF agent_traces
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
-- (continuar mes a mes)

-- Índice en cada partición se hereda automáticamente
CREATE INDEX ON agent_traces(job, created_at DESC);
CREATE INDEX ON agent_traces USING GIN (tool_calls);

-- Política de retención: DROP PARTITION después de 90 días
-- (más eficiente que DELETE fila por fila)
-- Job mensual via ARQ scheduled task (cron):
DROP TABLE IF EXISTS agent_traces_2025_12; -- partición > 90 días
```

**Alternativa MVP** (si no se implementa particionamiento aún):
```sql
-- agent_traces sin particionamiento + purge manual cada 90 días
CREATE INDEX idx_traces_created ON agent_traces(created_at DESC);

-- ARQ cron mensual (cron_tasks en WorkerSettings):
DELETE FROM agent_traces
WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## Constraints de Integridad Adicionales

```sql
-- Solo vets pueden tener tarjeta profesional registrada
ALTER TABLE users ADD CONSTRAINT chk_vet_professional_card
    CHECK (role != 'vet' OR professional_card IS NOT NULL);

-- cancer_location es obligatorio cuando condición = cancer
ALTER TABLE medical_conditions ADD CONSTRAINT chk_cancer_location_required
    CHECK (condition_code != 'cancer' OR cancer_location_encrypted IS NOT NULL);

-- Un sponsor debe estar verificado por vet antes de activarse
ALTER TABLE sponsors ADD CONSTRAINT chk_sponsor_verified_before_active
    CHECK (is_active = FALSE OR (verified_by_vet_id IS NOT NULL AND verified_at IS NOT NULL));

-- plan_content nunca puede ser JSONB vacío
ALTER TABLE nutrition_plans ADD CONSTRAINT chk_plan_content_not_empty
    CHECK (plan_content != '{}' AND jsonb_typeof(plan_content) = 'object');

-- El progreso de un job debe ser 0-100
ALTER TABLE async_jobs ADD CONSTRAINT chk_job_progress
    CHECK (progress_pct BETWEEN 0 AND 100);

-- Confianza OCR en rango válido
ALTER TABLE label_scans ADD CONSTRAINT chk_confidence_range
    CHECK (confidence IS NULL OR confidence BETWEEN 0.0 AND 1.0);

-- Peso de mascota en rango fisiológicamente posible
ALTER TABLE pets ADD CONSTRAINT chk_weight_reasonable
    CHECK (weight_kg BETWEEN 0.1 AND 200.0);
```

---

## Estrategia de Backup y Recuperación

```yaml
# PostgreSQL en Docker (Hetzner + Coolify) — configuración de backups
BackupRetentionDays: 7         # Coolify automático diario → Cloudflare R2 (/backups/postgres/)
PreferredBackupWindow: "03:00-04:00"  # UTC — baja actividad LATAM
RestartPolicy: always          # Docker restart:always — recuperación automática ante fallo

# RTO (Recovery Time Objective): < 1 hora
# RPO (Recovery Point Objective): < 24 horas (frecuencia de backup automático)
```

**Prueba de backup mensual:**
```bash
# Restaurar snapshot en instancia temporal para verificar integridad
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier nutrivet-restore-test \
  --db-snapshot-identifier <latest-snapshot>
# Ejecutar queries de verificación
# Eliminar instancia temporal
aws rds delete-db-instance --db-instance-identifier nutrivet-restore-test --skip-final-snapshot
```
