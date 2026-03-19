"""
NutritionPlan — Aggregate raíz del contexto Nutrition Planning.
Máquina de estados: PENDING_VET → ACTIVE → UNDER_REVIEW → ARCHIVED.

Constitution REGLA 4:
  - Mascota sana → ACTIVE directo.
  - Mascota con condición médica → PENDING_VET → firma vet → ACTIVE.
  - Plan ACTIVE al que se agrega condición médica → vuelve a PENDING_VET.
"""
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any
from uuid import UUID

from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.value_objects.bcs import BCSPhase


# ---------------------------------------------------------------------------
# Enums del aggregate
# ---------------------------------------------------------------------------

class PlanStatus(str, Enum):
    PENDING_VET = "PENDING_VET"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    ARCHIVED = "ARCHIVED"


class PlanType(str, Enum):
    ESTANDAR = "estándar"
    TEMPORAL_MEDICAL = "temporal_medical"
    LIFE_STAGE = "life_stage"


class PlanModality(str, Enum):
    NATURAL = "natural"
    CONCENTRADO = "concentrado"


# ---------------------------------------------------------------------------
# Aggregate Root
# ---------------------------------------------------------------------------

@dataclass
class NutritionPlan:
    """
    Aggregate raíz: NutritionPlan.
    Encapsula el ciclo de vida del plan nutricional con máquina de estados.
    """

    # Identidad
    plan_id: UUID
    pet_id: UUID
    owner_id: UUID

    # Tipo y estado
    plan_type: PlanType
    status: PlanStatus
    modality: PlanModality

    # Cálculo nutricional (determinista — inmutable post-creación)
    rer_kcal: float
    der_kcal: float
    weight_phase: BCSPhase
    llm_model_used: str

    # Contenido generado por LLM con guardarraíles
    content: dict[str, Any]

    # HITL
    approved_by_vet_id: UUID | None
    approval_timestamp: datetime | None
    review_date: date | None
    vet_comment: str | None

    # Trazabilidad (inmutable post-creación)
    agent_trace_id: UUID

    # --- Métodos del dominio ---

    def approve(self, vet_id: UUID, review_date: date | None = None) -> None:
        """
        Vet aprueba el plan: PENDING_VET → ACTIVE.
        Para TEMPORAL_MEDICAL, review_date es obligatorio.

        Raises:
            DomainError: Si el plan no está en PENDING_VET.
            DomainError: Si es TEMPORAL_MEDICAL y no se provee review_date.
        """
        if self.status != PlanStatus.PENDING_VET:
            raise DomainError(
                f"Solo se puede aprobar un plan en PENDING_VET. "
                f"Estado actual: '{self.status.value}'."
            )
        if self.plan_type == PlanType.TEMPORAL_MEDICAL and review_date is None:
            raise DomainError(
                "Los planes de tipo 'temporal_medical' requieren una fecha de "
                "revisión (review_date) al momento de la aprobación veterinaria."
            )
        self.status = PlanStatus.ACTIVE
        self.approved_by_vet_id = vet_id
        self.approval_timestamp = datetime.utcnow()
        if review_date is not None:
            self.review_date = review_date

    def return_to_owner(self, vet_id: UUID, comment: str) -> None:
        """
        Vet devuelve el plan al owner con comentario obligatorio.
        El plan permanece en PENDING_VET.

        Raises:
            DomainError: Si el comentario está vacío.
            DomainError: Si el plan no está en PENDING_VET.
        """
        if self.status != PlanStatus.PENDING_VET:
            raise DomainError(
                f"Solo se puede devolver un plan en PENDING_VET. "
                f"Estado actual: '{self.status.value}'."
            )
        if not comment or not comment.strip():
            raise DomainError(
                "El comentario del veterinario es obligatorio al devolver un plan. "
                "Indica qué debe corregirse."
            )
        self.vet_comment = comment.strip()

    def archive(self, replaced_by: UUID) -> None:
        """
        Archiva el plan al ser reemplazado por uno nuevo.
        Solo válido en ACTIVE o UNDER_REVIEW. Plan ARCHIVED es inmutable.

        Raises:
            DomainError: Si el plan ya está ARCHIVED.
            DomainError: Si el plan está en PENDING_VET (no se puede archivar sin activar).
        """
        if self.status == PlanStatus.ARCHIVED:
            raise DomainError("El plan ya está archivado — es inmutable.")
        if self.status == PlanStatus.PENDING_VET:
            raise DomainError(
                "No se puede archivar un plan en PENDING_VET. "
                "Solo planes ACTIVE o UNDER_REVIEW pueden archivarse."
            )
        self.status = PlanStatus.ARCHIVED

    def trigger_review(self, reason: str) -> None:
        """ACTIVE → UNDER_REVIEW por review_date alcanzado o milestone de life_stage."""
        if self.status != PlanStatus.ACTIVE:
            raise DomainError(
                f"Solo se puede iniciar revisión desde ACTIVE. "
                f"Estado actual: '{self.status.value}'."
            )
        self.status = PlanStatus.UNDER_REVIEW

    def add_medical_condition_requires_review(self) -> None:
        """
        Constitution REGLA 4: si el owner agrega una condición médica a un plan
        ACTIVE, el plan vuelve a PENDING_VET para revisión veterinaria.
        """
        if self.status == PlanStatus.ACTIVE:
            self.status = PlanStatus.PENDING_VET
            self.approved_by_vet_id = None
            self.approval_timestamp = None

    def can_export(self) -> bool:
        """
        True solo si el plan está en ACTIVE.
        Solo planes activos son exportables a PDF / compartibles.
        """
        return self.status == PlanStatus.ACTIVE

    def is_editable_by_vet(self) -> bool:
        """True si el vet puede editar el plan (solo en PENDING_VET)."""
        return self.status == PlanStatus.PENDING_VET

    def has_expired_review_date(self) -> bool:
        """True si el review_date ya se alcanzó y el plan sigue ACTIVE."""
        return (
            self.review_date is not None
            and date.today() >= self.review_date
            and self.status == PlanStatus.ACTIVE
        )
