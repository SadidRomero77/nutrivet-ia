# DEPLOY-SPEC.md — NutriVet.IA en Hetzner + Coolify
> Decisión documentada en ADR-022. Reemplaza la arquitectura AWS anterior.
> Stack: Hetzner CPX31 + Coolify + Cloudflare R2 + Cloudflare DNS/CDN

---

## Arquitectura de Despliegue

```
GitHub repo (github.com/sadid/nutrivet-ai)
    │
    ├── Push a develop → GitHub Actions CI → si pasan gates → Coolify deploy staging
    └── Push a main   → GitHub Actions CI → aprobación manual → Coolify deploy prod

                          ┌────────────────────────────────────┐
                          │  CLOUDFLARE                         │
                          │  DNS: api.nutrivet.app → Hetzner IP│
                          │  CDN: assets + PDFs (R2)            │
                          │  SSL/TLS: en el edge                │
                          └────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  HETZNER CPX31 — Ashburn VA — $13 USD/mes                                │
│  4 vCPU AMD · 8 GB RAM · 160 GB SSD · 20 TB tráfico                      │
│                                                                           │
│  COOLIFY gestiona:                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  nutrivet-backend  (FastAPI + Uvicorn)  :8000 → Caddy → :443    │    │
│  │  nutrivet-worker   (ARQ worker Python)                           │    │
│  │  PostgreSQL 16     (Docker — red privada)                        │    │
│  │  Redis 7           (Docker — red privada)                        │    │
│  │  Caddy             (reverse proxy + Let's Encrypt SSL)           │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                           │
│  Firewall Hetzner:  solo puertos 22 (SSH IP restringida), 80, 443        │
└──────────────────────────────────────────────────────────────────────────┘
         │
         │ boto3 con R2 endpoint
         ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  CLOUDFLARE R2                                                            │
│  /scans/{id}/image.jpg   · /pdfs/{id}/{hash}.pdf · /backups/postgres/    │
│  Free tier: 10GB storage · 1M read ops/mes · 10M write ops/mes           │
└──────────────────────────────────────────────────────────────────────────┘

Flutter App (APK / IPA)
    → Google Play Store / Apple App Store
    → Llama a https://api.nutrivet.app (Cloudflare → Hetzner)
```

---

## Contenedores y Configuración

### nutrivet-backend
```yaml
image: python:3.12-slim
command: uvicorn backend.presentation.main:app --host 0.0.0.0 --port 8000 --workers 2 --loop uvloop
restart: always
healthcheck: GET /health (cada 30s)
```

### nutrivet-worker
```yaml
image: python:3.12-slim
command: python -m arq backend.infrastructure.queue.arq_settings.WorkerSettings
restart: always
# ARQ WorkerSettings:
#   max_jobs: 10
#   job_timeout: 300s
#   max_tries: 3
```

### PostgreSQL 16
```yaml
image: postgres:16-alpine
volumes: /data/coolify/databases/postgres → /var/lib/postgresql/data
environment:
  POSTGRES_USER: nutrivet
  POSTGRES_PASSWORD: ${DB_PASSWORD}   # Coolify env var
  POSTGRES_DB: nutrivet
ports: solo accesible en red Docker interna (no expuesto externamente)
backups: Coolify automático diario → Cloudflare R2 (/backups/postgres/)
```

### Redis 7
```yaml
image: redis:7-alpine
command: redis-server --appendonly yes  # AOF para persistencia
volumes: /data/coolify/redis → /data
ports: solo accesible en red Docker interna
```

---

## Variables de Entorno (Coolify Dashboard)

