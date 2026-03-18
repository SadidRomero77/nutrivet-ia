# Aggregate: PetProfile

**Bounded Context**: Pet Management
**Aggregate Root**: `PetProfile`
**Responsabilidad**: Encapsular y proteger todos los datos de la mascota garantizando consistencia.

---

## Definición del Aggregate

```python
@dataclass
class PetProfile:
    # Identidad
    pet_id: UUID                          # Generado al crear
    owner_id: UUID                        # FK a UserAccount

    # Los 13 campos obligatorios del perfil
    name: str                             # Libre — max 50 chars
    species: Species                      # Enum: PERRO | GATO
    breed: str                            # Búsqueda libre + selector
    sex: Sex                              # Enum: MACHO | HEMBRA
    age_months: int                       # En meses (>0)
    weight_kg: Decimal                    # >0, precisión 2 decimales
    size: Size | None                     # Solo perros. Enum: MINI|PEQUEÑO|MEDIANO|GRANDE|GIGANTE. None para gatos.
    reproductive_status: ReproductiveStatus  # Enum: ESTERILIZADO | NO_ESTERILIZADO
    activity_level: DogActivityLevel | CatActivityLevel  # Según especie
    bcs: BCS                              # Value Object: 1-9
    medical_conditions: list[MedicalCondition]  # 0-13 condiciones
    allergies: list[FoodAllergy]          # 0-N alergias
    current_diet: CurrentDiet             # CONCENTRADO | NATURAL | MIXTO — para protocolo transición

    # Metadata
    created_at: datetime
    updated_at: datetime
```

---

## Value Objects

### BCS (Body Condition Score)
```python
@dataclass(frozen=True)
class BCS:
    value: int  # 1-9

    def __post_init__(self):
        if not 1 <= self.value <= 9:
            raise ValueError("BCS debe estar entre 1 y 9")

    @property
    def phase(self) -> WeightPhase:
        if self.value >= 7:
            return WeightPhase.REDUCCION
        elif self.value <= 3:
            return WeightPhase.AUMENTO
        return WeightPhase.MANTENIMIENTO
```

### Species
```python
class Species(str, Enum):
    PERRO = "perro"
    GATO = "gato"
```

### Size (solo perros — gatos no tienen talla)
```python
class Size(str, Enum):
    MINI = "mini"          # XS: 1-4 kg — Chihuahua, Yorkshire, Maltés
    PEQUEÑO = "pequeño"    # S:  4-9 kg — Poodle Toy, Pomerania
    MEDIANO = "mediano"    # M:  9-14 kg — Beagle, French Bulldog
    GRANDE = "grande"      # L:  14-30 kg — Labrador, Golden Retriever
    GIGANTE = "gigante"    # XL: +30 kg — Gran Danés, San Bernardo
```

### ReproductiveStatus
```python
class ReproductiveStatus(str, Enum):
    ESTERILIZADO = "esterilizado"
    NO_ESTERILIZADO = "no_esterilizado"
    # Nota: "entero" NO se usa — nomenclatura clínica correcta es "no esterilizado"
```

### ActivityLevel — diferenciado por especie
```python
class DogActivityLevel(str, Enum):
    """Nivel de actividad para perros — multiplicador DER NRC."""
    SEDENTARIO = "sedentario"       # Factor: 1.2
    MODERADO = "moderado"           # Factor: 1.4
    ACTIVO = "activo"               # Factor: 1.6
    MUY_ACTIVO = "muy_activo"       # Factor: 1.8

class CatActivityLevel(str, Enum):
    """Nivel de actividad para gatos — basado en estándares NRC felinos."""
    INDOOR = "indoor"               # Vive solo en casa — Factor: 1.0
    INDOOR_OUTDOOR = "indoor_outdoor"  # Mixto — Factor: 1.2
    OUTDOOR = "outdoor"             # Acceso al exterior — Factor: 1.4
```

### CurrentDiet (alimentación actual — para protocolo de transición)
```python
class CurrentDiet(str, Enum):
    CONCENTRADO = "concentrado"     # Solo alimento seco/húmedo comercial
    NATURAL = "natural"             # Solo dieta BARF/casera
    MIXTO = "mixto"                 # Combinación de ambos
```

