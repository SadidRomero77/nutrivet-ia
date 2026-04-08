"""
Validador post-LLM de planes nutricionales.

Verifica que el plan generado por el LLM sea clínicamente coherente:
1. Coherencia calórica: suma de kcal ≈ DER (tolerancia ±15%)
2. Proteína mínima NRC por especie y etapa de vida
3. Ratio Calcio:Fósforo dentro de 1.0-2.0
4. Sin ingredientes en lista de restricciones médicas
5. No se sobrepasa el límite de fósforo si condición renal
6. No se sobrepasa el límite de grasa si condición pancreática o hepática
7. Taurina presente en planes para gatos (si es dieta natural)

Las validaciones son ADVERTENCIAS por defecto — solo algunas son ERRORES bloqueantes.
Las validaciones P0 bloquean el plan (tóxicos, restricciones médicas violadas).
Las validaciones P1 son warnings que se incluyen en notas_clinicas del plan.

Uso:
    result = validate_nutritional_plan(plan_content, species, conditions, der_kcal, rer_kcal)
    if result.blocking_errors:
        raise ValueError(result.blocking_errors[0])
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.infrastructure.agent.prompts.condition_protocols import (
    get_protocols_for_conditions,
    get_most_restrictive_fat_pct,
)


@dataclass
class NutritionalValidationResult:
    """Resultado de la validación nutricional del plan."""

    is_valid: bool
    blocking_errors: list[str]   # P0 — bloquean el plan completamente
    warnings: list[str]          # P1 — se incluyen en notas_clinicas pero no bloquean
    nutritional_summary: dict[str, Any]  # Resumen calculado para loggear


def _extract_ingredients(plan_content: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrae la lista de ingredientes del plan en formato normalizado."""
    ingredientes = plan_content.get("ingredientes", [])
    result = []
    for ing in ingredientes:
        if isinstance(ing, dict):
            result.append(ing)
        elif isinstance(ing, str):
            result.append({"nombre": ing, "cantidad_g": 0, "kcal": 0})
    return result


