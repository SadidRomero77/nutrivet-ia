# Deployment Architecture — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Deployment del Export Service

```
Hetzner CPX31 (Ashburn VA)
└── Coolify
    ├── nutrivet-backend (FastAPI, puerto 8000)
    │   ├── presentation/exports/
    │   │   ├── router.py          ← POST /plans/{id}/export, GET /exports/{id}/url
    │   │   └── schemas.py         ← ExportResponse
    │   ├── application/exports/
    │   │   └── export_plan_use_case.py
    │   └── infrastructure/exports/
    │       ├── pdf_generator.py         ← WeasyPrint server-side
    │       ├── r2_export_client.py      ← boto3 para R2
    │       └── pg_export_repository.py
    │
    ├── Cloudflare R2 (object storage externo)
    │   └── bucket: nutrivet-exports
    │       └── exports/{owner_id}/{plan_id}/{export_id}.pdf
    │
    └── PostgreSQL
        └── export_results table
```

## PostgreSQL Schema

```sql
CREATE TABLE export_results (
    export_id UUID PRIMARY KEY,
    plan_id UUID NOT NULL REFERENCES nutrition_plans(plan_id),
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    owner_id UUID NOT NULL REFERENCES users(user_id),
    r2_key VARCHAR(500) NOT NULL,
    presigned_url TEXT NOT NULL,
    url_expires_at TIMESTAMPTZ NOT NULL,
    file_size_bytes INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exports_plan ON export_results(plan_id, created_at DESC);
CREATE INDEX idx_exports_owner ON export_results(owner_id);
```

## Cloudflare R2 — Bucket de Exports

```env
R2_EXPORTS_BUCKET=nutrivet-exports
# Mismas credenciales R2 que el scanner service
```

Estructura de objetos:
```
nutrivet-exports/
└── exports/
    └── {owner_uuid}/
        └── {plan_uuid}/
            ├── {export_id_1}.pdf  (primera exportación)
            └── {export_id_2}.pdf  (segunda exportación del mismo plan)
```

## Dependencias del Export Service en el Container

WeasyPrint requiere dependencias del sistema operativo:

```dockerfile
# Dockerfile — sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

## Variables de Entorno

```env
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_EXPORTS_BUCKET=nutrivet-exports
R2_ENDPOINT_URL=
PDF_PRESIGNED_URL_TTL_SECONDS=3600
```
