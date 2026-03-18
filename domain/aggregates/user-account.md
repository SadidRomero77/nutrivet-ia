# Aggregate: UserAccount

**Bounded Context**: Identity
**Aggregate Root**: `UserAccount`
**Responsabilidad**: Gestionar la identidad, autenticación, rol y límites de subscripción del usuario.

---

## Definición del Aggregate

```python
@dataclass
class UserAccount:
    user_id: UUID
    email: str                      # Único, validado con regex RFC 5322
    hashed_password: str            # bcrypt, nunca en texto plano
    role: UserRole                  # OWNER | VET
    subscription_tier: SubscriptionTier  # FREE | BASICO | PREMIUM | VET
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    consent_given_at: datetime | None  # Ley 1581/2012 Colombia
```

---

## Value Objects

### UserRole
```python
class UserRole(str, Enum):
    OWNER = "owner"  # Dueño de mascota
    VET = "vet"      # Veterinario firmante
```

### SubscriptionTier
```python
class SubscriptionTier(str, Enum):
    FREE = "free"          # $0 · 1 mascota · 1 plan total
    BASICO = "basico"      # $29.900 COP/mes · 1 mascota · 1 plan/mes
    PREMIUM = "premium"    # $59.900 COP/mes · 3 mascotas · ilimitados
    VET = "vet"            # $89.000 COP/mes · ilimitadas · dashboard clínico

    @property
    def max_pets(self) -> int | None:
        limits = {
            "free": 1,
            "basico": 1,
            "premium": 3,
            "vet": None  # Ilimitadas
        }
        return limits[self.value]

    @property
    def max_plans_per_month(self) -> int | None:
        limits = {
            "free": 1,    # 1 plan total, no mensual
            "basico": 1,
            "premium": None,  # Ilimitados
            "vet": None
        }
        return limits[self.value]
```

---

## Invariantes del Aggregate

- `email` debe ser único en el sistema.
- `hashed_password` nunca se expone en ninguna respuesta de API.
- Un `UserAccount` con rol `VET` no puede tener tier `FREE`, `BASICO`, o `PREMIUM` — solo `VET`.
- `consent_given_at` es obligatorio para usuarios en Colombia (Ley 1581/2012).
- Un owner con tier `FREE` que intente crear una segunda mascota → `SubscriptionLimitError`.

---

## Métodos del Aggregate Root

```python
def can_create_pet(self, current_pet_count: int) -> bool:
    """Verifica límite de mascotas según tier."""
    max_pets = self.subscription_tier.max_pets
    if max_pets is None:
        return True
    return current_pet_count < max_pets

def can_generate_plan(self, plans_this_month: int) -> bool:
    """Verifica límite de planes según tier."""
    max_plans = self.subscription_tier.max_plans_per_month
    if max_plans is None:
        return True
    return plans_this_month < max_plans

def is_vet(self) -> bool:
    return self.role == UserRole.VET

def is_owner(self) -> bool:
    return self.role == UserRole.OWNER
```

---

## Domain Events que Emite

| Evento | Trigger |
|--------|---------|
| `UserRegistered` | Registro exitoso |
| `UserSubscriptionChanged` | Cambio de tier |
| `TokenRevoked` | Logout o token comprometido |
