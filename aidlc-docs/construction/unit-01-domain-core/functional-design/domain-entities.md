# Domain Entities — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades Raíz del Dominio

### UserAccount
Aggregate raíz para la identidad del usuario.
- `user_id: UUID`
- `email: EmailStr` (value object, inmutable post-registro)
- `hashed_password: str`
- `role: Literal["owner", "vet"]`
- `tier: Literal["free", "basico", "premium", "vet"]`
- `is_locked: bool` (bloqueo por 5 intentos fallidos)
- `created_at: datetime`

### PetProfile
Aggregate raíz del perfil de mascota. 13 campos obligatorios.
- `pet_id: UUID`
- `owner_id: UUID`
- `nombre: str`
- `especie: Literal["perro", "gato"]`
- `raza: str`
- `sexo: Literal["macho", "hembra"]`
- `edad: AgeVO` (value object: valor + unidad meses/años)
- `peso_kg: Decimal` (> 0)
- `talla: Literal["mini_xs","pequeno_s","mediano_m","grande_l","gigante_xl"] | None` (solo perros)
- `estado_reproductivo: Literal["esterilizado", "no_esterilizado"]`
- `nivel_actividad: ActivityLevelVO`
- `bcs: int` (1–9)
- `condiciones_medicas: list[MedicalConditionVO]` (encriptado AES-256)
- `alergias: list[str]`
- `alimentacion_actual: Literal["concentrado", "natural", "mixto"]`

### NutritionPlan
Aggregate raíz del plan nutricional generado.
- `plan_id: UUID`
- `pet_id: UUID`
- `status: PlanStatus` (PENDING_VET | ACTIVE | UNDER_REVIEW | ARCHIVED)
- `modalidad: Literal["natural", "concentrado"]`
- `rer_kcal: Decimal`
- `der_kcal: Decimal`
- `sections: list[PlanSection]` (exactamente 5)
- `plan_type: Literal["estandar", "temporal_medical", "life_stage"]`
- `review_date: date | None`
- `created_at: datetime`

### ConversationSession
- `session_id: UUID`
- `pet_id: UUID`
- `messages: list[ConversationMessage]`
- `created_at: datetime`

### LabelScan
- `scan_id: UUID`
- `pet_id: UUID`
- `image_type: Literal["nutrition_table", "ingredients_list"]`
- `status: ScanStatus`
- `semaphore: Literal["green", "yellow", "red"] | None`
- `raw_ocr: str | None`
- `evaluation: dict | None`

## Value Objects

### AgeVO
```python
@dataclass(frozen=True)
class AgeVO:
    value: int
    unit: Literal["meses", "años"]
```

### ActivityLevelVO
```python
@dataclass(frozen=True)
class ActivityLevelVO:
    level: str  # validado por especie en invariante
```

### MedicalConditionVO
```python
@dataclass(frozen=True)
class MedicalConditionVO:
    condition: str  # debe estar en las 13 condiciones soportadas
```

### PlanStatus (Enum)
```python
class PlanStatus(str, Enum):
    PENDING_VET = "PENDING_VET"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    ARCHIVED = "ARCHIVED"
```

### NRCResult
```python
@dataclass(frozen=True)
class NRCResult:
    rer_kcal: Decimal
    der_kcal: Decimal
    peso_kg: Decimal
    factors_applied: dict[str, Decimal]
```
