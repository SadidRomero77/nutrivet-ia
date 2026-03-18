# Logical Components — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Auth Service

### AuthUseCase
**Responsabilidad**: Orquestar los flujos de registro, login, refresh y logout.
**Capa**: application/auth/
**Dependencias**: UserRepositoryPort, RefreshTokenRepositoryPort, JWTService, PasswordService
**Métodos**:
```
register(email, password, role) → AuthToken
login(email, password) → AuthToken | raise AuthError
refresh(refresh_token) → AuthToken | raise AuthError
logout(user_id, refresh_token) → None
```

### JWTService
**Responsabilidad**: Emitir y verificar JWT access tokens.
**Capa**: infrastructure/auth/
**Dependencias**: python-jose, settings (SECRET_KEY)
**Métodos**:
```
create_access_token(user_id, role, tier) → str
decode_access_token(token) → dict | raise JWTError
```

### PasswordService
**Responsabilidad**: Hashing y verificación de contraseñas con bcrypt.
**Capa**: infrastructure/auth/
**Dependencias**: passlib/bcrypt
**Métodos**:
```
hash(password) → str
verify(password, hashed) → bool
```

### PostgreSQLUserRepository
**Responsabilidad**: Persistencia de UserAccount y VetProfile en PostgreSQL.
**Capa**: infrastructure/auth/
**Dependencias**: SQLAlchemy async, asyncpg
**Implementa**: UserRepositoryPort (domain)

### RefreshTokenRepository
**Responsabilidad**: Gestión de tokens rotativos (crear, buscar, revocar).
**Capa**: infrastructure/auth/
**Dependencias**: SQLAlchemy async

### AuthRouter
**Responsabilidad**: Endpoints HTTP del auth service.
**Capa**: presentation/auth/
**Dependencias**: AuthUseCase, Pydantic schemas
**Endpoints**:
```
POST /auth/register   → 201 AuthToken
POST /auth/login      → 200 AuthToken
POST /auth/refresh    → 200 AuthToken
POST /auth/logout     → 204 No Content
GET  /auth/me         → 200 CurrentUser
```

### RBACMiddleware
**Responsabilidad**: Validar JWT y rol en cada request protegido.
**Capa**: presentation/middleware/
**Dependencias**: JWTService
**Uso**: Decorator `@require_role("vet")` o `@require_role("owner")`

## Diagrama de Flujo de Dependencias

```
AuthRouter (presentation)
    ↓ llama
AuthUseCase (application)
    ↓ usa ports
UserRepositoryPort          ← implementado por PostgreSQLUserRepository
RefreshTokenRepositoryPort  ← implementado por RefreshTokenRepository
JWTServicePort              ← implementado por JWTService
PasswordServicePort         ← implementado por PasswordService

RBACMiddleware (presentation)
    ↓ usa
JWTService (infrastructure) directamente (performance — evita caso de uso)
```

## Manejo de Errores

| Error | HTTP Status | Mensaje al cliente |
|-------|-------------|-------------------|
| Email ya registrado | 409 Conflict | "Email ya registrado" |
| Credenciales inválidas | 401 | "Credenciales inválidas" (genérico) |
| Cuenta bloqueada | 429 | "Cuenta bloqueada temporalmente" + Retry-After |
| Token expirado | 401 | "Token expirado" |
| Token inválido | 401 | "Token inválido" |
| Rol insuficiente | 403 | "Acceso denegado" |
