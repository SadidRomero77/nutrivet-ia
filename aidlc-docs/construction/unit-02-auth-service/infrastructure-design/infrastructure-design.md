# Infrastructure Design — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura

### JWTService (python-jose)

```python
# infrastructure/auth/jwt_service.py
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone

class JWTService:
    """Servicio de emisión y verificación de JWT. Usa python-jose."""

    def create_access_token(self, user_id: UUID, role: str, tier: str) -> str:
        """Emite access token JWT con TTL 15 minutos."""
        payload = {
            "sub": str(user_id),
            "role": role,
            "tier": tier,
            "jti": str(uuid4()),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    def decode_access_token(self, token: str) -> dict:
        """Decodifica y valida JWT. Lanza JWTError si inválido o expirado."""
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
```

### PasswordService (passlib/bcrypt)

```python
# infrastructure/auth/password_service.py
from passlib.context import CryptContext

class PasswordService:
    """Hashing y verificación de contraseñas con bcrypt."""
    _ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

    def hash(self, password: str) -> str:
        """Hash bcrypt factor 12. Nunca loggear el input."""
        return self._ctx.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        """Verificar password vs hash. Tiempo constante (previene timing attacks)."""
        return self._ctx.verify(password, hashed)
```

### PostgreSQLUserRepository (SQLAlchemy async)

```python
# infrastructure/auth/pg_user_repository.py
class PostgreSQLUserRepository(UserRepositoryPort):
    """Implementación PostgreSQL del repositorio de usuarios."""

    async def get_by_email(self, email: str) -> UserAccount | None: ...
    async def get_by_id(self, user_id: UUID) -> UserAccount | None: ...
    async def save(self, user: UserAccount) -> None: ...
    async def update_login_attempt(self, user_id: UUID, failed: bool) -> None: ...
```

### RefreshTokenRepository (SQLAlchemy async)

```python
class RefreshTokenRepository:
    async def save(self, token: RefreshToken) -> None: ...
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...
    async def revoke(self, token_id: UUID) -> None: ...
    async def revoke_all_for_user(self, user_id: UUID) -> None: ...
```

### RBACMiddleware (FastAPI)

```python
# presentation/auth/middleware.py
from functools import wraps
from fastapi import HTTPException, Depends

def require_role(*roles: str):
    """Decorator de RBAC. Valida rol del JWT en cada endpoint."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: CurrentUser = Depends(get_current_user), **kwargs):
            if current_user.role not in roles:
                raise HTTPException(status_code=403, detail="Rol insuficiente")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

## Alembic Migrations

```python
# migrations/versions/001_create_users_refresh_tokens.py
# Ejecutar: alembic revision --autogenerate -m "create users refresh tokens"
# Nunca ALTER directo en producción
```

## Dependencias Python

```
python-jose[cryptography]==3.3.0   # JWT
passlib[bcrypt]==1.7.4              # bcrypt hashing
sqlalchemy[asyncio]==2.0.x          # ORM async
asyncpg==0.29.x                     # PostgreSQL async driver
alembic==1.13.x                     # Migraciones
```
