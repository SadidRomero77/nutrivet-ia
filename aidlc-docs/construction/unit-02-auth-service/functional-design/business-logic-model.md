# Business Logic Model — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos E2E del Auth Service

### Flujo 1: Registro de Usuario

```
POST /auth/register { email, password, role }
  ↓
1. Validar Pydantic schema (RegisterRequest)
2. Verificar email no existe en users table → si existe: HTTP 409 Conflict
3. Validar password policy (≥8 chars, ≥1 número, ≥1 letra)
4. hashed_password = bcrypt.hash(password, rounds=12)
5. Crear UserAccount(user_id=uuid4(), email, hashed_password, role, tier="free")
6. Si role == "vet": crear VetProfile(vet_id=user_id, ...)
7. Persistir en PostgreSQL (transacción atómica)
8. Generar access_token (JWT 15min) + refresh_token (opaco)
9. Persistir refresh_token_hash en refresh_tokens table
10. Retornar AuthToken + HTTP 201

Output: AuthToken { access_token, refresh_token, token_type, expires_in }
```

### Flujo 2: Login

```
POST /auth/login { email, password }
  ↓
1. Validar Pydantic schema
2. Buscar UserAccount por email → si no existe: HTTP 401 (sin revelar que no existe)
3. Verificar is_locked → si locked_until > now(): HTTP 429 Retry-After
4. bcrypt.verify(password, hashed_password)
   → Fallo: incrementar failed_login_attempts
            si attempts >= 5: is_locked=True, locked_until=now()+15min
            retornar HTTP 401 (mensaje genérico)
   → Éxito: reset failed_login_attempts = 0
5. Actualizar last_login_at = now()
6. Generar access_token + refresh_token
7. Persistir refresh_token_hash
8. Retornar AuthToken + HTTP 200
```

### Flujo 3: Refresh Token

```
POST /auth/refresh { refresh_token }
  ↓
1. Buscar refresh_token por hash(token) en refresh_tokens table
2. Verificar: encontrado + not is_revoked + expires_at > now()
   → No válido: HTTP 401
3. Verificar UserAccount.is_active == True
   → Inactivo: HTTP 401
4. Revocar token actual (is_revoked=True)
5. Generar nuevo access_token + nuevo refresh_token
6. Persistir nuevo refresh_token (con replaced_by apuntando al anterior)
7. Retornar AuthToken + HTTP 200
```

### Flujo 4: Verificación de Token (Middleware)

```
Request con Authorization: Bearer <access_token>
  ↓
1. Extraer token del header
2. jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
   → Expirado o inválido: HTTP 401
3. Extraer claims: sub (user_id), role, tier
4. Inyectar CurrentUser(user_id, role, tier) en request state
5. Verificar rol requerido por el endpoint (RBAC decorator)
   → Rol insuficiente: HTTP 403
6. Continuar al handler
```

### Flujo 5: Logout

```
POST /auth/logout (requiere access token válido)
  ↓
1. Extraer user_id del JWT
2. Revocar refresh token activo del usuario (is_revoked=True)
3. Retornar HTTP 204 No Content
```
