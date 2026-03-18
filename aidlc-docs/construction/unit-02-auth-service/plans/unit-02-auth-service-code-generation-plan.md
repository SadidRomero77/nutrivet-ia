# Plan: Code Generation — Unit 02: auth-service

**Unidad**: unit-02-auth-service
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar autenticación JWT (access 15min + refresh rotativo), RBAC (owner/vet),
gestión de subscripciones (tier freemium), y endpoints de auth.

**Dependencias previas**: Unit 01 — domain-core completado ✅

---

## Pasos de Implementación

### Paso 1 — Estructura de Carpetas

- [ ] Crear `backend/application/interfaces/user_repository.py` (ABC: IUserRepository)
- [ ] Crear `backend/application/interfaces/token_repository.py` (ABC: ITokenRepository)
- [ ] Crear `backend/application/use_cases/__init__.py`
- [ ] Crear `backend/infrastructure/db/__init__.py`
- [ ] Crear `backend/infrastructure/auth/__init__.py`
- [ ] Crear `backend/presentation/routers/__init__.py`
- [ ] Crear `backend/presentation/schemas/__init__.py`
- [ ] Crear `backend/presentation/middleware/__init__.py`
- [ ] Crear `tests/auth/__init__.py`
- [ ] Crear todos los archivos de test vacíos

### Paso 2 — Tests RED: UserAccount Domain Entity

- [ ] Escribir tests en `tests/auth/test_user_account.py`:
  - test_crear_user_account_owner
  - test_crear_user_account_vet
  - test_email_duplicado_detectado_en_dominio
  - test_password_debe_tener_mayuscula_y_numero
  - test_tier_initial_free
  - test_can_add_pet_free_tier_maximo_1
  - test_can_add_pet_premium_hasta_3
  - test_can_generate_plan_free_con_plan_existente_falla
  - test_agent_questions_free_limite_correcto
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 3 — GREEN: UserAccount Entity

- [ ] Crear `backend/domain/aggregates/user_account.py`:
  - UserAccount dataclass (id, email, password_hash, role, tier, subscription_status)
  - TIER_LIMITS dict: Free→1 pet, Básico→1 pet, Premium→3 pets, Vet→ilimitado
  - `can_add_pet(current_count) -> bool`
  - `can_generate_plan(existing_plans_count) -> bool`
  - `check_agent_quota(questions_used, days_active) -> QuotaResult`
- [ ] Verificar tests PASAN

### Paso 4 — Tests RED: JWT Service

- [ ] Escribir tests en `tests/auth/test_jwt_service.py`:
  - test_generar_access_token_expira_en_15min
  - test_generar_refresh_token_es_uuid
  - test_verificar_token_valido
  - test_verificar_token_expirado_lanza_error
  - test_verificar_token_invalido_lanza_error
  - test_refresh_token_rotativo_invalida_anterior
- [ ] Verificar FALLAN

### Paso 5 — GREEN: JWTService

- [ ] Crear `backend/infrastructure/auth/jwt_service.py`:
  - `create_access_token(user_id, role, tier) -> str` (HS256, exp=15min)
  - `create_refresh_token() -> str` (UUID, guardado en DB)
  - `verify_access_token(token: str) -> TokenPayload`
  - `rotate_refresh_token(old_token, user_id) -> str` (invalida old, crea new)
- [ ] Crear `backend/infrastructure/auth/password_service.py`:
  - `hash_password(password: str) -> str` (bcrypt)
  - `verify_password(plain, hashed) -> bool`
- [ ] Verificar tests PASAN

### Paso 6 — Tests RED: AuthUseCase

- [ ] Escribir tests en `tests/auth/test_auth_use_case.py`:
  - test_registro_owner_exitoso
  - test_registro_con_email_existente_falla
  - test_login_credenciales_correctas
  - test_login_password_incorrecto_falla
  - test_login_email_no_existe_falla
  - test_refresh_token_valido
  - test_refresh_token_invalido_falla
  - test_logout_invalida_refresh_token
