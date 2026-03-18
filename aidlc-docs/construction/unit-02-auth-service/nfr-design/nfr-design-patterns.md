# NFR Design Patterns — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones de Diseño NFR para Auth Service

### Patrón 1: Stateless JWT (Escalabilidad)
El access token es stateless: el servidor no necesita consultar DB para validarlo.
- Escalabilidad horizontal: múltiples workers de Uvicorn validan el mismo token.
- Trade-off: revocación de access tokens no es posible (expira naturalmente en 15 min).
- Mitigación: logout revoca el refresh token; el access token queda inválido al expirar.

### Patrón 2: Token Rotation con Detección de Robo
Al detectar uso de un refresh token ya revocado → revocar todos los tokens del usuario.
```python
async def refresh(self, token: str) -> AuthToken:
    stored = await self.rt_repo.get_by_hash(sha256(token))
    if stored is None:
        raise AuthError("Token no encontrado")
    if stored.is_revoked:
        # Token revocado usado → posible robo, revocar todo
        await self.rt_repo.revoke_all_for_user(stored.user_id)
        raise AuthError("Token comprometido detectado")
    ...
```

### Patrón 3: Respuestas Genéricas para Prevenir Enumeración
Login fallido siempre retorna HTTP 401 con el mismo mensaje, independientemente de si:
- El email no existe
- La contraseña es incorrecta
- La cuenta está desactivada
Previene que un atacante enumere emails registrados.

### Patrón 4: Bcrypt con Factor 12 (Resistencia a Fuerza Bruta)
Factor 12 ≈ 250ms por hash en hardware moderno.
- Hace ataques de fuerza bruta inviables en caso de filtración de DB.
- Trade-off: 250ms de latencia en login — aceptable para UX.
- No usar factor < 12 sin autorización explícita.

### Patrón 5: Exponential Lockout (Rate Limiting de Login)
5 intentos fallidos → bloqueo 15 min. Reset en login exitoso.
- Previene ataques de fuerza bruta en tiempo real.
- El bloqueo se almacena en PostgreSQL (no en memoria) → persiste entre restarts.

### Patrón 6: Hash del Refresh Token en DB
El refresh token real viaja en la respuesta HTTP (Bearer o cookie).
Solo el SHA-256 del token se almacena en PostgreSQL.
- Si la DB es filtrada, los refresh tokens no pueden usarse.
- Búsqueda por hash: `WHERE token_hash = sha256(token_from_request)`.

### Patrón 7: RBAC como Decorator
```python
@router.get("/vet/pending-plans")
@require_role("vet")
async def get_pending_plans(current_user: CurrentUser = Depends(get_current_user)):
    ...
```
- La validación de rol está en el decorator, no en la lógica de negocio.
- El caso de uso nunca recibe requests de roles incorrectos.
- Previene omisión accidental de validación de rol.

### Patrón 8: Audit Log para Auth Events
Todos los eventos de auth se loggean en JSON estructurado sin PII:
```json
{
  "event": "login_failed",
  "user_id": "uuid",
  "ip_hash": "sha256(ip)",
  "timestamp": "ISO8601",
  "attempt_number": 3
}
```
Nunca se loggea email, contraseña, ni el token completo.
