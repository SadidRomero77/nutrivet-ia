"""
Validador de relación Calcio:Fósforo (Ca:P) — NutriVet.IA (A-05)

Fuentes: NRC 2006, AAFCO 2023, Small Animal Clinical Nutrition 5th Ed.

La relación Ca:P es crítica para:
- Cachorros de raza gigante: rango estrecho para evitar osteocondrodisplasia
- Gestantes/lactantes: demanda ósea elevada
- Enfermos renales: restricción de fósforo

Constitution REGLA 3: esta validación es DETERMINISTA — nunca la hace el LLM.
Validado por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar rangos sin confirmación veterinaria.
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Rangos Ca:P por fase/contexto (min_ratio, max_ratio)
# Fuente: NRC 2006 Table 15-1 + AAFCO 2023 Nutrient Profiles
# ---------------------------------------------------------------------------

CA_P_RATIOS: dict[str, tuple[float, float]] = {
    # Cachorros
    "cachorro_raza_gigante": (1.2, 1.8),   # muy estricto — exceso → osteocondrodisplasia
    "cachorro": (1.0, 2.0),                 # cachorros en general
    # Adultos
    "adulto": (1.0, 2.0),                   # rango estándar NRC 2006
    # Estados reproductivos especiales
    "gestante": (1.2, 2.0),                 # mayor demanda ósea
    "lactante": (1.2, 2.0),                 # pérdida de calcio en leche
    # Patológicos — restricciones específicas
    "renal": (1.5, 2.5),                    # mayor ratio para reducir fósforo absorbible
    "senior": (1.0, 2.0),
}

# Fases de vida que corresponden a "cachorro" en la lógica del plan
_FASES_CACHORRO: frozenset[str] = frozenset({"cachorro", "cachorro_raza_gigante"})


@dataclass(frozen=True)
class CaPValidationResult:
    """
    Resultado de la validación Ca:P.

    aprobado:       True si el ratio está dentro del rango esperado.
    ratio_actual:   Ratio Ca:P calculado (calcio_g / fosforo_g). None si sin datos.
    rango_esperado: (min, max) según el contexto.
    contexto:       Clave del contexto usado para la validación.
    mensaje:        Descripción del resultado para logs y el LLM.
    es_bloqueante:  True si el incumplimiento impide generar el plan.
    """

    aprobado: bool
    ratio_actual: float | None
    rango_esperado: tuple[float, float]
    contexto: str
    mensaje: str
    es_bloqueante: bool


def validate_ca_p_ratio(
    calcio_g: float,
    fosforo_g: float,
    contexto: str = "adulto",
) -> CaPValidationResult:
    """
    Valida que la relación Ca:P del plan esté dentro del rango seguro.

    Args:
        calcio_g:   Gramos de calcio diarios en el plan.
        fosforo_g:  Gramos de fósforo diarios en el plan.
        contexto:   Clave de CA_P_RATIOS: "adulto" | "cachorro" |
                    "cachorro_raza_gigante" | "gestante" | "lactante" |
                    "renal" | "senior".

    Returns:
        CaPValidationResult con el veredicto y detalle.

    Notes:
        - Si fósforo = 0 → ratio incalculable → aprobado=False, bloqueante=False
          (el LLM debe proveer datos completos).
        - Cachorro raza gigante con ratio > 1.8 → BLOQUEANTE (riesgo óseo grave).
        - Cualquier ratio < 0.8 → siempre BLOQUEANTE (hipocalcemia).
    """
    rango = CA_P_RATIOS.get(contexto, CA_P_RATIOS["adulto"])
    min_ratio, max_ratio = rango

    # Sin datos de fósforo — no podemos calcular
    if fosforo_g <= 0:
        return CaPValidationResult(
            aprobado=False,
            ratio_actual=None,
            rango_esperado=rango,
            contexto=contexto,
            mensaje=(
                "No se puede calcular Ca:P — fósforo_g_dia es 0. "
                "El plan debe especificar el aporte de fósforo."
            ),
            es_bloqueante=False,
        )

    ratio = calcio_g / fosforo_g

    # Ratio peligrosamente bajo → hipocalcemia → siempre bloqueante
    if ratio < 0.8:
        return CaPValidationResult(
            aprobado=False,
            ratio_actual=ratio,
            rango_esperado=rango,
            contexto=contexto,
            mensaje=(
                f"Ca:P = {ratio:.2f} — PELIGROSAMENTE BAJO (< 0.8). "
                "Riesgo de hipocalcemia severa. Suplementar calcio obligatoriamente."
            ),
            es_bloqueante=True,
        )

    # Dentro del rango → aprobado
    if min_ratio <= ratio <= max_ratio:
        return CaPValidationResult(
            aprobado=True,
            ratio_actual=ratio,
            rango_esperado=rango,
            contexto=contexto,
            mensaje=f"Ca:P = {ratio:.2f} — dentro del rango {min_ratio}-{max_ratio} para {contexto}.",
            es_bloqueante=False,
        )

    # Fuera del rango
    es_bloqueante = (
        ratio < 0.8
        or (contexto == "cachorro_raza_gigante" and ratio > 1.8)
    )
    direccion = "bajo" if ratio < min_ratio else "alto"
    return CaPValidationResult(
        aprobado=False,
        ratio_actual=ratio,
        rango_esperado=rango,
        contexto=contexto,
        mensaje=(
            f"Ca:P = {ratio:.2f} — demasiado {direccion} para contexto '{contexto}' "
            f"(rango esperado {min_ratio}-{max_ratio}). "
            "Ajustar suplementación de calcio o reducir fuentes de fósforo."
        ),
        es_bloqueante=es_bloqueante,
    )


def get_ca_p_context(
    age_months: int,
    species: str,
    is_giant_breed: bool = False,
    medical_conditions: list[str] | None = None,
    reproductive_status: str = "adulto",
) -> str:
    """
    Determina el contexto Ca:P adecuado dado el perfil de la mascota.

    Args:
        age_months:          Edad en meses.
        species:             "perro" | "gato".
        is_giant_breed:      True si la raza tiene meses_adulto ≥ 18.
        medical_conditions:  Lista de condiciones médicas activas.
        reproductive_status: Estado reproductivo ("gestante" | "lactante" | ...).

    Returns:
        Clave de CA_P_RATIOS para usar en validate_ca_p_ratio().
    """
    conditions = set(medical_conditions or [])

    # Estado reproductivo especial tiene prioridad sobre edad
    if reproductive_status == "gestante":
        return "gestante"
    if reproductive_status == "lactante":
        return "lactante"

    # Enfermedad renal — ratio especial
    if "renal" in conditions:
        return "renal"

    # Cachorro
    umbral_adulto = 18 if is_giant_breed else (12 if species == "perro" else 12)
    if age_months < umbral_adulto:
        return "cachorro_raza_gigante" if is_giant_breed else "cachorro"

    # Senior (perro > 7 años = 84 meses; gato > 10 años = 120 meses)
    umbral_senior = 84 if species == "perro" else 120
    if age_months >= umbral_senior:
        return "senior"

    return "adulto"
