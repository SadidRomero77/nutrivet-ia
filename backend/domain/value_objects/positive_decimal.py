"""
PositiveDecimal — value object para valores numéricos positivos (peso, cantidades).
Garantiza que el valor sea mayor a cero.
"""
from dataclasses import dataclass

from backend.domain.exceptions.domain_errors import InvalidWeightError


@dataclass(frozen=True)
class PositiveDecimal:
    """
    Valor decimal positivo estrictamente mayor a cero.
    Usado para peso (kg), porciones en gramos y otras medidas físicas.
    """

    value: float

    def __post_init__(self) -> None:
        """Valida que el valor sea estrictamente positivo."""
        if self.value <= 0:
            raise InvalidWeightError(self.value)
