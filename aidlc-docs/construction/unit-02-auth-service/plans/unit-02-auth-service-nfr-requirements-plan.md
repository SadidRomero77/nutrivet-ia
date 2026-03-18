# Plan: NFR Requirements — Unit 02: auth-service

**Unidad**: unit-02-auth-service
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del auth-service

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| POST /v1/auth/login | < 200ms p95 | bcrypt verify es el cuello de botella — work factor 12 |
| POST /v1/auth/refresh | < 50ms p95 | Solo DB lookup + JWT sign |
| JWT verification (middleware) | < 10ms | HS256 en memoria, sin red |
| POST /v1/auth/register | < 300ms p95 | bcrypt hash + DB insert |

### Seguridad

**JWT**:
- Algoritmo: HS256 — clave secreta mínimo 256 bits.
- Access token TTL: exactamente 15 minutos — sin excepción.
- Refresh token TTL: 30 días — rotativo (single-use).
- Payload JWT: solo `user_id`, `role`, `tier`, `exp` — sin datos sensibles.
- Refresh tokens: almacenados como hash SHA-256 en DB — nunca el token crudo.

**Passwords**:
- bcrypt work factor: 12 — balance seguridad/performance para < 200ms.
- Mínimo 8 caracteres — validado en Pydantic antes de hashear.
- Nunca loggear passwords en ningún nivel de log.

**Rate Limiting**:
- 5 intentos de login fallidos → lockout de 15 minutos (por IP + email).
- 10 intentos de refresh en 1 minuto → 429 Too Many Requests.

**RBAC**:
- Validación de rol en cada endpoint — nunca confiar en el payload sin verificar firma JWT.
- Decorador `@require_role("owner")` o `@require_role("vet")` en cada router.

**Datos en Logs**:
- NUNCA loggear: passwords, tokens JWT, refresh tokens, emails en texto plano.
- Solo loggear: `user_id` (UUID anónimo), evento, timestamp, IP hasheada.

**CORS**:
- Configurado explícitamente — nunca wildcard (`*`) en producción.
- Orígenes permitidos: solo dominios propios de NutriVet.IA.

### Confiabilidad

- Refresh token rotation: si un token ya usado es presentado de nuevo → revocar TODA la familia de tokens del usuario (señal de robo de token).
- JWT secret: rotar sin downtime vía key versioning si se compromete.

### Mantenibilidad

- Cobertura mínima: **80%** en `application/` y `domain/` relacionados.
- Type hints obligatorios en toda función.
- Docstrings en español.
- Ruff + bandit: 0 errores antes de PR.

## Checklist NFR auth-service

- [ ] `pytest --cov=backend/auth tests/auth/ --cov-fail-under=80` pasa
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM en auth modules
- [ ] Login p95 < 200ms verificado en test de carga básico
- [ ] JWT verification < 10ms (test unitario con timer)
- [ ] Lockout activo después de 5 intentos fallidos
- [ ] Refresh token rotation: token reusado → revoca familia completa
- [ ] CORS configurado explícitamente (no wildcard)
- [ ] 0 datos sensibles en logs (test de logs negativos)

## Referencias

- Global: `_shared/nfr-requirements.md`
- ADR-004: JWT access + refresh rotativo
- Constitution: REGLA 6 (seguridad de datos)
- Unit spec: `inception/units/unit-02-auth-service.md`
