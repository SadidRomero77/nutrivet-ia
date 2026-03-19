"""
NutritionalEvaluator — Semáforo determinístico para evaluación nutricional.

Sin LLM. Orden de prioridad:
  1. Tóxicos → ROJO (REGLA 1)
  2. Restricciones médicas → ROJO (REGLA 2)
  3. Alergias → AMARILLO
  4. Desequilibrio nutricional → AMARILLO
  5. Todo OK → VERDE
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.safety.food_safety_checker import FoodSafetyChecker
from backend.domain.safety.medical_restriction_engine import MedicalRestrictionEngine

SEMAPHORE_ROJO = "ROJO"
SEMAPHORE_AMARILLO = "AMARILLO"
SEMAPHORE_VERDE = "VERDE"

_DISCLAIMER = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)


@dataclass
class SemaphoreResult:
    """Resultado del semáforo nutricional."""

    color: str                          # ROJO | AMARILLO | VERDE
    issues: list[str] = field(default_factory=list)   # Motivos de ROJO o AMARILLO
    recomendacion: str = ""             # Recomendación para el usuario


def evaluate_semaphore(
    ingredients: list[str],
    nutritional_profile: dict,
    pet_profile: dict,
) -> SemaphoreResult:
    """
    Evalúa ingredientes contra el perfil de la mascota.

    Determinístico: mismos inputs → mismo output.
    No llama LLM.

    Args:
        ingredients: Lista de ingredientes extraídos por OCR.
        nutritional_profile: Valores nutricionales extraídos (proteínas, grasas, etc.).
        pet_profile: Perfil de la mascota (species, conditions, allergies).

    Returns:
        SemaphoreResult con color, issues y recomendación.
    """
    species = pet_profile.get("species", "perro")
    conditions = pet_profile.get("medical_conditions", [])
    allergies = [a.lower() for a in pet_profile.get("allergies", [])]

    issues: list[str] = []

    # ── Prioridad 1: Toxicidad (REGLA 1) ──────────────────────────────────────
    toxicity_results = FoodSafetyChecker.validate_plan_ingredients(
        ingredients=ingredients, species=species
    )
    toxic_found = [r.ingredient for r in toxicity_results if r.is_toxic]
    if toxic_found:
        issues.extend([
            f"⛔ '{ing}' es tóxico para {species}" for ing in toxic_found
        ])
        return SemaphoreResult(
            color=SEMAPHORE_ROJO,
            issues=issues,
            recomendacion=(
                f"Este producto NO es seguro para tu {species}. "
                f"Contiene ingredientes tóxicos: {', '.join(toxic_found)}. "
                "Consulta a tu veterinario antes de cualquier cambio alimentario. "
                f"{_DISCLAIMER}"
            ),
        )

    # ── Prioridad 2: Restricciones médicas (REGLA 2) ──────────────────────────
    if conditions:
        restriction_result = MedicalRestrictionEngine.get_restrictions_for_conditions(conditions)
        prohibited = {p.lower() for p in restriction_result.prohibited}
        restricted_found = [
            ing for ing in ingredients if ing.lower() in prohibited
        ]
        if restricted_found:
            issues.extend([
                f"🚫 '{ing}' está restringido para {', '.join(conditions)}"
                for ing in restricted_found
            ])
            return SemaphoreResult(
                color=SEMAPHORE_ROJO,
                issues=issues,
                recomendacion=(
                    f"Este producto NO es adecuado para las condiciones médicas de tu mascota. "
                    f"Ingredientes restringidos: {', '.join(restricted_found)}. "
                    "Requiere aprobación veterinaria. "
                    f"{_DISCLAIMER}"
                ),
            )

    # ── Prioridad 3: Alergias ──────────────────────────────────────────────────
    allergy_found = [
        ing for ing in ingredients if ing.lower() in allergies
    ]
    if allergy_found:
        issues.extend([
            f"⚠️ '{ing}' está registrado como alergia/intolerancia"
            for ing in allergy_found
        ])
        return SemaphoreResult(
            color=SEMAPHORE_AMARILLO,
            issues=issues,
            recomendacion=(
                f"Tu mascota tiene registrada alergia/intolerancia a: {', '.join(allergy_found)}. "
                "Consulta con tu veterinario antes de ofrecer este producto. "
                f"{_DISCLAIMER}"
            ),
        )

    # ── VERDE: Sin problemas detectados ───────────────────────────────────────
    return SemaphoreResult(
        color=SEMAPHORE_VERDE,
        issues=[],
        recomendacion=(
            "✅ No se detectaron ingredientes problemáticos para tu mascota. "
            "Recuerda introducir cualquier alimento nuevo de forma gradual. "
            f"{_DISCLAIMER}"
        ),
    )
