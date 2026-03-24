"""
Suplementación clínica específica por condición — NutriVet.IA (B-01)

Define dosis terapéuticas diferenciadas de dosis de mantenimiento para las
condiciones médicas soportadas.

Fuentes:
- NRC 2006 Nutrient Requirements of Dogs and Cats
- ACVIM Consensus Statement — Cardiovascular Disease 2019
- J Vet Intern Med 1992, 2012 (taurina, DHA neurológico)
- WSAVA 2010 (glucosamina/condroitina articular)
- J Nutr 1998 Ogilvie (omega-3 antitumoral)
- Small Animal Clinical Nutrition 5th Ed.

Validado por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar dosis sin confirmación veterinaria.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClinicalDose:
    """
    Dosis clínica de un suplemento para una condición específica.

    dosis_perro:   Dosis para perros (string con unidad, e.g. "100 mg/kg/día")
    dosis_gato:    Dosis para gatos ("N/A" si no aplica a gatos)
    frecuencia:    Frecuencia de administración
    forma:         Presentación preferida (cápsula, polvo, aceite)
    justificacion: Referencia clínica o razón terapéutica
    contraindicaciones: Condiciones que contraindican este suplemento
    nivel:         "terapeutico" | "preventivo" | "mantenimiento"
    """

    dosis_perro: str
    dosis_gato: str
    frecuencia: str
    forma: str
    justificacion: str
    contraindicaciones: list[str] = field(default_factory=list)
    nivel: str = "terapeutico"


# ---------------------------------------------------------------------------
# Suplementos clínicos por condición
# ---------------------------------------------------------------------------

CLINICAL_SUPPLEMENTS: dict[str, dict[str, ClinicalDose]] = {

    # ── INSUFICIENCIA CARDÍACA ─────────────────────────────────────────────
    "insuficiencia_cardiaca": {
        "taurina": ClinicalDose(
            dosis_perro="100 mg/kg/día",
            dosis_gato="250 mg/kg/día",
            frecuencia="diario",
            forma="polvo mezclado en alimento o cápsula abierta",
            justificacion=(
                "NRC 2006 + J Vet Intern Med 1992: deficiencia de taurina documentada "
                "en cardiomiopatía dilatada (DCM). Obligatoria en razas predispuestas "
                "(Cocker, Boxer, Doberman, Golden). Dosis terapéutica vs 25 mg/kg mantenimiento."
            ),
            contraindicaciones=[],
            nivel="terapeutico",
        ),
        "l_carnitina": ClinicalDose(
            dosis_perro="50 mg/kg/día",
            dosis_gato="50 mg/kg/día",
            frecuencia="diario",
            forma="polvo o cápsula",
            justificacion=(
                "Deficiencia documentada en DCM — especialmente Cocker Spaniel y Boxer. "
                "ACVIM 2019: suplementación recomendada cuando se sospecha deficiencia."
            ),
            contraindicaciones=["Insuficiencia renal severa (acumulación)"],
            nivel="terapeutico",
        ),
        "omega3_epa_dha": ClinicalDose(
            dosis_perro="40 mg EPA+DHA/kg/día",
            dosis_gato="25 mg EPA+DHA/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsula de omega-3 marino",
            justificacion=(
                "ACVIM 2019: omega-3 en dosis altas antiinflamatorio cardíaco — "
                "reduce citoquinas proinflamatorias, mejora función cardíaca. "
                "Dosis terapéutica: 2× la dosis de mantenimiento."
            ),
            contraindicaciones=["Trastornos de coagulación activos"],
            nivel="terapeutico",
        ),
    },

    # ── CONDICIÓN ARTICULAR ───────────────────────────────────────────────
    "articular": {
        "glucosamina": ClinicalDose(
            dosis_perro="22 mg/kg/día",
            dosis_gato="15 mg/kg/día",
            frecuencia="diario",
            forma="polvo o cápsula con alimento",
            justificacion=(
                "WSAVA 2010: condroprotector en artritis degenerativa (OA). "
                "Estimula síntesis de glucosaminoglicanos en cartílago articular."
            ),
            contraindicaciones=["Alergia a mariscos (glucosamina de origen marino)"],
            nivel="terapeutico",
        ),
        "condroitina": ClinicalDose(
            dosis_perro="17 mg/kg/día",
            dosis_gato="10 mg/kg/día",
            frecuencia="diario",
            forma="polvo o cápsula — generalmente combinado con glucosamina",
            justificacion=(
                "WSAVA 2010: sinergia con glucosamina. Inhibe enzimas degradadoras "
                "del cartílago (MMP). Presentaciones combinadas (glucosamina+condroitina) "
                "son más eficaces que por separado."
            ),
            contraindicaciones=["Trastornos de coagulación (anticoagulante débil)"],
            nivel="terapeutico",
        ),
        "omega3_epa_dha": ClinicalDose(
            dosis_perro="30 mg EPA+DHA/kg/día",
            dosis_gato="20 mg EPA+DHA/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas omega-3 marino",
            justificacion=(
                "Antiinflamatorio articular — reduce COX-2 y prostaglandinas inflamatorias. "
                "Evidencia sólida en perros con OA: mejora movilidad y reduce dolor."
            ),
            contraindicaciones=["Trastornos de coagulación activos"],
            nivel="terapeutico",
        ),
    },

    # ── CONDICIÓN ONCOLÓGICA (cancerígeno) ────────────────────────────────
    "cancerígeno": {
        "omega3_epa_dha": ClinicalDose(
            dosis_perro="50 mg EPA+DHA/kg/día",
            dosis_gato="30 mg EPA+DHA/kg/día",
            frecuencia="diario",
            forma="aceite de salmón de alta pureza o cápsulas",
            justificacion=(
                "J Nutr 1998 Ogilvie: EPA antitumoral en dosis altas — reduce "
                "caquexia neoplásica, inhibe proliferación tumoral. Dosis 2.5× "
                "la de mantenimiento. Evidencia más sólida en linfoma y carcinoma."
            ),
            contraindicaciones=["Trastornos de coagulación activos"],
            nivel="terapeutico",
        ),
        "vitamina_e": ClinicalDose(
            dosis_perro="400 UI/día",
            dosis_gato="30 UI/día",
            frecuencia="diario",
            forma="cápsula de vitamina E natural (d-alfa-tocoferol)",
            justificacion=(
                "Antioxidante — reduce estrés oxidativo en cáncer. "
                "Sinérgico con omega-3 (protege EPA/DHA de oxidación). "
                "NOTA: suspender 1-2 semanas antes de cirugía (anticoagulante leve)."
            ),
            contraindicaciones=["Hipervitaminosis E si se usa junto con otros suplementos E"],
            nivel="terapeutico",
        ),
    },

    # ── EPILEPSIA ─────────────────────────────────────────────────────────
    "epilepsia": {
        "magnesio": ClinicalDose(
            dosis_perro="1.5 mg/kg/día",
            dosis_gato="1.0 mg/kg/día",
            frecuencia="diario",
            forma="glicinato de magnesio o citrato (mejor absorción que óxido)",
            justificacion=(
                "Cofactor neurológico — déficit documentado en algunos epilépticos. "
                "Magnesio tiene efecto NMDA-antagonista leve — modulador de excitabilidad neuronal."
            ),
            contraindicaciones=["Insuficiencia renal (acumulación de magnesio)"],
            nivel="terapeutico",
        ),
        "dha": ClinicalDose(
            dosis_perro="25 mg/kg/día",
            dosis_gato="15 mg/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o aceite de krill (mayor DHA/EPA ratio)",
            justificacion=(
                "J Vet Intern Med 2012: DHA neuroprotector — reduce frecuencia de crisis "
                "en perros epilépticos en algunos estudios. Componente estructural de membranas neuronales."
            ),
            contraindicaciones=[],
            nivel="terapeutico",
        ),
    },

    # ── INSUFICIENCIA RENAL AVANZADA (IRIS 3-4) ───────────────────────────
    "renal": {
        "omega3_epa_dha": ClinicalDose(
            dosis_perro="30 mg EPA+DHA/kg/día",
            dosis_gato="20 mg EPA+DHA/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas de omega-3",
            justificacion=(
                "Am J Vet Res 1998: reduce inflamación glomerular, retarda progresión "
                "de ERC. IRIS guidelines: recomendado en estadios 2-4."
            ),
            contraindicaciones=[],
            nivel="terapeutico",
        ),
        "b_complex": ClinicalDose(
            dosis_perro="1 comprimido/día",
            dosis_gato="0.5 comprimido/día",
            frecuencia="diario",
            forma="complejo B hidrosoluble — polvo o comprimido partido",
            justificacion=(
                "ERC: las vitaminas B hidrosolubles se pierden en mayor cantidad. "
                "Déficit de tiamina (B1), riboflavina (B2) y B12 frecuente en ERC avanzada."
            ),
            contraindicaciones=[],
            nivel="terapeutico",
        ),
    },

    # ── NEURODEGENERATIVO ─────────────────────────────────────────────────
    "neurodegenerativo": {
        "dha": ClinicalDose(
            dosis_perro="25 mg/kg/día",
            dosis_gato="20 mg/kg/día",
            frecuencia="diario",
            forma="aceite de krill o aceite de algas (fuente vegana de DHA)",
            justificacion=(
                "DHA es componente estructural de membranas neuronales (30% de la corteza). "
                "Deterioro cognitivo canino (CCD): suplementación DHA enlentece progresión."
            ),
            contraindicaciones=[],
            nivel="terapeutico",
        ),
        "vitamina_e": ClinicalDose(
            dosis_perro="200 UI/día",
            dosis_gato="30 UI/día",
            frecuencia="diario",
            forma="cápsula vitamina E natural",
            justificacion="Antioxidante neuroprotector — reduce estrés oxidativo cerebral.",
            contraindicaciones=[],
            nivel="terapeutico",
        ),
    },

    # ── HEPATOPATÍA / HIPERLIPIDEMIA ──────────────────────────────────────
    "hepático/hiperlipidemia": {
        "vitamina_e": ClinicalDose(
            dosis_perro="400 UI/día",
            dosis_gato="30 UI/día",
            frecuencia="diario",
            forma="cápsula vitamina E natural",
            justificacion=(
                "Hepatitis crónica: antioxidante hepático — protege hepatocitos del "
                "estrés oxidativo. Especialmente en hepatitis inmunomediada."
            ),
            contraindicaciones=["Hepatitis séptica activa (consultar vet)"],
            nivel="terapeutico",
        ),
        "silimarina": ClinicalDose(
            dosis_perro="20-50 mg/kg/día",
            dosis_gato="20-30 mg/kg/día",
            frecuencia="diario",
            forma="extracto de cardo mariano estandarizado (70-80% silimarina)",
            justificacion=(
                "Hepatoprotector — estabiliza membranas hepatocitarias, reduce "
                "inflamación hepática. Ampliamente usado en hepatitis tóxica y crónica."
            ),
            contraindicaciones=[],
            nivel="terapeutico",
        ),
    },
}


def get_supplements_for_condition(condition_id: str) -> dict[str, ClinicalDose]:
    """
    Retorna los suplementos clínicos para una condición médica.

    Args:
        condition_id: ID de la condición (e.g. "insuficiencia_cardiaca").

    Returns:
        Dict {nombre_suplemento: ClinicalDose}. Vacío si no hay datos.
    """
    return CLINICAL_SUPPLEMENTS.get(condition_id, {})


def get_all_supplements_for_conditions(
    conditions: list[str],
) -> dict[str, dict[str, ClinicalDose]]:
    """
    Retorna todos los suplementos clínicos para una lista de condiciones.

    Cuando la misma condición aparece en múltiples entradas, no hay deduplicación
    — el LLM decide la dosis final integrando el contexto completo.

    Args:
        conditions: Lista de condition_ids.

    Returns:
        Dict {condition_id: {suplemento: ClinicalDose}}.
    """
    return {
        cond: CLINICAL_SUPPLEMENTS[cond]
        for cond in conditions
        if cond in CLINICAL_SUPPLEMENTS
    }
