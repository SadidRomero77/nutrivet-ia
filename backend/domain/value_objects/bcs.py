"""
BCS — Body Condition Score (1-9) para perros y gatos.
Determina la fase del plan nutricional (reducción / mantenimiento / aumento).
"""
from dataclasses import dataclass
from enum import Enum

from backend.domain.exceptions.domain_errors import InvalidBCSError


class BCSPhase(str, Enum):
    """Fase nutricional determinada por el BCS."""

    REDUCCION = "reduccion"       # BCS 7-9: exceso de peso
    MANTENIMIENTO = "mantenimiento"  # BCS 4-6: peso ideal
    AUMENTO = "aumento"           # BCS 1-3: bajo peso


_BCS_MIN = 1
_BCS_MAX = 9


@dataclass(frozen=True)
class BCS:
    """
    Body Condition Score — escala 1 a 9.
    Inmutable (frozen=True). Determina phase y der_modifier para el cálculo DER.
    """

    value: int

    def __post_init__(self) -> None:
        """Valida que el BCS esté dentro del rango 1-9."""
        if not (_BCS_MIN <= self.value <= _BCS_MAX):
            raise InvalidBCSError(self.value)

    @property
    def phase(self) -> BCSPhase:
        """Retorna la fase nutricional según el BCS."""
        if self.value >= 7:
            return BCSPhase.REDUCCION
        if self.value <= 3:
            return BCSPhase.AUMENTO
        return BCSPhase.MANTENIMIENTO

    @property
    def der_modifier(self) -> float:
        """
        Modificador del DER según la fase:
        - Reducción (BCS 7-9): 0.8 aplicado sobre RER de peso ideal
        - Mantenimiento (BCS 4-6): 1.0
        - Aumento (BCS 1-3): 1.2
        """
        if self.phase == BCSPhase.REDUCCION:
            return 0.8
        if self.phase == BCSPhase.AUMENTO:
            return 1.2
        return 1.0
