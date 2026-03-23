"""
FoodSafetyChecker — Verificación determinista de toxicidad y seguridad alimentaria.
Constitution REGLA 1: tolerancia CERO — un ingrediente tóxico = plan rechazado.

Incluye verificaciones adicionales:
- Tiaminasa en pescado crudo (riesgo neurológico en gatos) — B-03/A-02
- Lipidosis hepática felina por ayuno (C-06)

Este módulo es Python puro. Cero dependencias externas. Cero llamadas a LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.domain.safety.toxic_foods import (
    SCIENTIFIC_ALIASES,
    TOXIC_CATS,
    TOXIC_DOGS,
)

# ---------------------------------------------------------------------------
# Alimentos crudos con tiaminasa activa — CRÍTICO para gatos
# La cocción destruye la tiaminasa. Solo aplica a dieta cruda (BARF/natural).
# Fuente: NRC 2006, Thiaminase activity in fish — Int J Vitam Nutr Res 1992
# ---------------------------------------------------------------------------
_TIAMINASA_INGREDIENTS: frozenset[str] = frozenset({
    "sardina cruda", "sardinas crudas",
    "atún crudo", "salmón crudo",
    "tilapia cruda", "trucha cruda",
    "carpa cruda", "carpa",
    "arenque crudo",
    "pescado crudo", "pez crudo",
    "bacalao crudo",
})


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

    @classmethod
    def check_tiaminasa_risk(
        cls,
        ingredients: list[str],
        species: str,
        diet_type: str = "natural",
    ) -> Optional[str]:
        """
        Verifica riesgo de deficiencia de tiamina (B1) por tiaminasa en pescado crudo.

        Solo aplica a GATOS con dieta natural/BARF. La cocción destruye la tiaminasa
        — sardinas enlatadas y pescado cocido son seguros.

        Args:
            ingredients: Lista de nombres de ingredientes del plan.
            species:     "perro" | "gato".
            diet_type:   "natural" | "barf" | "concentrado" | "mixto".

        Returns:
            Mensaje de alerta (str) si hay riesgo, None si es seguro.
        """
        if species != "gato":
            return None
        if diet_type not in ("natural", "barf"):
            return None

        normalized = {cls._normalize(ing) for ing in ingredients}
        risky = normalized & _TIAMINASA_INGREDIENTS
        if risky:
            items = ", ".join(sorted(risky))
            return (
                f"ALERTA TIAMINASA — GATOS: {items} contiene(n) tiaminasa activa "
                "que destruye la vitamina B1 (tiamina). Riesgo de convulsiones y daño "
                "neurológico irreversible. Opciones seguras: (1) cocinar el pescado, "
                "(2) reemplazar por sardinas en agua enlatadas (cocidas), "
                "(3) suplementar tiamina 1-2 mg/kg/día si el plan incluye pescado crudo."
            )
        return None

    @classmethod
    def check_feline_fasting_risk(
        cls,
        species: str,
        hours_without_food: Optional[int],
        conditions: list[str] | None = None,
    ) -> Optional[str]:
        """
        Alerta crítica de lipidosis hepática (hígado graso) en gatos en ayuno.

        Un gato que no come > 24 horas está en riesgo real de lipidosis hepática,
        una emergencia médica potencialmente letal. El riesgo es MAYOR en gatos
        con sobrepeso/obesidad — paradójicamente son los más susceptibles.

        Args:
            species:            "perro" | "gato".
            hours_without_food: Horas sin comer (None = desconocido).
            conditions:         Condiciones médicas activas (para detectar sobrepeso).

        Returns:
            Mensaje de alerta urgente (str) si aplica, None si no aplica.
        """
        if species != "gato":
            return None
        if hours_without_food is None:
            return None

        conditions_set = set(conditions or [])
        tiene_sobrepeso = "sobrepeso/obesidad" in conditions_set

        if hours_without_food >= 48:
            base = (
                "⚠️ EMERGENCIA VETERINARIA — LIPIDOSIS HEPÁTICA: "
                f"El gato lleva {hours_without_food} horas sin comer. "
                "La lipidosis hepática (hígado graso) es una emergencia médica letal. "
                "Acudir a urgencias veterinarias INMEDIATAMENTE. No esperar."
            )
            if tiene_sobrepeso:
                base += (
                    " RIESGO CRÍTICO ELEVADO: el sobrepeso aumenta significativamente "
                    "la susceptibilidad a lipidosis con ayunos breves."
                )
            return base

        if hours_without_food >= 24:
            msg = (
                "⚠️ ALERTA LIPIDOSIS HEPÁTICA: El gato lleva "
                f"{hours_without_food} horas sin comer. "
                "En gatos, el ayuno de 24-48h puede desencadenar lipidosis hepática. "
                "Contactar al veterinario hoy. Intentar estimular el apetito "
                "(calentar la comida, cambiar textura). Si no come en las próximas "
                "4-6 horas, acudir a urgencias."
            )
            if tiene_sobrepeso:
                msg += " ATENCIÓN ESPECIAL: el sobrepeso eleva el riesgo."
            return msg

        return None

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
