# Plan: Infrastructure Design — Unit 02: auth-service

**Unidad**: unit-02-auth-service
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| AuthRouter (FastAPI) | Contenedor Docker — FastAPI + Uvicorn en Hetzner CPX31 |
| JWT middleware | Módulo en `presentation/middleware/jwt_middleware.py` |
| RBAC decorator | `presentation/middleware/rbac.py` |
| LoginUseCase | `application/use_cases/login_use_case.py` |
| RegisterUseCase | `application/use_cases/register_use_case.py` |
| RefreshTokenUseCase | `application/use_cases/refresh_token_use_case.py` |

**Servidor**: Hetzner CPX31 (Ashburn VA) — mismo contenedor FastAPI del backend.
No se requiere un servicio separado para auth — co-ubicado con el backend principal.

### Storage

| Componente | Motor | Tabla/Colección |
|------------|-------|-----------------|
| UserAccount | PostgreSQL Docker | `users` |
| RefreshTokens | PostgreSQL Docker | `refresh_tokens` |
| Lockout tracking | PostgreSQL Docker | `login_attempts` |

**Nota**: No se usa Redis para blacklist de tokens — PostgreSQL es suficiente para la escala inicial
(simplicity over premature optimization). Ver NFR Design para el patrón de token blacklist.

### No se Requieren Servicios Externos

Auth es completamente self-contained. No hay proveedor externo de auth (sin Auth0, sin Firebase Auth).
El JWT secret es una variable de entorno en el contenedor.

### Variables de Entorno Requeridas

```bash
# Obligatorias — sin defaults en código
JWT_SECRET_KEY=<mínimo 256 bits, generado con openssl rand -hex 32>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
BCRYPT_WORK_FACTOR=12
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrivet
```

### Migraciones de Base de Datos

```
Alembic migrations:
  001_users.py          → tabla users (user_id, email, password_hash, role, tier, is_active, created_at)
  002_refresh_tokens.py → tabla refresh_tokens (token_id, user_id, token_hash, expires_at, used_at, created_at)
  002b_login_attempts.py → tabla login_attempts (id, email, ip_hash, attempted_at, success)
```

### Dockerfile (adiciones para auth)

```dockerfile
# No requiere dependencias adicionales al Dockerfile base
# bcrypt, python-jose ya en requirements.txt
RUN pip install bcrypt==4.1.3 python-jose[cryptography]==3.3.0 passlib==1.7.4
```

## Notas Arquitecturales

1. **Sin Redis en Fase 1**: El token blacklist y lockout se implementan en PostgreSQL.
   Si la escala lo requiere, migrar a Redis es un cambio de infrastructure sin tocar domain/application.

2. **Secret rotation**: El `JWT_SECRET_KEY` puede rotarse sin downtime agregando soporte
   de múltiples keys activas en el middleware (ADR-004 define el procedimiento).

3. **Refresh tokens en DB**: Se almacena solo el `SHA256(token)` — el token crudo
   nunca persiste en disco, solo en memoria durante la respuesta HTTP.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- ADR-004: JWT access + refresh rotativo
- ADR-011: RBAC implementation
