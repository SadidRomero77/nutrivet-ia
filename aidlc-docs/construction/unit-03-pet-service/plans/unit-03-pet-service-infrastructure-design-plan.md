# Plan: Infrastructure Design — Unit 03: pet-service

**Unidad**: unit-03-pet-service
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| PetRouter (FastAPI) | Contenedor Docker — FastAPI + Uvicorn en Hetzner CPX31 |
| PetProfileUseCase | `application/use_cases/pet_profile_use_case.py` |
| WeightTrackingUseCase | `application/use_cases/weight_tracking_use_case.py` |
| PetClaimUseCase | `application/use_cases/pet_claim_use_case.py` |
| PostgreSQLPetRepository | `infrastructure/db/pet_repository.py` |
| PostgreSQLWeightRepository | `infrastructure/db/weight_repository.py` |
| PostgreSQLClaimCodeRepository | `infrastructure/db/claim_code_repository.py` |

**Servidor**: Hetzner CPX31 — co-ubicado con el backend FastAPI principal.

### Storage — Tablas PostgreSQL

**Tabla `pets`**:
```sql
CREATE TABLE pets (
    pet_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID REFERENCES users(user_id),
    vet_id          UUID REFERENCES users(user_id) NULL,  -- NULL si es AppPet sin vet
    name            VARCHAR(100) NOT NULL,
    species         VARCHAR(10) NOT NULL,          -- perro / gato
    breed           VARCHAR(100),
    sex             VARCHAR(10) NOT NULL,
    age_months      INTEGER NOT NULL,
    weight_kg       NUMERIC(5,2) NOT NULL,
    size            VARCHAR(20),                   -- solo perros
    reproductive_status VARCHAR(20) NOT NULL,
    activity_level  VARCHAR(20) NOT NULL,
    bcs             SMALLINT NOT NULL,
    medical_conditions BYTEA,                      -- AES-256 encrypted JSONB
    allergies       BYTEA,                         -- AES-256 encrypted JSONB
    current_feeding VARCHAR(20) NOT NULL,
    is_clinic_pet   BOOLEAN DEFAULT FALSE,
    owner_name      VARCHAR(200),                  -- solo ClinicPet
    owner_phone     VARCHAR(50),                   -- solo ClinicPet
    claimed_at      TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

**Tabla `weight_records`**:
```sql
CREATE TABLE weight_records (
    record_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID REFERENCES pets(pet_id),
    weight_kg       NUMERIC(5,2) NOT NULL,
    bcs             SMALLINT,
    recorded_by     UUID REFERENCES users(user_id),
    recorded_at     TIMESTAMP DEFAULT NOW()
    -- SIN updated_at — append-only
);
CREATE INDEX idx_weight_records_pet_id ON weight_records(pet_id, recorded_at DESC);
```

**Tabla `claim_codes`**:
```sql
CREATE TABLE claim_codes (
    code            VARCHAR(8) PRIMARY KEY,
    pet_id          UUID REFERENCES pets(pet_id),
    created_by_vet  UUID REFERENCES users(user_id),
    expires_at      TIMESTAMP NOT NULL,            -- creacion + 30 días
    used_at         TIMESTAMP NULL,
    used_by         UUID REFERENCES users(user_id) NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_claim_codes_pet_id ON claim_codes(pet_id);
```

### Alembic Migrations

```
003_pets.py           → tabla pets con todos sus campos
004_weight_records.py → tabla weight_records + índice
005_claim_codes.py    → tabla claim_codes + índice
```

### Variables de Entorno Requeridas

```bash
# Encriptación de datos médicos — AES-256 via Fernet
FERNET_KEY=<generado con Fernet.generate_key() — guardar en Hetzner secrets>
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrivet
```

### Servicios Externos

**Ninguno** para esta unidad. No requiere LLM, R2, ni Redis.
- La generación del claim code es local (Python `secrets.token_urlsafe`).
- El cifrado es local (Python `cryptography.fernet`).

## Notas Arquitecturales

1. **BYTEA vs JSONB**: Los campos `medical_conditions` y `allergies` se almacenan
   como `BYTEA` (bytes encriptados) en lugar de `JSONB` nativo. La desencriptación
   ocurre en el repository antes de retornar al application layer.

2. **Rotación de clave Fernet**: Si el `FERNET_KEY` necesita rotarse, usar
   `MultiFernet([new_key, old_key])` para migración gradual sin downtime.

3. **ClinicPet vs AppPet**: La misma tabla `pets` alberga ambos tipos.
   `is_clinic_pet=True` + `owner_id=NULL` indica ClinicPet sin claim.
   Post-claim: `owner_id` se actualiza con el UUID del owner que reclamó.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- Unit spec: `inception/units/unit-03-pet-service.md`
- Constitution: REGLA 6 (AES-256 en reposo)
