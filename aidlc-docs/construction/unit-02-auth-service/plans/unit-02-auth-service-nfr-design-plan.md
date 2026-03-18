# Plan: NFR Design — Unit 02: auth-service

**Unidad**: unit-02-auth-service
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a auth-service

### Patrón: Refresh Token Rotation

**Contexto**: Los refresh tokens de larga duración (30 días) son blancos de robo.
La rotación limita la ventana de exposición.

**Diseño**:
- Cada uso del refresh token invalida el anterior e emite uno nuevo.
- Cada token tiene un `family_id` — si un token ya usado es presentado de nuevo,
  se revocan TODOS los tokens de esa familia (señal de robo de token).
- El token crudo se retorna al cliente, pero en DB se almacena solo `SHA256(token)`.

```python
# Patrón de rotación en RefreshTokenUseCase:
async def refresh(self, token: str) -> TokenPair:
    token_hash = sha256(token)
    stored = await self.repo.find_by_hash(token_hash)

    if stored is None:
        raise InvalidTokenError()

    if stored.used_at is not None:  # Token reusado → robo detectado
        await self.repo.revoke_family(stored.family_id)
        raise TokenReuseDetectedError()

    if stored.expires_at < datetime.utcnow():
        raise TokenExpiredError()

    await self.repo.mark_used(stored.token_id)
    return await self._issue_new_pair(stored.user_id, stored.family_id)
```

### Patrón: bcrypt Work Factor 12

**Contexto**: Balancear seguridad (resistencia a fuerza bruta) y performance (< 200ms).

**Diseño**:
```python
# En domain/value_objects/password.py — no en infrastructure
BCRYPT_WORK_FACTOR = 12  # ~100ms en CPX31 — ajustar si hardware cambia

def hash_password(plain: str) -> str:
    """Hashea password con bcrypt work factor 12. Nunca loggear el input."""
    if len(plain) < 8:
        raise WeakPasswordError("Password mínimo 8 caracteres")
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_WORK_FACTOR)).decode()

def verify_password(plain: str, hashed: str) -> bool:
    """Verifica password — tiempo constante para evitar timing attacks."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

### Patrón: Token Blacklist en PostgreSQL (sin Redis)

**Contexto**: Invalidar refresh tokens sin agregar Redis como dependencia en Fase 1.

**Diseño**:
- Tabla `refresh_tokens` con `used_at TIMESTAMP NULL`.
- Token válido = `used_at IS NULL AND expires_at > NOW()`.
- Cleanup job diario: `DELETE FROM refresh_tokens WHERE expires_at < NOW() - INTERVAL '7 days'`.
- Index: `CREATE INDEX idx_refresh_tokens_hash ON refresh_tokens(token_hash)` — O(log n) lookup.

### Patrón: Fail-Fast en LoginRequest

**Contexto**: Validar el request antes de tocar la DB para evitar queries innecesarios.

**Diseño** (Pydantic schema en presentation layer):
```python
class LoginRequest(BaseModel):
    email: EmailStr  # Pydantic valida formato email
    password: str = Field(min_length=1, max_length=72)  # bcrypt max 72 bytes

    # Fail-fast: si email o password están vacíos → 422 antes de llegar al use case
```

### Patrón: Logging Sin Datos Sensibles

**Contexto**: Los logs no pueden contener passwords, tokens ni emails en texto plano (Constitution REGLA 6).

**Diseño**:
```python
# Correcto:
logger.info("login_attempt", extra={"user_id": str(user_id), "success": True})

# PROHIBIDO:
logger.info(f"login for {email}")         # ❌ email en log
logger.debug(f"token: {access_token}")    # ❌ token en log
logger.error(f"wrong password: {plain}")  # ❌ password en log
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `use_cases/login_use_case.py` | 90% | Unit tests — happy path + error paths |
| `use_cases/refresh_token_use_case.py` | 90% | Unit tests — rotation + reuse detection |
| `use_cases/register_use_case.py` | 80% | Unit tests — validaciones |
| `middleware/jwt_middleware.py` | 80% | Unit + integration tests |
| `routers/auth_router.py` | 80% | Integration tests |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- ADR-004: JWT access + refresh rotativo
- Constitution: REGLA 6 (seguridad de datos)
