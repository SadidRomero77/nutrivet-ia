# NFR Requirements — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Auth Service

### NFR-AUTH-01: JWT Access Token — TTL Estricto 15 Minutos
- Nunca emitir access tokens con TTL > 15 minutos.
- Verificado en test: `assert token_exp - token_iat == 900 seconds`.
- En producción: `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15` como variable de entorno obligatoria.

### NFR-AUTH-02: Bcrypt Factor 12
- Nunca usar factor < 12 en producción.
- Verificado: `bcrypt.checkpw` + inspección de hash (`$2b$12$...`).
- Factor 12 ≈ 250ms de latencia en login — aceptable, documentado.

### NFR-AUTH-03: Latencia de Login ≤ 500ms (p95)
- El endpoint `POST /auth/login` debe responder en ≤ 500ms en p95.
- El bcrypt (250ms) es el bottleneck — Uvicorn en threadpool para bcrypt (CPU-bound).
- Alerta si login p95 > 500ms → revisar pool de threads y factor bcrypt.

### NFR-AUTH-04: 0% Tokens sin Expiración
- Ningún access token se emite sin campo `exp`.
- Verificado en CI: test de decodificación sin `exp` debe fallar.

### NFR-AUTH-05: CORS Explícito — Nunca Wildcard en Producción
- `CORS_ORIGINS` en variable de entorno con lista explícita de dominios.
- En staging: puede incluir `localhost:*`.
- En producción: solo dominios de la app móvil / web panel.

### NFR-AUTH-06: Sin PII en Logs
- Los logs de auth no incluyen: email, password, token completo, nombre.
- Solo se loggea: `user_id (UUID)`, `event`, `timestamp`, `ip_hash`.
- Verificado en code review (bandit no cubre esto — manual).

### NFR-AUTH-07: HTTPS Obligatorio
- En producción: Coolify + Traefik con Let's Encrypt (TLS automático).
- Requests HTTP → redirect a HTTPS (middleware de Traefik).
- No se puede desactivar TLS en producción sin autorización explícita.

### NFR-AUTH-08: Cobertura de Tests ≥ 80%
- `pytest --cov=app/application/auth tests/auth/ --cov-fail-under=80`
- Tests obligatorios: registro, login exitoso, login fallido × 5, bloqueo, refresh, logout, RBAC.

### NFR-AUTH-09: Migraciones Solo via Alembic
- Nunca `ALTER TABLE` directo en producción.
- `alembic upgrade head` en pipeline de CI antes de iniciar el servidor.
- Rollback: `alembic downgrade -1`.

### NFR-AUTH-10: Auditoría de Seguridad
- `bandit -r app/infrastructure/auth/` en cada PR → 0 issues HIGH/MEDIUM.
- `safety check` → 0 CVEs críticas en dependencias de auth.
- Revisión de OWASP Top 10 en cada feature de auth (A01: Broken Access Control, A02: Cryptographic Failures, A07: Identification and Authentication Failures).
