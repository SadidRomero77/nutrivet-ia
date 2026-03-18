"""
EmailAddress — value object para direcciones de correo electrónico.
Valida formato mínimo y normaliza a lowercase.
"""
import re
from dataclasses import dataclass

from backend.domain.exceptions.domain_errors import DomainError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class EmailAddress:
    """
    Dirección de email normalizada a lowercase.
    Inmutable. Valida formato básico al instanciar.
    """

    value: str

    def __post_init__(self) -> None:
        """Normaliza a lowercase y valida formato de email."""
        # frozen=True requiere object.__setattr__ para mutar en __post_init__
        normalizado = self.value.strip().lower()
        object.__setattr__(self, "value", normalizado)
        if not normalizado:
            raise DomainError("El email no puede estar vacío.")
        if not _EMAIL_PATTERN.match(normalizado):
            raise DomainError(f"Formato de email inválido: '{normalizado}'")
