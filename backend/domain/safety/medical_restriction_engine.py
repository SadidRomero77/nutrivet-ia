"""
MedicalRestrictionEngine — Motor de restricciones médicas determinista.
Constitution REGLA 2: el LLM NO puede sobrescribir RESTRICTIONS_BY_CONDITION.

Este módulo es Python puro — cero dependencias externas.
"""
import unicodedata
from dataclasses import dataclass

from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.safety.medical_restrictions import (
    RESTRICTIONS_BY_CONDITION,
    VALID_CONDITIONS,
    ConditionRestrictions,
)


def _tokenize(text: str) -> frozenset[str]:
    """
    Convierte un texto en un frozenset de tokens normalizados.

    Normaliza:
    - Minúsculas
    - Reemplaza guiones bajos por espacios (términos como "fósforo_alto")
    - Elimina caracteres no alfanuméricos (excepto espacios)

    Ejemplo: "fósforo_alto" → {"fósforo", "alto"}
    """
    normalized = unicodedata.normalize("NFC", text.lower().replace("_", " "))
    return frozenset(t for t in normalized.split() if t)


def _terms_match(ingredient: str, restriction_term: str) -> bool:
    """
    Verifica si un ingrediente hace match con un término de restricción.

    Usa intersección de tokens para evitar falsos positivos por substring:
    - "grasa" NO hace match con "grasas totales mayor 10pct ms" (tokens distintos)
    - "fósforo" SÍ hace match con "fósforo alto" (token "fósforo" compartido)
    - "proteína de pollo" NO hace match con "proteína alta densidad" (sin tokens comunes
      que sean términos restrictivos — salvo "proteína", que sí compartiría)

    La intersección de tokens es más precisa que substring bidireccional y evita
    el caso documentado: "sal" como substring de "ensalada" o "grasa" dentro de
    "grasas totales mayor 10pct ms".

    Args:
        ingredient: Nombre del ingrediente del plan (ej. "pollo", "fósforo").
        restriction_term: Término de la restricción (ej. "fósforo_alto").

    Returns:
        True si hay coincidencia de al menos un token.
    """
    ingredient_tokens = _tokenize(ingredient)
    restriction_tokens = _tokenize(restriction_term)
    return bool(ingredient_tokens & restriction_tokens)


@dataclass(frozen=True)
class RestrictionResult:
    """Resultado de validar un ingrediente contra las condiciones médicas."""

    ingredient: str
    condition: str
    is_violation: bool
    category: str = ""  # "prohibited" | "limited" | ""
    reason: str = ""


class MedicalRestrictionEngine:
    """
    Motor estático de restricciones médicas.
    Todos los métodos son de clase — no requiere instanciación.
    """

    @classmethod
    def get_restrictions_for_conditions(
        cls, conditions: list[str]
    ) -> ConditionRestrictions:
        """
        Retorna las restricciones unificadas para una lista de condiciones médicas.

        Si hay múltiples condiciones, las restricciones se unen (principio
        de máxima restricción — siempre se aplica lo más conservador).

        Args:
            conditions: Lista de condiciones médicas (strings exactos).

        Returns:
            ConditionRestrictions con la unión de todas las restricciones.

        Raises:
            DomainError: Si alguna condición no es válida.
        """
        for condicion in conditions:
            if condicion not in VALID_CONDITIONS:
                raise DomainError(
                    f"Condición médica desconocida: '{condicion}'. "
                    f"Válidas: {sorted(VALID_CONDITIONS)}"
                )

        if not conditions:
            return ConditionRestrictions()

        # Unión de todas las restricciones (más restrictivo = más seguro)
        all_prohibited: set[str] = set()
        all_limited: set[str] = set()
        all_recommended: set[str] = set()
        all_special_rules: set[str] = set()

        for condicion in conditions:
            r = RESTRICTIONS_BY_CONDITION[condicion]
            all_prohibited |= r.prohibited
            all_limited |= r.limited
            all_recommended |= r.recommended
            all_special_rules |= r.special_rules

        return ConditionRestrictions(
            prohibited=frozenset(all_prohibited),
            limited=frozenset(all_limited),
            recommended=frozenset(all_recommended),
            special_rules=frozenset(all_special_rules),
        )

    @classmethod
    def validate_ingredient_against_conditions(
        cls, ingredient: str, conditions: list[str]
    ) -> list[RestrictionResult]:
        """
        Verifica si un ingrediente viola alguna restricción de las condiciones dadas.

        Nota: La validación semántica completa (ej. detectar que "miel" es un
        azúcar simple) requiere un mapa de categorías de ingredientes que vive
        en infrastructure. Este método valida contra los términos exactos de
        las restricciones y palabras clave en el texto del ingrediente.

        Args:
            ingredient: Nombre del ingrediente.
            conditions: Lista de condiciones médicas.

        Returns:
            Lista de RestrictionResult. Violaciones tienen is_violation=True.
        """
        if not conditions:
            return []

        restricciones = cls.get_restrictions_for_conditions(conditions)
        ingrediente_lower = ingredient.lower()
        resultados: list[RestrictionResult] = []

        # Verificar contra términos prohibidos con matching por token (no substring)
        for termino_prohibido in restricciones.prohibited:
            if _terms_match(ingredient, termino_prohibido):
                resultados.append(RestrictionResult(
                    ingredient=ingredient,
                    condition=_find_condition_for_rule(termino_prohibido, conditions),
                    is_violation=True,
                    category="prohibited",
                    reason=(
                        f"'{ingredient}' coincide con '{termino_prohibido}' — "
                        f"prohibido por restricción médica."
                    ),
                ))

        # Si no hay violaciones encontradas, retornar resultado limpio
        if not resultados:
            resultados.append(RestrictionResult(
                ingredient=ingredient,
                condition="",
                is_violation=False,
                category="",
                reason="Sin violaciones detectadas.",
            ))

        return resultados


def _find_condition_for_rule(rule: str, conditions: list[str]) -> str:
    """Encuentra qué condición define una regla dada (para trazabilidad)."""
    for condicion in conditions:
        r = RESTRICTIONS_BY_CONDITION.get(condicion)
        if r and (rule in r.prohibited or rule in r.limited or rule in r.special_rules):
            return condicion
    return "desconocida"
