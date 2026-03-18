"""
Excepciones del domain layer — NutriVet.IA
Todas las excepciones de dominio heredan de DomainError.
"""


class DomainError(Exception):
    """Error base del domain layer. Nunca lanzar Exception directamente."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ToxicIngredientError(DomainError):
    """Ingrediente presente en TOXIC_DOGS o TOXIC_CATS — tolerancia cero."""

    def __init__(self, ingrediente: str, especie: str, lista: str) -> None:
        super().__init__(
            f"'{ingrediente}' es tóxico para {especie} (lista {lista})"
        )
        self.ingrediente = ingrediente
        self.especie = especie
        self.lista = lista


class MedicalRestrictionViolationError(DomainError):
    """Ingrediente o elemento viola una restricción médica hard-coded."""

    def __init__(self, condicion: str, elemento: str, razon: str) -> None:
        super().__init__(
            f"Violación de restricción '{condicion}': '{elemento}' — {razon}"
        )
        self.condicion = condicion
        self.elemento = elemento
        self.razon = razon


class InvalidWeightError(DomainError):
    """Peso inválido — debe ser un valor positivo mayor a cero."""

    def __init__(self, valor: float) -> None:
        super().__init__(f"Peso inválido: {valor}. Debe ser mayor a 0.")
        self.valor = valor


class InvalidBCSError(DomainError):
    """BCS fuera de rango válido (1-9)."""

    def __init__(self, valor: int) -> None:
        super().__init__(f"BCS inválido: {valor}. Debe estar entre 1 y 9.")
        self.valor = valor


class NRCCalculationError(DomainError):
    """Error en el cálculo NRC/DER — datos insuficientes o inválidos."""

    def __init__(self, razon: str) -> None:
        super().__init__(f"Error en cálculo NRC: {razon}")
