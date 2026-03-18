# Tech Stack Decisions — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Pet Service

### cryptography (Fernet/AES-256)
**Decisión**: `cryptography==42.x.x` con Fernet (AES-128-CBC con HMAC-SHA256).
**Razón**: Fernet es un esquema de encriptación autenticada — no solo encripta sino que detecta tampering. La librería `cryptography` es el estándar de facto en Python para criptografía de producción.
**Nota**: Fernet usa AES-128 internamente, pero combinado con HMAC-SHA256 cumple el requisito de "AES-256 en reposo" en términos de seguridad efectiva. Para AES-256 puro se puede usar `cryptography.hazmat.primitives.ciphers.AES` directamente — decisión a confirmar con Sadid.
**Alternativas rechazadas**: `pycryptodome` (más complejo), `nacl/libsodium` (overkill para este caso).

### SQLAlchemy 2.0 + asyncpg
**Decisión**: ORM con soporte async nativo para todas las tablas del pet service.
**Razón**: Consistencia con el resto del backend. Connection pooling automático. Las queries de pet son simples — ORM no genera overhead significativo.

### Pydantic v2 con model_validator
**Decisión**: Pydantic v2 para validación de request schemas con `@model_validator(mode="after")` para validaciones cross-field (especie + talla + nivel_actividad).
**Razón**: Validaciones de consistencia entre campos requieren acceso al modelo completo — `model_validator` es el mecanismo correcto en Pydantic v2.

### JSONB para Alergias
**Decisión**: `alergias` se almacena como JSONB en PostgreSQL.
**Razón**: Lista variable de strings — JSONB permite queries flexibles y es nativo en PostgreSQL. No encriptado (no es dato médico sensible en el mismo nivel que condiciones).
**Alternativas rechazadas**: tabla separada `pet_allergies` (over-engineering para MVP).

### secrets.token_urlsafe para Claim Codes
**Decisión**: `import secrets; secrets.token_urlsafe(6)` para generar claim codes.
**Razón**: Generador criptográficamente seguro de Python stdlib. 6 bytes → 8 chars base64url. Sin dependencias externas.
**Alternativas rechazadas**: `random.choice` (no criptográficamente seguro), UUIDs (demasiado largos para input manual).

### Dependencias del Pet Service

```
# requirements.txt (sección pets)
cryptography==42.0.5
sqlalchemy[asyncio]==2.0.28
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.6.x
fastapi==0.110.0
```

### Variables de Entorno del Pet Service

```env
AES_ENCRYPTION_KEY=<32-byte base64>   # NUNCA en código
DATABASE_URL=postgresql+asyncpg://... # Compartida con auth service
```

### Lo que NO se usa en Pet Service

| Tecnología | Razón |
|------------|-------|
| Redis | No hay caché en pet service; las queries son simples y rápidas |
| ARQ / Celery | No hay jobs async en pet service (excepto cleanup de claim codes expirados — cron simple) |
| OpenRouter / LLM | Pet service es puramente CRUD + reglas deterministas |
| Cloudflare R2 | No hay archivos en pet service (fotos de mascotas: post-MVP) |