- [ ] Verificar FALLAN

### Paso 7 — GREEN: AuthUseCase

- [ ] Crear `backend/application/interfaces/user_repository.py` (IUserRepository ABC)
- [ ] Crear `backend/application/use_cases/auth_use_case.py`:
  - `register(email, password, role, vet_data?) -> TokenResponse`
  - `login(email, password) -> TokenResponse`
  - `refresh(refresh_token) -> TokenResponse`
  - `logout(refresh_token) -> None`
- [ ] Verificar tests PASAN

### Paso 8 — Migración Alembic: users + refresh_tokens

- [ ] Crear `backend/alembic/versions/001_create_users_table.py`:
  - Tabla `users`: id (UUID), email (unique), password_hash, role, tier, subscription_status, created_at
- [ ] Crear `backend/alembic/versions/002_create_refresh_tokens_table.py`:
  - Tabla `refresh_tokens`: id (UUID), user_id (FK), token_hash, expires_at, revoked_at
- [ ] Ejecutar migraciones en entorno local: `alembic upgrade head`
- [ ] Verificar schema con `alembic current`

### Paso 9 — PostgreSQLUserRepository

- [ ] Crear `backend/infrastructure/db/user_repository.py`:
  - Implementa IUserRepository
  - SQLAlchemy async con asyncpg
  - `save(user)`, `find_by_email(email)`, `find_by_id(id)`
- [ ] Crear `backend/infrastructure/db/token_repository.py`:
  - `save_refresh_token(user_id, token_hash, expires_at)`
  - `find_valid_token(token_hash)`
  - `revoke_token(token_hash)`
- [ ] Tests de integración: `tests/auth/test_user_repository.py` (con DB de test)

### Paso 10 — Middleware RBAC

- [ ] Crear `backend/presentation/middleware/auth_middleware.py`:
  - `get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload`
  - `require_role(*roles: str) → Depends`
- [ ] Tests: `tests/auth/test_auth_middleware.py`:
  - test_require_role_owner_con_token_owner
  - test_require_role_vet_con_token_owner_falla
  - test_token_expirado_retorna_401

### Paso 11 — Endpoints FastAPI

- [ ] Crear `backend/presentation/routers/auth_router.py`:
  - `POST /v1/auth/register` → RegisterRequest → TokenResponse
  - `POST /v1/auth/login` → LoginRequest → TokenResponse
  - `POST /v1/auth/refresh` → RefreshRequest → TokenResponse
  - `POST /v1/auth/logout` → LogoutRequest → 204
- [ ] Crear `backend/presentation/schemas/auth_schemas.py`:
  - RegisterRequest, LoginRequest, RefreshRequest, TokenResponse
  - Todos con validaciones Pydantic
- [ ] Tests de endpoints: `tests/auth/test_auth_router.py`

### Paso 12 — Cobertura y Calidad

- [ ] Ejecutar: `pytest --cov=backend/application/use_cases tests/auth/ --cov-fail-under=80`
- [ ] Ejecutar: `ruff check backend/` → 0 errores
- [ ] Ejecutar: `bandit -r backend/` → 0 HIGH/MEDIUM
- [ ] Verificar: todos los endpoints con Pydantic validation

---

## Criterios de Done

- [ ] POST /v1/auth/register → 201 (owner y vet)
- [ ] POST /v1/auth/login → 200 con JWT 15min + refresh UUID
- [ ] POST /v1/auth/refresh → nuevo access token, refresh rotado
- [ ] POST /v1/auth/logout → 204, refresh invalidado en DB
- [ ] `require_role("vet")` bloquea tokens de owner → 403
- [ ] Migración Alembic ejecutada correctamente
- [ ] Tests ≥ 80% cobertura en use cases

## Tiempo Estimado

3-4 días

## Referencias

- Unit spec: `inception/units/unit-02-auth-service.md`
- ADR-004: JWT access 15min + refresh rotativo
- ADR-011: Freemium — tiers
- Constitution REGLA 6 (seguridad de datos)
