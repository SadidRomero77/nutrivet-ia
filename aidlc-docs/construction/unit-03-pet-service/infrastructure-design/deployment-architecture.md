# Deployment Architecture — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Ubicación en el Deployment

El pet service es parte del monolito modular `nutrivet-backend` en Hetzner CPX31.

```
Hetzner CPX31 (Ashburn VA)
└── Coolify (Docker orchestrator)
    └── nutrivet-backend (Docker container, puerto 8000)
        ├── presentation/pets/
        │   ├── router.py          ← /pets CRUD + /claim
        │   └── schemas.py         ← CreatePetRequest, UpdatePetRequest, PetResponse
        ├── application/pets/
        │   ├── pet_profile_use_case.py
        │   ├── weight_tracking_use_case.py
        │   └── pet_claim_use_case.py
        ├── infrastructure/pets/
        │   ├── pg_pet_repository.py    ← SQLAlchemy async
        │   ├── encrypted_fields.py     ← AES-256 para condiciones médicas
        │   └── pg_weight_repository.py
        └── domain/entities/
            └── pet_profile.py
```

## PostgreSQL Schema

```sql
CREATE TABLE pets (
    pet_id UUID PRIMARY KEY,
    owner_id UUID NOT NULL REFERENCES users(user_id),
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(20) NOT NULL CHECK (especie IN ('perro','gato')),
    raza VARCHAR(100) NOT NULL,
    sexo VARCHAR(20) NOT NULL,
    edad_valor INT NOT NULL,
    edad_unidad VARCHAR(10) NOT NULL,
    peso_kg DECIMAL(5,2) NOT NULL CHECK (peso_kg > 0),
    talla VARCHAR(20) NULL,
    estado_reproductivo VARCHAR(30) NOT NULL,
    nivel_actividad VARCHAR(30) NOT NULL,
    bcs INT NOT NULL CHECK (bcs BETWEEN 1 AND 9),
    condiciones_medicas_encrypted BYTEA NULL,  -- AES-256
    alergias JSONB NOT NULL DEFAULT '[]',
    alimentacion_actual VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE weight_records (
    record_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    peso_kg DECIMAL(5,2) NOT NULL CHECK (peso_kg > 0),
    bcs INT NOT NULL CHECK (bcs BETWEEN 1 AND 9),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    recorded_by UUID NOT NULL REFERENCES users(user_id),
    notes TEXT NULL
);

CREATE TABLE claim_codes (
    claim_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    vet_id UUID NOT NULL REFERENCES users(user_id),
    code VARCHAR(10) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    is_used BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_by UUID NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE clinic_pets (
    clinic_pet_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    vet_id UUID NOT NULL REFERENCES users(user_id),
    linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (pet_id, vet_id)
);

CREATE INDEX idx_pets_owner ON pets(owner_id) WHERE is_active = TRUE;
CREATE INDEX idx_weight_pet ON weight_records(pet_id, recorded_at DESC);
```

## Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/nutrivet
AES_ENCRYPTION_KEY=<32-byte base64 key>  # Para AES-256, nunca en código
```