```bash
# ──── Aplicación ────
ENVIRONMENT=staging|production
LOG_LEVEL=INFO

# ──── Base de datos ────
DATABASE_URL=postgresql+asyncpg://nutrivet:${DB_PASSWORD}@postgres:5432/nutrivet
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# ──── Redis ────
REDIS_URL=redis://redis:6379/0

# ──── Auth ────
JWT_SECRET=<openssl rand -hex 32>
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=30

# ──── LLM (OpenRouter) ────
OPENROUTER_API_KEY=<desde OpenRouter dashboard>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# ──── Storage (Cloudflare R2) ────
R2_ACCOUNT_ID=<Cloudflare Account ID>
R2_ACCESS_KEY_ID=<R2 API Token>
R2_SECRET_ACCESS_KEY=<R2 API Secret>
R2_BUCKET_NAME=nutrivet-storage-${ENVIRONMENT}
R2_ENDPOINT_URL=https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com

# ──── Encryption AES-256 ────
MEDICAL_DATA_ENCRYPTION_KEY=<openssl rand -hex 32>

# ──── Sentry ────
SENTRY_DSN=<desde Sentry dashboard>
```

> **Regla absoluta**: NINGUNA de estas variables va en el código ni en git.
> En desarrollo local: `.env` (gitignored) · En CI: GitHub Secrets · En producción: Coolify Environment Variables.

---

## Pipeline CI/CD — GitHub Actions

```yaml
# .github/workflows/ci.yml
name: NutriVet.IA CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }

      - name: Install deps
        run: pip install ".[dev]"

      - name: Lint (ruff)
        run: ruff check backend/

      - name: SAST (bandit)
        run: bandit -r backend/ -ll
        # -ll = solo HIGH y MEDIUM

      - name: Dependency CVEs (safety)
        run: safety check

      - name: Tests + coverage domain ≥ 80%
        run: pytest tests/domain/ --cov=backend/domain --cov-fail-under=80

      - name: Coverage safety 100%
        run: pytest tests/domain/ --cov=backend/domain/safety --cov-fail-under=100

      - name: Caso Sally golden case
        run: pytest tests/domain/test_nrc_calculator.py::test_sally_golden_case -v

  deploy-staging:
    needs: quality-gates
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Coolify deploy (staging)
        run: |
          curl -X POST "${{ secrets.COOLIFY_WEBHOOK_STAGING }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}" \
            --fail
          # Coolify: git pull → docker build → health check → swap containers

  deploy-prod:
    needs: quality-gates
    if: github.ref == 'refs/heads/main'
    environment: production   # ← Requiere aprobación manual en GitHub Settings
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Coolify deploy (producción)
        run: |
          curl -X POST "${{ secrets.COOLIFY_WEBHOOK_PROD }}" \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}" \
            --fail
```

**Secretos requeridos en GitHub Actions**:
```
COOLIFY_WEBHOOK_STAGING  → URL del webhook de Coolify para staging
COOLIFY_WEBHOOK_PROD     → URL del webhook de Coolify para producción
COOLIFY_TOKEN            → Token de API de Coolify
```

---

## Dockerfile

```dockerfile
# Dockerfile — para backend y worker (multi-stage)
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[main]"

COPY backend/ ./backend/

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Backend (default)
CMD ["uvicorn", "backend.presentation.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--loop", "uvloop", "--access-log"]
```

```dockerfile
# Dockerfile.worker
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[main]"

COPY backend/ ./backend/

CMD ["python", "-m", "arq", "backend.infrastructure.queue.arq_settings.WorkerSettings"]
```

---

## main.py — Entry Point (sin Mangum)

```python
# backend/presentation/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from backend.presentation.middleware.cors import setup_cors
from backend.presentation.middleware.auth import JWTAuthMiddleware
from backend.presentation.middleware.logging import StructlogMiddleware
from backend.presentation.middleware.db_health import DBHealthMiddleware
from backend.presentation.routers import (
    auth_router, pet_router, plan_router,
    agent_router, scanner_router, export_router
)
from backend.infrastructure.db.session import init_db
from backend.infrastructure.config import settings

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[FastApiIntegration()],
    environment=settings.environment,
    traces_sample_rate=0.1,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="NutriVet.IA API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,  # ocultar en prod
)

setup_cors(app)
app.add_middleware(StructlogMiddleware)
app.add_middleware(DBHealthMiddleware)
app.add_middleware(JWTAuthMiddleware)

app.include_router(auth_router.router,    prefix="/v1/auth",    tags=["auth"])
app.include_router(pet_router.router,     prefix="/v1/pets",    tags=["pets"])
app.include_router(plan_router.router,    prefix="/v1/plans",   tags=["plans"])
app.include_router(agent_router.router,   prefix="/v1/agent",   tags=["agent"])
app.include_router(scanner_router.router, prefix="/v1/scanner", tags=["scanner"])
app.include_router(export_router.router,  prefix="/v1/export",  tags=["export"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/deep")
async def health_deep(db=Depends(get_db), redis=Depends(get_redis)):
    # Verifica DB y Redis
    ...
```

