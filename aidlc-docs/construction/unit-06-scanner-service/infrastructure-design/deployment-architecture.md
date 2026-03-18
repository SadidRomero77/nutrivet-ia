# Deployment Architecture — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Deployment del Scanner Service

```
Hetzner CPX31 (Ashburn VA)
└── Coolify
    ├── nutrivet-backend (FastAPI, puerto 8000)
    │   ├── presentation/scanner/
    │   │   ├── router.py          ← POST /scanner/scan, GET /scanner/scans/{scan_id}
    │   │   └── schemas.py         ← ScanRequest, ScanResponse
    │   ├── application/scanner/
    │   │   └── scan_use_case.py   ← ScannerSubgraph orchestration
    │   └── infrastructure/scanner/
    │       ├── r2_storage_client.py   ← Upload/download Cloudflare R2
    │       ├── openrouter_ocr_client.py ← gpt-4o vision via OpenRouter
    │       └── pg_scan_repository.py
    │
    ├── Cloudflare R2 (object storage, externo)
    │   └── bucket: nutrivet-scans
    │       └── scans/{owner_id}/{scan_id}.{ext}
    │
    └── PostgreSQL
        └── label_scans, product_evaluations tables
```

## PostgreSQL Schema

```sql
CREATE TABLE label_scans (
    scan_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    owner_id UUID NOT NULL REFERENCES users(user_id),
    image_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    r2_image_key VARCHAR(500) NULL,
    raw_ocr_text TEXT NULL,
    error_message TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL
);

CREATE TABLE product_evaluations (
    evaluation_id UUID PRIMARY KEY,
    scan_id UUID NOT NULL REFERENCES label_scans(scan_id),
    overall_score DECIMAL(3,2) NULL,
    semaphore VARCHAR(10) NOT NULL,
    findings JSONB NOT NULL DEFAULT '[]',
    toxic_ingredients_found JSONB NOT NULL DEFAULT '[]',
    restricted_ingredients_found JSONB NOT NULL DEFAULT '[]',
    missing_nutrients JSONB NOT NULL DEFAULT '[]',
    excess_nutrients JSONB NOT NULL DEFAULT '[]',
    recommendation TEXT NULL,
    protein_pct DECIMAL(5,2) NULL,
    fat_pct DECIMAL(5,2) NULL,
    fiber_pct DECIMAL(5,2) NULL,
    moisture_pct DECIMAL(5,2) NULL,
    ingredients JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scans_pet ON label_scans(pet_id, created_at DESC);
```

## Cloudflare R2 Configuration

```env
R2_ACCOUNT_ID=<cloudflare_account_id>
R2_ACCESS_KEY_ID=<r2_access_key>
R2_SECRET_ACCESS_KEY=<r2_secret_key>
R2_BUCKET_NAME=nutrivet-scans
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
```

## Ciclo de Vida de Imágenes en R2

```
Upload al escanear       → scans/{owner_id}/{scan_id}.jpg
Retención: 90 días       → purge job mensual (ARQ cron)
Post-purge: solo metadata en PostgreSQL permanece
```
