# Business Rules — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Auth Service

### BR-AUTH-01: JWT Access Token — TTL 15 Minutos
- Los access tokens expiran exactamente a los 15 minutos.
- No se puede emitir un access token con TTL mayor.
- Claims obligatorios: `sub` (user_id UUID), `role`, `tier`, `exp`, `iat`, `jti`.
- Algoritmo: HS256 con secret desde variable de entorno (nunca hardcoded).

### BR-AUTH-02: Refresh Token Rotativo
- Cada uso del refresh token genera un nuevo refresh token.
- El token anterior es revocado inmediatamente tras el intercambio.
- TTL del refresh token: 7 días.
- Almacenado como hash SHA-256 en PostgreSQL (nunca el token raw).
- Si un token revocado se intenta usar → revocar TODOS los tokens de ese usuario (indicador de robo).

### BR-AUTH-03: Bcrypt Factor 12
- Las contraseñas se hashean con bcrypt, cost factor 12.
- Nunca se almacena ni se loggea la contraseña en plaintext.
- El plaintext solo existe en memoria durante la operación de hashing/verificación.

### BR-AUTH-04: Bloqueo por Intentos Fallidos
- 5 intentos de login fallidos consecutivos → bloqueo de la cuenta por 15 minutos.
- El contador se resetea en cada login exitoso.
- El contador se incrementa independientemente de si el email existe o no (previene enumeración).
- Respuesta al usuario bloqueado: HTTP 429 con `Retry-After: 900` (segundos).

### BR-AUTH-05: RBAC — Validación de Rol en Cada Endpoint
- Cada endpoint protegido valida el rol del JWT antes de ejecutar el caso de uso.
- `owner`: acceso a sus propias mascotas y planes.
- `vet`: acceso al dashboard clínico, firma de planes PENDING_VET.
- Un owner NO puede acceder a endpoints de vet, y viceversa.
- La validación de rol ocurre en el middleware, no en el caso de uso.

### BR-AUTH-06: Límites de Tier
- Los límites de tier se validan en application layer al crear mascota o plan.
- El JWT incluye el `tier` para que la validación no requiera DB lookup extra.
- Cambiar de tier requiere re-emitir access token para reflejar el nuevo tier.

### BR-AUTH-07: Registro — Validaciones
- Email único en el sistema (constraint en PostgreSQL + validación de negocio).
- Contraseña mínimo 8 caracteres, al menos 1 número, al menos 1 letra.
- Role válido: solo "owner" o "vet".
- Tier inicial: siempre "free" (no se puede registrar en otro tier directamente).

### BR-AUTH-08: Logout
- Logout = revocar el refresh token activo del usuario.
- El access token NO se puede revocar (stateless) — expira naturalmente en 15 min.
- Logout de "todos los dispositivos" = revocar todos los refresh tokens activos del user_id.

### BR-AUTH-09: Seguridad de Transporte
- Access token: Bearer en header `Authorization: Bearer <token>`.
- Refresh token: HttpOnly cookie + header alternativo para mobile (Flutter no maneja cookies nativamente).
- HTTPS obligatorio — nunca HTTP en producción.