### MedicalCondition (13 condiciones soportadas)
```python
class MedicalCondition(str, Enum):
    DIABETICO = "diabético"
    HIPOTIROIDEO = "hipotiroideo"
    CANCERIGENO = "cancerígeno"         # + campo: ubicación
    ARTICULAR = "articular"
    RENAL = "renal"
    HEPATICO_HIPERLIPIDEMIA = "hepático/hiperlipidemia"
    PANCREATICO = "pancreático"
    NEURODEGENERATIVO = "neurodegenerativo"
    BUCAL_PERIODONTAL = "bucal/periodontal"
    PIEL_DERMATITIS = "piel/dermatitis"
    GASTRITIS = "gastritis"
    CISTITIS_URINARIA = "cistitis/enfermedad_urinaria"
    SOBREPESO_OBESIDAD = "sobrepeso/obesidad"
```

---

## Invariantes del Aggregate

- `weight_kg` debe ser > 0. Si es 0 o negativo → `InvalidWeightError`.
- `age_months` debe ser > 0.
- `bcs` debe estar entre 1 y 9.
- `medical_conditions` no puede contener duplicados.
- `allergies` no puede contener duplicados.
- `name` no puede estar vacío.
- Si `species == GATO` → `size` debe ser `None`. Los gatos no tienen clasificación de talla.
- Si `species == PERRO` → `size` es obligatorio (no puede ser `None`).
- Si `species == PERRO` → `activity_level` debe ser instancia de `DogActivityLevel`.
- Si `species == GATO` → `activity_level` debe ser instancia de `CatActivityLevel`.
- El peso de la mascota debe ser consistente con su talla declarada (±50% del rango). Si hay discrepancia grave, advertencia — no bloqueo.
- `current_diet` es obligatorio — debe estar definido antes de generar el plan.

---

## Domain Events que Emite

| Evento | Trigger |
|--------|---------|
| `PetProfileCreated` | Al completar el wizard (todos los 12 campos) |
| `PetProfileUpdated` | Al modificar cualquier campo |
| `MedicalConditionAdded` | Al agregar una condición médica |
| `AllergyRegistered` | Al agregar una alergia |

---

## Métodos del Aggregate Root

```python
def add_medical_condition(self, condition: MedicalCondition) -> None:
    """
    Agrega una condición médica. Si el owner tiene un plan ACTIVE,
    emite MedicalConditionAdded para triggear re-evaluación.
    """

def remove_medical_condition(self, condition: MedicalCondition) -> None:
    """
    Remueve una condición médica. Requiere confirmación explícita del owner.
    """

def update_bcs(self, new_bcs: BCS) -> None:
    """
    Actualiza el BCS. Puede cambiar la fase del Weight Journey.
    """

def update_weight(self, new_weight_kg: Decimal) -> None:
    """
    Actualiza el peso. Recalcula estimado de peso ideal si en fase reducción.
    """

def requires_vet_review(self) -> bool:
    """
    True si tiene al menos una condición médica registrada.
    Determina si el plan generado irá a PENDING_VET o ACTIVE.
    """
    return len(self.medical_conditions) > 0

def llm_routing_key(self) -> int:
    """
    Retorna el número de condiciones médicas para el LLM routing.
    0 → Ollama · 1-2 → Groq · 3+ → GPT-4o
    """
    return len(self.medical_conditions)
```

---

## Caso Sally — Ejemplo de PetProfile

```python
sally = PetProfile(
    name="Sally",
    species=Species.PERRO,
    breed="French Poodle",
    sex=Sex.HEMBRA,
    age_months=96,                              # 8 años
    weight_kg=Decimal("9.6"),
    size=Size.PEQUEÑO,                          # 4-9 kg — French Poodle encaja en PEQUEÑO
    reproductive_status=ReproductiveStatus.ESTERILIZADO,
    activity_level=DogActivityLevel.SEDENTARIO,
    bcs=BCS(6),                                 # Fase Mantenimiento
    medical_conditions=[
        MedicalCondition.DIABETICO,
        MedicalCondition.HEPATICO_HIPERLIPIDEMIA,
        MedicalCondition.GASTRITIS,
        MedicalCondition.CISTITIS_URINARIA,
        MedicalCondition.HIPOTIROIDEO,           # 5 condiciones confirmadas por Lady Carolina
    ],
    allergies=[],
    current_diet=CurrentDiet.CONCENTRADO        # Dato a confirmar con el owner
)

assert sally.requires_vet_review() == True
assert sally.llm_routing_key() == 5             # 5 condiciones → GPT-4o ✓
assert sally.bcs.phase == WeightPhase.MANTENIMIENTO
# RER = 70 × 9.6^0.75 ≈ 396 kcal
# DER = 396 × factores ≈ 534 kcal/día
```
