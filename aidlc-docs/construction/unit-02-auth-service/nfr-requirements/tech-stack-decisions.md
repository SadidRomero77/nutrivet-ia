# Tech Stack Decisions — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Auth Service

### python-jose[cryptography] para JWT
**Decisión**: `python-jose[cryptography]==3.3.0`
**Razón**: Librería estándar en el ecosistema FastAPI. Soporte HS256, RS256. La dependencia `[cryptography]` provee el backend criptográfico nativo (más rápido y seguro que PyCryptodome).
**Alternativas rechazadas**: `PyJWT` (menos integrado con FastAPI), `authlib` (overhead mayor para uso simple).

### passlib[bcrypt] para Hashing
**Decisión**: `passlib[bcrypt]==1.7.4`
**Razón**: Abstracción de alto nivel sobre bcrypt. Maneja verificación en tiempo constante automáticamente (previene timing attacks). Fácil upgrade de factor sin cambiar código.
**Alternativas rechazadas**: `bcrypt` directo (más bajo nivel, más verboso), `argon2-cffi` (más moderno pero menos adopción en el ecosistema FastAPI en producción).

### SQLAlchemy 2.0 async + asyncpg
**Decisión**: SQLAlchemy async para persistencia de users y refresh_tokens.
**Razón**: ORM maduro con soporte async nativo en v2.0. asyncpg es el driver más rápido para PostgreSQL en Python async.
**Alternativas rechazadas**: `tortoise-orm` (menor madurez), `databases` (demasiado bajo nivel), raw asyncpg (sin ORM overhead pero más código boilerplate).

### Alembic para Migraciones
**Decisión**: Alembic con autogenerate.
**Razón**: Estándar para proyectos SQLAlchemy. Migraciones versionadas y reversibles. Integrado en CI pipeline.
**Regla**: Revisar siempre el script autogenerado antes de aplicar — el autogenerate puede perder constraints custom.

### FastAPI para Endpoints
**Decisión**: FastAPI con Pydantic v2 para schemas.
**Razón**: Validación automática de request bodies. OpenAPI docs automáticas. Type hints nativos. Dependency injection para `get_current_user`.

### Dependencias del Auth Service

```
# requirements.txt (sección auth)
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy[asyncio]==2.0.28
asyncpg==0.29.0
alembic==1.13.1
fastapi==0.110.0
pydantic[email]==2.6.x
uvicorn[standard]==0.27.x
```

### Variables de Entorno Obligatorias
```env
JWT_SECRET_KEY=           # 256-bit random — NUNCA en código
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12
DATABASE_URL=postgresql+asyncpg://...
CORS_ORIGINS=["https://app.nutrivetia.com"]  # Nunca wildcard en prod
```

### Lo que NO se usa en Auth Service
| Tecnología | Razón de Exclusión |
|------------|-------------------|
| OAuth2 / OpenID Connect | Complejidad innecesaria para MVP; puede agregarse post-lanzamiento |
| Redis para sesiones | JWT stateless — no requiere session store |
| Celery | ARQ es suficiente para jobs async; no aplica en auth |
| 2FA (TOTP) | Post-MVP; no en scope del piloto BAMPYSVET |
