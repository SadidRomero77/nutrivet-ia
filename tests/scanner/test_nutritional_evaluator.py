"""
Tests RED — NutritionalEvaluator Semáforo (NUT-72 · Paso 3).

Semáforo determinístico (sin LLM):
  tóxicos → ROJO
  restricciones médicas → ROJO
  alergias → AMARILLO
  desequilibrio nutricional → AMARILLO
  todo OK → VERDE
"""
from __future__ import annotations

import pytest

from backend.infrastructure.agent.nodes.nutritional_evaluator import (
    SEMAPHORE_ROJO,
    SEMAPHORE_AMARILLO,
    SEMAPHORE_VERDE,
    SemaphoreResult,
    evaluate_semaphore,
)


def _pet_profile(
    species: str = "perro",
    conditions: list[str] | None = None,
    allergies: list[str] | None = None,
) -> dict:
    return {
        "species": species,
        "medical_conditions": conditions or [],
        "allergies": allergies or [],
    }


class TestNutritionalEvaluator:
    """Semáforo determinístico — sin LLM."""

    def test_toxico_semaforo_rojo(self) -> None:
        """Ingrediente tóxico (cebolla) para perro → ROJO (REGLA 1)."""
        result = evaluate_semaphore(
            ingredients=["pollo", "arroz", "cebolla"],
            nutritional_profile={},
            pet_profile=_pet_profile(species="perro"),
        )
        assert result.color == SEMAPHORE_ROJO
        assert len(result.issues) > 0

    def test_toxico_gato_semaforo_rojo(self) -> None:
        """Ajo tóxico para gato → ROJO."""
        result = evaluate_semaphore(
            ingredients=["atún", "ajo"],
            nutritional_profile={},
            pet_profile=_pet_profile(species="gato"),
        )
        assert result.color == SEMAPHORE_ROJO

    def test_restringido_diabetico_rojo(self) -> None:
        """Ingrediente restringido para diabético → ROJO (REGLA 2)."""
        result = evaluate_semaphore(
            ingredients=["azúcar", "miel", "pollo"],
            nutritional_profile={},
            pet_profile=_pet_profile(conditions=["diabético"]),
        )
        assert result.color == SEMAPHORE_ROJO

    def test_alergia_amarillo(self) -> None:
        """Ingrediente en alergias del pet → AMARILLO."""
        result = evaluate_semaphore(
            ingredients=["pollo", "trigo"],
            nutritional_profile={},
            pet_profile=_pet_profile(allergies=["trigo"]),
        )
        assert result.color == SEMAPHORE_AMARILLO

    def test_adecuado_verde(self) -> None:
        """Sin tóxicos, restricciones ni alergias → VERDE."""
        result = evaluate_semaphore(
            ingredients=["pollo", "arroz", "zanahoria"],
            nutritional_profile={},
            pet_profile=_pet_profile(),
        )
        assert result.color == SEMAPHORE_VERDE

    def test_resultado_incluye_issues_cuando_rojo(self) -> None:
        """SemaphoreResult con issues explica el motivo del ROJO."""
        result = evaluate_semaphore(
            ingredients=["uvas"],
            nutritional_profile={},
            pet_profile=_pet_profile(species="perro"),
        )
        assert isinstance(result.issues, list)
        assert len(result.issues) > 0

    def test_resultado_sin_issues_cuando_verde(self) -> None:
        """SemaphoreResult VERDE → issues vacío."""
        result = evaluate_semaphore(
            ingredients=["pollo", "arroz"],
            nutritional_profile={},
            pet_profile=_pet_profile(),
        )
        assert result.color == SEMAPHORE_VERDE
        assert result.issues == []

    def test_semaphore_result_tiene_recomendacion(self) -> None:
        """SemaphoreResult siempre incluye campo recomendacion."""
        result = evaluate_semaphore(
            ingredients=["pollo"],
            nutritional_profile={},
            pet_profile=_pet_profile(),
        )
        assert hasattr(result, "recomendacion")
        assert isinstance(result.recomendacion, str)

    def test_toxicos_tienen_prioridad_sobre_alergias(self) -> None:
        """Si hay tóxico Y alergia → ROJO (tóxico tiene prioridad)."""
        result = evaluate_semaphore(
            ingredients=["uvas", "trigo"],  # uvas tóxico, trigo alergia
            nutritional_profile={},
            pet_profile=_pet_profile(species="perro", allergies=["trigo"]),
        )
        assert result.color == SEMAPHORE_ROJO

    def test_semaphore_result_es_dataclass(self) -> None:
        """SemaphoreResult debe ser un dataclass con campos color, issues, recomendacion."""
        result = evaluate_semaphore(
            ingredients=["pollo"],
            nutritional_profile={},
            pet_profile=_pet_profile(),
        )
        assert isinstance(result, SemaphoreResult)
        assert hasattr(result, "color")
        assert hasattr(result, "issues")
        assert hasattr(result, "recomendacion")

    def test_sin_llm_evaluacion_es_deterministica(self) -> None:
        """Mismos inputs → mismo output siempre (sin variabilidad LLM)."""
        kwargs = {
            "ingredients": ["pollo", "arroz", "cebolla"],
            "nutritional_profile": {},
            "pet_profile": _pet_profile(species="perro"),
        }
        result1 = evaluate_semaphore(**kwargs)
        result2 = evaluate_semaphore(**kwargs)
        assert result1.color == result2.color
        assert result1.issues == result2.issues
