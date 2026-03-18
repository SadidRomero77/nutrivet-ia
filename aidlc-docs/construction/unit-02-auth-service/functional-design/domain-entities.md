# Domain Entities — unit-02-auth-service
**Unidad**: unit-02-auth-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Auth Service

### UserAccount
Aggregate raíz de identidad y autenticación.
- `user_id: UUID` — identificador único, nunca expuesto en logs
- `email: str` — único, índice en PostgreSQL
- `hashed_password: str` — bcrypt factor 12, nunca almacenado en plaintext
- `role: Literal["owner", "vet"]` — inmutable post-registro (cambio requiere admin)
- `tier: Literal["free", "basico", "premium", "vet"]` — determina LLM routing y límites
- `is_active: bool` — desactivación lógica, no DELETE
- `is_locked: bool` — bloqueo por intentos fallidos
- `failed_login_attempts: int` — contador, reset en login exitoso
- `locked_until: datetime | None` — TTL del bloqueo (15 min)
- `created_at: datetime`
- `last_login_at: datetime | None`

### RefreshToken
Entidad de token rotativo.
- `token_id: UUID`
- `user_id: UUID` — FK a UserAccount
- `token_hash: str` — hash SHA-256 del token (el token real viaja en cookie/header)
- `expires_at: datetime` — TTL configurable (default 7 días)
- `is_revoked: bool` — revocación explícita
- `created_at: datetime`
- `replaced_by: UUID | None` — enlace al nuevo token tras rotación

### VetProfile
Extensión de UserAccount para rol "vet".
- `vet_id: UUID` — mismo UUID que user_id
- `user_id: UUID` — FK a UserAccount (role == "vet")
- `nombre_completo: str`
- `numero_tarjeta_profesional: str` — verificación futura
- `clinica_nombre: str | None`
- `clinica_ciudad: str | None`
- `verified: bool` — verificación manual en piloto

### TIER_LIMITS (Value Object / Configuración)
Reglas de negocio por tier, hard-coded como constante:
```python
TIER_LIMITS = {
    "free":    {"mascotas": 1, "planes": 1, "preguntas_por_dia": 3, "dias_agente": 3},
    "basico":  {"mascotas": 1, "planes_por_mes": 1, "agente": "ilimitado"},
    "premium": {"mascotas": 3, "planes": "ilimitado", "agente": "ilimitado"},
    "vet":     {"mascotas": "ilimitado", "planes": "ilimitado", "agente": "ilimitado"},
}
```

## Value Objects

### EmailVO
```python
@dataclass(frozen=True)
class EmailVO:
    value: str
    def __post_init__(self):
        if "@" not in self.value or "." not in self.value:
            raise DomainInvariantError("Email inválido")
```

### HashedPasswordVO
```python
@dataclass(frozen=True)
class HashedPasswordVO:
    value: str  # bcrypt hash, siempre empieza con $2b$
```

### AuthToken (VO de respuesta, nunca persistido)
```python
@dataclass(frozen=True)
class AuthToken:
    access_token: str   # JWT 15 min
    refresh_token: str  # opaco, rotativo
    token_type: str = "bearer"
    expires_in: int = 900  # segundos
```
