"""
FoodSafetyChecker — Verificación determinista de toxicidad de alimentos.
Constitution REGLA 1: tolerancia CERO — un ingrediente tóxico = plan rechazado.

Este módulo es Python puro. Cero dependencias externas. Cero llamadas a LLM.
"""
from dataclasses import dataclass, field

from backend.domain.safety.toxic_foods import (
    SCIENTIFIC_ALIASES,
    TOXIC_CATS,
    TOXIC_DOGS,
)


@dataclass(frozen=True)
class ToxicityResult:
    """Resultado de la verificación de toxicidad para un ingrediente."""

    ingredient: str
    is_toxic: bool
    affects_species: frozenset[str] = field(default_factory=frozenset)
    reason: str = ""

    def __post_init__(self) -> None:
        # Convertir set mutable a frozenset si se pasó uno
        if isinstance(self.affects_species, set):
            object.__setattr__(self, "affects_species", frozenset(self.affects_species))


_VALID_SPECIES = frozenset({"perro", "gato"})


class FoodSafetyChecker:
    """
    Verificador estático de toxicidad de ingredientes.
    Todos los métodos son de clase — no requiere instanciación.
    """

    @classmethod
    def check_ingredient(cls, ingredient: str, species: str) -> ToxicityResult:
        """
        Verifica si un ingrediente es tóxico para la especie indicada.

        La verificación es case-insensitive y detecta nombres científicos
        y aliases definidos en SCIENTIFIC_ALIASES.

        Args:
            ingredient: Nombre del ingrediente (texto libre).
            species: "perro" | "gato".

        Returns:
            ToxicityResult con is_toxic=True si el ingrediente es peligroso.
        """
        normalizado = cls._normalize(ingredient)
        # Resolver alias científicos o regionales
        canónico = SCIENTIFIC_ALIASES.get(normalizado, normalizado)

        lista_especie = cls._get_toxic_set_for_species(species)
        is_toxic = canónico in lista_especie or normalizado in lista_especie

        # Determinar qué especies afecta (para ingredientes que afectan a ambas)
        affects: set[str] = set()
        if canónico in TOXIC_DOGS or normalizado in TOXIC_DOGS:
            affects.add("perro")
        if canónico in TOXIC_CATS or normalizado in TOXIC_CATS:
            affects.add("gato")

        reason = ""
        if is_toxic:
            reason = (
                f"'{ingredient}' es tóxico para {species}. "
                "Tolerancia cero — ingrediente bloqueado. "
                "Fuente: TOXIC_DOGS/TOXIC_CATS NutriVet.IA domain layer."
            )

        return ToxicityResult(
            ingredient=ingredient,
            is_toxic=is_toxic,
            affects_species=frozenset(affects),
            reason=reason,
        )

    @classmethod
    def validate_plan_ingredients(
        cls, ingredients: list[str], species: str
    ) -> list[ToxicityResult]:
        """
        Verifica todos los ingredientes de un plan nutricional.

        Args:
            ingredients: Lista de nombres de ingredientes.
            species: "perro" | "gato".

        Returns:
            Lista de ToxicityResult, uno por ingrediente.
            Los tóxicos tienen is_toxic=True.

        Raises:
            ValueError: Si la especie no es válida.
        """
        if species not in _VALID_SPECIES:
            raise ValueError(
                f"Especie inválida: '{species}'. Válidas: {sorted(_VALID_SPECIES)}"
            )
        return [cls.check_ingredient(ing, species) for ing in ingredients]

    @classmethod
    def get_toxic_list_for_species(cls, species: str) -> frozenset[str]:
        """
        Retorna la lista de tóxicos para la especie.
        Siempre retorna un frozenset — inmutable por diseño.

        Args:
            species: "perro" | "gato".

        Returns:
            frozenset con los nombres canónicos de ingredientes tóxicos.
        """
        return cls._get_toxic_set_for_species(species)

    # --- Métodos privados ---

    @classmethod
    def _normalize(cls, ingredient: str) -> str:
        """Normaliza a lowercase con espacios limpios."""
        return ingredient.strip().lower()

    @classmethod
    def _get_toxic_set_for_species(cls, species: str) -> frozenset[str]:
        """Retorna el frozenset de tóxicos según especie."""
        if species == "perro":
            return TOXIC_DOGS
        elif species == "gato":
            return TOXIC_CATS
        else:
            raise ValueError(
                f"Especie inválida: '{species}'. Válidas: 'perro', 'gato'"
            )
