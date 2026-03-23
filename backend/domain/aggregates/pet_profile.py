"""
PetProfile — Aggregate raíz del contexto Pet Management.
Encapsula los 13 campos obligatorios con sus invariantes de dominio.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID

from backend.domain.exceptions.domain_errors import DomainError, InvalidWeightError
from backend.domain.value_objects.bcs import BCS


# ---------------------------------------------------------------------------
# Enums del aggregate
# ---------------------------------------------------------------------------

class Species(str, Enum):
    """Especie de la mascota — determina listas de tóxicos y factores NRC."""
    PERRO = "perro"
    GATO = "gato"


class Sex(str, Enum):
    MACHO = "macho"
    HEMBRA = "hembra"


class Size(str, Enum):
    """Talla del perro. Solo aplica a perros — gatos usan None."""
    MINI = "mini"          # XS: 1-4 kg
    PEQUEÑO = "pequeño"    # S:  4-9 kg
    MEDIANO = "mediano"    # M:  9-14 kg
    GRANDE = "grande"      # L:  14-30 kg
    GIGANTE = "gigante"    # XL: +30 kg


class ReproductiveStatus(str, Enum):
    ESTERILIZADO = "esterilizado"
    NO_ESTERILIZADO = "no_esterilizado"
    GESTANTE = "gestante"      # hembra en gestación — factores NRC especiales
    LACTANTE = "lactante"      # hembra en lactancia — factores NRC especiales


class DogActivityLevel(str, Enum):
    """Nivel de actividad para perros."""
    SEDENTARIO = "sedentario"
    MODERADO = "moderado"
    ACTIVO = "activo"
    MUY_ACTIVO = "muy_activo"


class CatActivityLevel(str, Enum):
    """Nivel de actividad para gatos."""
    INDOOR = "indoor"
    INDOOR_OUTDOOR = "indoor_outdoor"
    OUTDOOR = "outdoor"


class CurrentDiet(str, Enum):
    """Alimentación actual — usada para protocolo de transición."""
    CONCENTRADO = "concentrado"
    NATURAL = "natural"
    MIXTO = "mixto"


class MedicalCondition(str, Enum):
    """Las 17 condiciones médicas soportadas por NutriVet.IA."""
    # Originales (13)
    DIABETICO = "diabético"
    HIPOTIROIDEO = "hipotiroideo"
    CANCERIGENO = "cancerígeno"
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
    # Nuevas (4) — validadas por Lady Carolina Castañeda (MV, BAMPYSVET)
    INSUFICIENCIA_CARDIACA = "insuficiencia_cardiaca"
    CUSHING = "hiperadrenocorticismo_cushing"
    EPILEPSIA = "epilepsia"
    MEGAESOFAGO = "megaesofago"


_DOG_ACTIVITY_VALUES = frozenset(e.value for e in DogActivityLevel)
_CAT_ACTIVITY_VALUES = frozenset(e.value for e in CatActivityLevel)
_VALID_CONDITION_VALUES = frozenset(e.value for e in MedicalCondition)


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

@dataclass
class PetProfile:
    """
    Aggregate raíz: PetProfile.
    Encapsula los 13 campos del wizard con invariantes de dominio.
    """

    # Identidad
    pet_id: UUID
    owner_id: UUID

    # Los 13 campos obligatorios
    name: str
    species: Species
    breed: str
    sex: Sex
    age_months: int
    weight_kg: float
    size: Size | None
    reproductive_status: ReproductiveStatus
    activity_level: DogActivityLevel | CatActivityLevel
    bcs: BCS
    medical_conditions: list[MedicalCondition] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    current_diet: CurrentDiet = CurrentDiet.CONCENTRADO
    is_clinic_pet: bool = False
    vet_id: Optional[UUID] = None
    # Campos adicionales para estados reproductivos especiales
    num_offspring: int = 0          # Número de crías (lactante) o esperados (gestante)
    gestation_week: int = 0         # Semana de gestación 1-9 (0 = desconocida)
    breed_id: Optional[str] = None  # ID de raza del catálogo (A-01)

    def __post_init__(self) -> None:
        """Valida todas las invariantes del aggregate al instanciar."""
        self._validate_name()
        self._validate_weight()
        self._validate_size_by_species()
        self._validate_activity_by_species()
        self._validate_medical_conditions()

    # --- Invariantes ---

    def _validate_name(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainError("El nombre de la mascota no puede estar vacío.")

    def _validate_weight(self) -> None:
        if self.weight_kg <= 0:
            raise InvalidWeightError(self.weight_kg)

    def _validate_size_by_species(self) -> None:
        if self.species == Species.PERRO and self.size is None:
            raise DomainError(
                "Los perros requieren una talla (size). "
                "Opciones: mini, pequeño, mediano, grande, gigante."
            )
        if self.species == Species.GATO and self.size is not None:
            raise DomainError(
                "Los gatos no tienen clasificación de talla. "
                "El campo 'size' debe ser None para gatos."
            )

    def _validate_activity_by_species(self) -> None:
        activity_val = (
            self.activity_level.value
            if isinstance(self.activity_level, Enum)
            else str(self.activity_level)
        )
        if self.species == Species.PERRO and activity_val not in _DOG_ACTIVITY_VALUES:
            raise DomainError(
                f"Nivel de actividad inválido para perro: '{activity_val}'. "
                f"Válidos: {sorted(_DOG_ACTIVITY_VALUES)}"
            )
        if self.species == Species.GATO and activity_val not in _CAT_ACTIVITY_VALUES:
            raise DomainError(
                f"Nivel de actividad inválido para gato: '{activity_val}'. "
                f"Válidos: {sorted(_CAT_ACTIVITY_VALUES)}"
            )

    def _validate_medical_conditions(self) -> None:
        seen: set[str] = set()
        for cond in self.medical_conditions:
            val = cond.value if isinstance(cond, MedicalCondition) else str(cond)
            if val not in _VALID_CONDITION_VALUES:
                raise DomainError(
                    f"Condición médica desconocida: '{val}'. "
                    f"Válidas: {sorted(_VALID_CONDITION_VALUES)}"
                )
            if val in seen:
                raise DomainError(
                    f"Condición médica duplicada: '{val}'. "
                    "Cada condición puede aparecer solo una vez."
                )
            seen.add(val)

    # --- Métodos del dominio ---

    def requires_vet_review(self) -> bool:
        """
        True si la mascota tiene al menos una condición médica.
        Determina si el plan irá a PENDING_VET o ACTIVE.
        Constitution REGLA 4.
        """
        return len(self.medical_conditions) > 0

    def llm_routing_key(self) -> int:
        """
        Número de condiciones médicas para el LLM routing.
        0 → llama-3.3-70b · 1-2 → gpt-4o-mini · 3+ → claude-sonnet-4-5
        Constitution REGLA 5.
        """
        return len(self.medical_conditions)

    def add_medical_condition(self, condition: MedicalCondition) -> None:
        """
        Agrega una condición médica. No permite duplicados.
        Si la mascota tiene un plan ACTIVE, el plan debe volver a PENDING_VET
        (ese trigger lo maneja el application layer, no este aggregate).
        """
        if condition in self.medical_conditions:
            raise DomainError(
                f"La condición '{condition.value}' ya está registrada."
            )
        self.medical_conditions.append(condition)

    def remove_medical_condition(self, condition: MedicalCondition) -> None:
        """Remueve una condición médica si existe."""
        if condition not in self.medical_conditions:
            raise DomainError(
                f"La condición '{condition.value}' no está registrada."
            )
        self.medical_conditions.remove(condition)

    def update_bcs(self, new_bcs: BCS) -> None:
        """Actualiza el BCS. Puede cambiar la fase del Weight Journey."""
        self.bcs = new_bcs

    def update_weight(self, new_weight_kg: float) -> None:
        """Actualiza el peso. Valida que sea positivo."""
        if new_weight_kg <= 0:
            raise InvalidWeightError(new_weight_kg)
        self.weight_kg = new_weight_kg
