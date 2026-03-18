# Aggregate: NutritionPlan

**Bounded Context**: Nutrition Planning
**Aggregate Root**: `NutritionPlan`
**Responsabilidad**: Encapsular el plan nutricional, su ciclo de vida y garantizar que las reglas de negocio se cumplan en cada transición de estado.

---

## Definición del Aggregate

```python
@dataclass
class NutritionPlan:
    # Identidad
    plan_id: UUID
    pet_id: UUID
    owner_id: UUID

    # Tipo y estado
    plan_type: PlanType          # ESTANDAR | TEMPORAL_MEDICAL | LIFE_STAGE
    status: PlanStatus           # PENDING_VET | ACTIVE | UNDER_REVIEW | ARCHIVED
    modality: PlanModality       # NATURAL | CONCENTRADO

    # Cálculo nutricional (determinista)
    rer_kcal: float              # Calculado por NRCCalculator
    der_kcal: float              # Calculado por NRCCalculator
    weight_phase: WeightPhase    # REDUCCION | MANTENIMIENTO | AUMENTO
    llm_model_used: str          # Modelo que generó el plan

    # Contenido del plan (generado por LLM con guardarraíles)
    content: PlanContent         # Ver PlanContent abajo

    # HITL
    approved_by_vet_id: UUID | None   # None hasta aprobación
    approval_timestamp: datetime | None
    review_date: date | None          # Para plan temporal_medical y life_stage

    # Trazabilidad
    agent_trace_id: UUID         # FK a agent_traces (inmutable)
    created_at: datetime
    updated_at: datetime
```

---

## Value Objects

### PlanStatus
```python
class PlanStatus(str, Enum):
    PENDING_VET = "PENDING_VET"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    ARCHIVED = "ARCHIVED"
```

### PlanType
```python
class PlanType(str, Enum):
    ESTANDAR = "estándar"               # Mascota sana, sin expiración
    TEMPORAL_MEDICAL = "temporal_medical"  # Con condición médica, vet define review_date
    LIFE_STAGE = "life_stage"           # Cachorro/gatito, milestones automáticos
```

### PlanModality
```python
class PlanModality(str, Enum):
    NATURAL = "natural"        # BARF/casero — ingredientes + porciones + preparación
    CONCENTRADO = "concentrado"  # Perfil ideal + criterios de selección
```

### PlanContent (Natural)
```python
@dataclass(frozen=True)
class NaturalPlanContent:
    ingredients: list[Ingredient]   # Con gramos y porcentaje calórico
    preparation_instructions: str   # Instrucciones de preparación
    transition_protocol: str        # 7 días de transición
    weekly_schedule: list[DailyMenu]
```

### PlanContent (Concentrado)
```python
@dataclass(frozen=True)
class ConcentradoPlanContent:
    ideal_nutritional_profile: NutritionalProfile  # % proteína, grasa, fibra, etc.
    selection_criteria: list[str]                   # Criterios de selección
    daily_ration_grams: float                       # Porción en gramos
    sponsors: list[Sponsor] | None                  # Máximo 3, siempre con tag
```

---

## Máquina de Estados

```
                    ┌─────────────────────────────┐
                    │                             │
         Con condición médica                   Sin condición
                    │                             │
                    ▼                             ▼
             PENDING_VET ──────────────────► ACTIVE
             (firma vet)                      │   │
                                              │   │
                                   review_date/   │owner agrega
                                   milestone      │condición
                                              │   │
                                              ▼   ▼
                                         UNDER_REVIEW ──► PENDING_VET
                                              │
                                              ▼
                                   Nuevo plan generado
                                              │
                                              ▼
                                          ARCHIVED
```

---

## Invariantes del Aggregate

- **INV-09**: Mascota con condición médica → status inicial = `PENDING_VET`. No `ACTIVE`.
- **INV-10**: Mascota sana → status inicial = `ACTIVE`. No `PENDING_VET`.
- **INV-12**: Plan `ARCHIVED` es inmutable — sin modificaciones posibles.
- `review_date` es obligatorio para `PlanType.TEMPORAL_MEDICAL`.
- `approved_by_vet_id` solo se puede asignar si `status == PENDING_VET`.
- `rer_kcal` y `der_kcal` son inmutables post-generación (los calculó el NRCCalculator).
- Si `weight_phase == REDUCCION`: `der_kcal = RER(peso_ideal) × factores × 0.8`.

---

## Métodos del Aggregate Root

```python
def approve(self, vet_id: UUID, review_date: date | None = None) -> None:
    """
    Vet aprueba el plan. Solo válido en PENDING_VET.
    Para TEMPORAL_MEDICAL, review_date es obligatorio.
    """
    if self.status != PlanStatus.PENDING_VET:
        raise InvalidStatusTransitionError(...)
    if self.plan_type == PlanType.TEMPORAL_MEDICAL and review_date is None:
        raise ReviewDateRequiredError(...)

def archive(self, replaced_by: UUID) -> None:
    """
    Archiva el plan al generar uno nuevo.
    Solo válido en ACTIVE o UNDER_REVIEW.
    """

def trigger_review(self, reason: str) -> None:
    """
    Pasa a UNDER_REVIEW por review_date alcanzado o milestone de life_stage.
    """

def is_editable_by_vet(self) -> bool:
    return self.status == PlanStatus.PENDING_VET

def has_expired_review_date(self) -> bool:
    return (
        self.review_date is not None
        and date.today() >= self.review_date
        and self.status == PlanStatus.ACTIVE
    )
```

---

## Domain Events que Emite

| Evento | Trigger |
|--------|---------|
| `PlanGenerated` | Al crear el plan |
| `PlanActivated` | Al pasar a ACTIVE (mascota sana) |
| `PlanPendingVet` | Al crear plan con condición médica |
| `PlanApprovedByVet` | Al aprobar el vet |
| `PlanUnderReview` | Al alcanzar review_date o milestone |
| `PlanArchived` | Al ser reemplazado por nuevo plan |
