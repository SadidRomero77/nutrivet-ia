# Deployment Architecture — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Ubicación en el Deployment

El auth service es parte del monolito modular `nutrivet-backend`.

```
Hetzner CPX31 (Ashburn VA)
└── Coolify (Docker orchestrator)
    └── nutrivet-backend (Docker container)
        ├── presentation/auth/
        │   ├── router.py          ← POST /auth/register, /login, /refresh, /logout
        │   └── schemas.py         ← RegisterRequest, LoginRequest, AuthToken response
        ├── application/auth/
        │   └── auth_use_case.py   ← AuthUseCase (orquestador de flujos)
        ├── infrastructure/auth/
        │   ├── jwt_service.py     ← JWTService (python-jose)
        │   ├── password_service.py ← PasswordService (bcrypt)
        │   └── pg_user_repository.py ← SQLAlchemy implementation
        └── domain/entities/
            └── user_account.py    ← UserAccount entity
```

## Base de Datos

PostgreSQL en el mismo servidor Hetzner CPX31 (containerizado en Coolify).

```sql
-- Tablas del auth service
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner','vet')),
    tier VARCHAR(20) NOT NULL DEFAULT 'free',
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_login_at TIMESTAMPTZ NULL
);

CREATE TABLE refresh_tokens (
    token_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    token_hash VARCHAR(64) NOT NULL,  -- SHA-256 hex
    expires_at TIMESTAMPTZ NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    replaced_by UUID NULL
);

CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id) WHERE NOT is_revoked;
```

## Variables de Entorno Requeridas

```env
JWT_SECRET_KEY=<256-bit random secret>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/nutrivet
```

## Coolify Deployment

- El contenedor `nutrivet-backend` expone el puerto 8000 (Uvicorn).
- Coolify gestiona el reverse proxy (Traefik) con TLS automático (Let's Encrypt).
- La base de datos PostgreSQL corre en un contenedor separado en el mismo servidor.
- Healthcheck endpoint: `GET /health` → 200 OK (verifica DB connection).

## CI/CD Pipeline

```yaml
# GitHub Actions → Coolify webhook
on: [push to main]
jobs:
  test:
    - pytest tests/auth/ --cov=app/application/auth --cov-fail-under=80
    - bandit -r app/infrastructure/auth/
  deploy:
    - Coolify webhook trigger (auto en staging, manual en prod)
```