def _get_float(d: dict, key: str, default: float = 0.0) -> float:
    """Extrae un float de un dict de forma segura."""
    val = d.get(key, default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def validate_nutritional_plan(
    plan_content: dict[str, Any],
    species: str,
    conditions: list[str],
    der_kcal: float,
    rer_kcal: float,
    allergies: list[str],
    medical_restrictions: list[str],
    age_months: int,
) -> NutritionalValidationResult:
    """
    Valida el plan nutricional generado por el LLM.

    Args:
        plan_content: Plan parseado (dict con perfil_nutricional, ingredientes, etc.)
        species: 'perro' | 'gato'
        conditions: Lista de condiciones médicas activas
        der_kcal: DER calculado (determinístico — la verdad)
        rer_kcal: RER calculado
        allergies: Alergias de la mascota
        medical_restrictions: Ingredientes prohibidos por MedicalRestrictionEngine
        age_months: Edad en meses (para calcular etapa de vida)

    Returns:
        NutritionalValidationResult con is_valid, blocking_errors y warnings.
    """
    blocking_errors: list[str] = []
    warnings: list[str] = []

    perfil = plan_content.get("perfil_nutricional", {})
    ingredientes = _extract_ingredients(plan_content)

    # ── 1. Coherencia calórica ────────────────────────────────────────────────
    # El prompt anti-alucinación exige ±10%. Desviación >20% es clínicamente inaceptable
    # (especialmente en diabetes, obesidad, ERC) — se bloquea el plan.
    kcal_suma = sum(_get_float(i, "kcal") for i in ingredientes)
    if kcal_suma > 0 and der_kcal > 0:
        desviacion = abs(kcal_suma - der_kcal) / der_kcal
        if desviacion > 0.20:
            blocking_errors.append(
                f"DESVIACIÓN CALÓRICA CRÍTICA: Plan suma {kcal_suma:.0f} kcal "
                f"vs DER de {der_kcal:.0f} kcal ({desviacion:.1%} de diferencia). "
                "El plan debe estar dentro de ±20% del DER. "
                "Ajustar cantidades_g de ingredientes para cumplir el requerimiento energético."
            )
        elif desviacion > 0.10:
            warnings.append(
                f"Desviación calórica: {kcal_suma:.0f} kcal vs DER {der_kcal:.0f} kcal "
                f"({desviacion:.1%}). El plan debe idealmente estar en ±10%."
            )

    # ── 2. Proteína mínima NRC ────────────────────────────────────────────────
    proteina_pct = _get_float(perfil, "proteina_pct_ms")
    is_kitten_puppy = age_months < 12
    is_gato = species.lower() in ("gato", "cat")

    if proteina_pct > 0:
        if is_gato:
            min_protein = 30.0 if is_kitten_puppy else 26.0
            if proteina_pct < min_protein:
                blocking_errors.append(
                    f"PROTEÍNA INSUFICIENTE para gato: {proteina_pct:.1f}% MS "
                    f"(mínimo NRC: {min_protein}% MS). "
                    "Los gatos son carnívoros obligados — no se puede reducir más."
                )
        else:
            # Perros: mínimo NRC 18% MS adulto, 22% MS cachorro (<12m).
            # Es bloqueante igual que gatos — un plan con déficit proteico crea riesgo de
            # sarcopenia, fallo renal (paradoja: la restricción renal aplica a proteína ALTA,
            # pero el mínimo NRC sigue vigente para mantener masa muscular).
            min_protein = 22.0 if is_kitten_puppy else 18.0
            if proteina_pct < min_protein:
                blocking_errors.append(
                    f"PROTEÍNA INSUFICIENTE para perro: {proteina_pct:.1f}% MS "
                    f"(mínimo NRC: {min_protein}% MS). "
                    "Riesgo de sarcopenia y déficit nutricional. "
                    "Aumentar fuente proteica dentro de las restricciones de la condición médica."
                )

    # ── 3. Ratio Calcio:Fósforo ───────────────────────────────────────────────
    calcio_g = _get_float(perfil, "calcio_g_dia")
    fosforo_g = _get_float(perfil, "fosforo_g_dia")
    if calcio_g > 0 and fosforo_g > 0:
        ratio_ca_p = calcio_g / fosforo_g
        # Blocker en los límites exactos NRC 2006 (1.0–2.0).
        # Fuera de rango causa problemas esqueléticos en crecimiento y alteraciones metabólicas.
        if ratio_ca_p < 1.0 or ratio_ca_p > 2.0:
            blocking_errors.append(
                f"RATIO Ca:P FUERA DE RANGO NRC: {ratio_ca_p:.2f} (rango obligatorio 1.0–2.0). "
                f"Ca: {calcio_g:.2f}g · P: {fosforo_g:.2f}g/día. "
                "Ajustar suplementación de calcio o reducir fuentes altas en fósforo."
            )

    # ── 4. Restricciones médicas violadas ────────────────────────────────────
    ingredient_names_lower = [
        i.get("nombre", "").lower() for i in ingredientes if isinstance(i, dict)
    ]
    restrictions_lower = [r.lower() for r in medical_restrictions]

    for restriction in restrictions_lower:
        # Verificar si algún ingrediente contiene el término restringido
        for ing_name in ingredient_names_lower:
            if restriction in ing_name or ing_name in restriction:
                blocking_errors.append(
                    f"RESTRICCIÓN MÉDICA VIOLADA: '{ing_name}' está en la lista de "
                    f"ingredientes restringidos ('{restriction}'). Este plan debe ser rechazado."
                )
                break

    # ── 5. Alergias presentes en el plan ─────────────────────────────────────
    allergies_lower = [a.lower() for a in allergies]
    for allergy in allergies_lower:
        for ing_name in ingredient_names_lower:
            if allergy in ing_name or ing_name in allergy:
                blocking_errors.append(
                    f"ALERGIA INCLUIDA EN PLAN: '{ing_name}' es un alérgeno declarado "
                    f"('{allergy}'). El plan debe excluir todos los alérgenos registrados."
                )
                break

    # ── 6. Límite de fósforo (condición renal) ────────────────────────────────
    if "renal" in conditions and fosforo_g > 0:
        # Estimar kcal del plan para calcular g/100kcal
        kcal_ref = kcal_suma if kcal_suma > 0 else der_kcal
        if kcal_ref > 0:
            fosforo_por_100kcal = (fosforo_g / kcal_ref) * 100
            if fosforo_por_100kcal > 0.6:
                warnings.append(
                    f"FÓSFORO ALTO para condición renal: {fosforo_por_100kcal:.2f} g/100kcal "
                    f"(meta: <0.5 g/100kcal estadio 2, <0.4 estadio 3). "
                    "Revisar ingredientes altos en fósforo."
                )

    # ── 7. Límite de grasa (pancreatitis, hepatopatía) ────────────────────────
    protocols = get_protocols_for_conditions(conditions)
    grasa_max_pct = get_most_restrictive_fat_pct(protocols)
    grasa_plan_pct = _get_float(perfil, "grasa_pct_ms")

    if grasa_plan_pct > 0 and grasa_plan_pct > grasa_max_pct:
        if grasa_max_pct <= 10.0:
            # Pancreatitis o hepatopatía con hiperlipidemia — bloquear
            blocking_errors.append(
                f"GRASA EXCESIVA para condición crítica: plan tiene {grasa_plan_pct:.1f}% MS "
                f"de grasa, máximo permitido para condiciones activas: {grasa_max_pct:.1f}% MS. "
                "Reducir ingredientes grasos."
            )
        else:
            warnings.append(
                f"Grasa por encima del rango recomendado: {grasa_plan_pct:.1f}% MS "
                f"(máximo para condiciones activas: {grasa_max_pct:.1f}% MS)."
            )

    # ── 8. Taurina en planes para gatos ───────────────────────────────────────
    if is_gato:
        taurina_en_plan = False
        for ing in ingredientes:
            nombre = ing.get("nombre", "").lower()
            if any(t in nombre for t in ["taurina", "corazón", "corazon", "sardina", "mejillón"]):
                taurina_en_plan = True
                break
        # También verificar suplementos
        for supl in plan_content.get("suplementos", []):
            if "taurina" in supl.get("nombre", "").lower():
                taurina_en_plan = True
                break
        if not taurina_en_plan:
            warnings.append(
                "TAURINA: No se detectó fuente clara de taurina en el plan para gato. "
                "Agregar corazón de pollo, sardinas o suplemento de taurina (250 mg/día). "
                "Deficiencia causa ceguera y cardiomiopatía dilatada."
            )

    # ── 9. Número de ingredientes razonable ───────────────────────────────────
    if len(ingredientes) < 2:
        blocking_errors.append(
            f"Plan con solo {len(ingredientes)} ingrediente(s) — "
            "un plan completo requiere al menos 2 fuentes alimenticias."
        )
    elif len(ingredientes) > 15:
        warnings.append(
            f"Plan con {len(ingredientes)} ingredientes — puede ser demasiado complejo "
            "para preparación práctica. Considerar simplificar."
        )

    # ── Resumen para logging ──────────────────────────────────────────────────
    nutritional_summary = {
        "kcal_suma": round(kcal_suma, 1),
        "der_kcal": round(der_kcal, 1),
        "desviacion_calorica_pct": round(abs(kcal_suma - der_kcal) / der_kcal * 100, 1) if der_kcal else None,
        "proteina_pct_ms": proteina_pct,
        "grasa_pct_ms": grasa_plan_pct,
        "calcio_g": calcio_g,
        "fosforo_g": fosforo_g,
        "ratio_ca_p": round(calcio_g / fosforo_g, 2) if fosforo_g else None,
        "num_ingredientes": len(ingredientes),
        "blocking_errors_count": len(blocking_errors),
        "warnings_count": len(warnings),
    }

    is_valid = len(blocking_errors) == 0

    return NutritionalValidationResult(
        is_valid=is_valid,
        blocking_errors=blocking_errors,
        warnings=warnings,
        nutritional_summary=nutritional_summary,
    )


def enrich_plan_with_validation(
    plan_content: dict[str, Any],
    validation_result: NutritionalValidationResult,
) -> dict[str, Any]:
    """
    Enriquece el plan con los warnings de validación en notas_clinicas.

    Los blocking_errors ya habrán causado ValueError antes de llegar aquí.
    Los warnings se añaden como notas para el veterinario revisor.

    Args:
        plan_content: Plan parseado del LLM
        validation_result: Resultado de validate_nutritional_plan

    Returns:
        plan_content enriquecido con warnings en notas_clinicas
    """
    enriched = dict(plan_content)

    if validation_result.warnings:
        if "notas_clinicas" not in enriched:
            enriched["notas_clinicas"] = []
        for warning in validation_result.warnings:
            enriched["notas_clinicas"].append(f"⚠ {warning}")

    # Añadir resumen nutricional como metadata interna
    enriched["_validation_summary"] = validation_result.nutritional_summary

    return enriched