---

## Desarrollo Local

```bash
# 1. Copiar variables de entorno
cp .env.example .env
# Editar .env con tu OPENROUTER_API_KEY

# 2. Levantar stack completo
docker-compose up -d

# 3. Ejecutar migraciones
docker-compose exec backend alembic upgrade head

# 4. API disponible en http://localhost:8000
# 5. MinIO (simula R2) en http://localhost:9001 (admin/admin)

# Tests
pytest tests/ --cov=backend/domain --cov-fail-under=80

# Lint + seguridad
ruff check backend/ && bandit -r backend/ -ll
```

---

## Ambientes

| Ambiente | Branch | Dominio | Propósito |
|----------|--------|---------|-----------|
| `development` | local | localhost:8000 | Desarrollo con hot-reload |
| `staging` | `develop` | staging.api.nutrivet.app | QA — deploy automático |
| `production` | `main` | api.nutrivet.app | Usuarios reales — aprobación manual |

---

## Procedimiento de Rollback

```bash
# En Coolify Dashboard:
# 1. Ir a la aplicación → Deployments
# 2. Click en el deploy anterior → "Rollback"
# → Coolify restaura el contenedor anterior en < 30 segundos

# Rollback de base de datos (si una migración causó problemas):
docker exec nutrivet-backend alembic downgrade -1

# REGLA DE ORO: nunca hacer rollback de migración en producción sin:
# - Backup verificado del mismo día
# - Confirmación de Sadid
```

---

## Retención y Eliminación de Datos

| Tipo de dato | Retención | Eliminación |
|-------------|-----------|-------------|
| Datos usuario (nombre, email) | Hasta baja + 5 años | DELETE + anonimizar |
| Datos clínicos mascota | Hasta baja + 5 años | Anonimizar (no eliminar) |
| Imágenes OCR (R2) | 90 días | R2 Lifecycle Rule |
| PDFs exportados (R2) | 1 año activo + Glacier equivalente | R2 Lifecycle Rule |
| Logs Coolify | 30 días | Coolify retention config |
| agent_traces | 90 días caliente + archivado | Purge job mensual |
| plan_changes | Permanente (auditoría) | Nunca |
| user_consents | Permanente (prueba legal) | Nunca |

---

## Seguridad

```
Capa 1 — Código:      ruff (linting) + bandit (SAST) en cada PR
Capa 2 — Deps:        safety (CVE scan) en cada PR
Capa 3 — Secrets:     Coolify env vars + .env local (gitignored) + git-secrets scan
Capa 4 — Auth:        JWT 15min + RBAC por endpoint + refresh tokens revocables
Capa 5 — Network:     Cloudflare básico + Hetzner Firewall + Docker private network
Capa 6 — Data:        AES-256 en columnas médicas + HTTPS/TLS 1.3 en tránsito
Capa 7 — Auditoría:   structlog JSON sin PII + Sentry + agent_traces append-only
Capa 8 — Review:      OWASP Top 10 checklist en cada PR (.github/PULL_REQUEST_TEMPLATE.md)
```

### Datos que NUNCA se registran en logs

```python
LOG_EXCLUDED_FIELDS = frozenset({
    "password", "password_hash",
    "access_token", "refresh_token", "token",
    "jwt_secret", "openrouter_api_key",
    "r2_access_key_id", "r2_secret_access_key",
    "medical_data_encryption_key",
    "full_name", "email",                # PII — usar user_id UUID
    "cancer_location", "notes",          # Datos médicos sensibles
})
```
