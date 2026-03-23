"""
Motor de restricciones nutricionales preventivas por raza — NutriVet.IA

A diferencia de RESTRICTIONS_BY_CONDITION (hard-coded, bloqueantes),
estas restricciones son PREVENTIVAS: aplican a razas con predisposición genética
incluso cuando NO tienen la condición médica activa declarada.

Son recomendaciones fuertes al LLM — no bloquean el plan, pero sí aparecen
como alertas en las notas clínicas y se inyectan al prompt.

Validado clínicamente por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar sin confirmación veterinaria.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BreedPreventiveRestriction:
    """
    Restricciones nutricionales preventivas para una raza específica.

    prohibited_preventive: Evitar siempre en esta raza (aunque no tenga condición activa).
    limited_preventive:    Limitar en esta raza como prevención.
    recommended_preventive: Incluir en esta raza como prevención.
    special_preventive:    Reglas especiales de manejo.
    alert:                 Mensaje de alerta visible para el vet y propietario.
    """
    prohibited_preventive: frozenset[str] = field(default_factory=frozenset)
    limited_preventive: frozenset[str] = field(default_factory=frozenset)
    recommended_preventive: frozenset[str] = field(default_factory=frozenset)
    special_preventive: frozenset[str] = field(default_factory=frozenset)
    alert: str = ""

    def __post_init__(self) -> None:
        for attr in ("prohibited_preventive", "limited_preventive",
                     "recommended_preventive", "special_preventive"):
            val = getattr(self, attr)
            if not isinstance(val, frozenset):
                object.__setattr__(self, attr, frozenset(val))


def _br(
    prohibited: set[str] | None = None,
    limited: set[str] | None = None,
    recommended: set[str] | None = None,
    special: set[str] | None = None,
    alert: str = "",
) -> BreedPreventiveRestriction:
    """Helper para construir BreedPreventiveRestriction."""
    return BreedPreventiveRestriction(
        prohibited_preventive=frozenset(prohibited or set()),
        limited_preventive=frozenset(limited or set()),
        recommended_preventive=frozenset(recommended or set()),
        special_preventive=frozenset(special or set()),
        alert=alert,
    )


# Mapa de restricciones preventivas por breed_id
BREED_PREVENTIVE_RESTRICTIONS: dict[str, BreedPreventiveRestriction] = {

    # --- PERROS ---

    "dalmata": _br(
        prohibited={"hígado", "anchoas", "sardinas_enlatadas_alto_sodio",
                    "riñón_exceso", "corazón_en_exceso", "proteínas_alta_purina"},
        limited={"proteínas_purinas_moderadas"},
        recommended={"hidratación_máxima", "dieta_alcalinizante", "proteína_baja_purinas"},
        special={"restricción_purinas_obligatoria",
                 "monitoreo_urinario_semestral",
                 "ph_urinario_alcalino_preferido"},
        alert=(
            "DÁLMATA — Predisposición genética a hiperuricosuria: restricción preventiva "
            "de purinas (sin hígado, riñón, anchoas). Hidratación máxima. "
            "Monitoreo urinario semestral recomendado."
        ),
    ),

    "bedlington_terrier": _br(
        prohibited={"hígado_de_res", "mariscos", "nueces", "mejillones",
                    "ostras", "semillas_alto_cobre"},
        limited={"cobre_total_dieta"},
        recommended={"proteína_digestible_bajo_cobre", "zinc_quelado"},
        special={"restricción_cobre_preventiva",
                 "monitoreo_hepático_semestral"},
        alert=(
            "BEDLINGTON TERRIER — Predisposición genética a acumulación hepática de cobre. "
            "Restricción preventiva: sin hígado de res, sin mariscos, sin nueces. "
            "Monitoreo hepático semestral obligatorio."
        ),
    ),

    "west_highland_white_terrier": _br(
        prohibited={"hígado_de_res", "mariscos"},
        limited={"cobre_total_dieta", "proteínas_alérgenas_comunes"},
        recommended={"omega3_piel", "zinc_quelado"},
        special={"restricción_cobre_preventiva"},
        alert=(
            "WEST HIGHLAND WHITE TERRIER — Predisposición a acumulación de cobre y "
            "dermatitis atópica. Restricción preventiva de cobre. "
            "Omega-3 y zinc recomendados para piel."
        ),
    ),

    "cocker_spaniel": _br(
        limited={"grasa_total", "grasas_saturadas"},
        recommended={"omega3", "proteína_digestible_alta_calidad"},
        special={"grasa_moderada_preventiva_pancreatitis"},
        alert=(
            "COCKER SPANIEL — Predisposición a pancreatitis e hepatopatía. "
            "Grasa total moderada como prevención. Omega-3 recomendado."
        ),
    ),

    "schnauzer_miniatura": _br(
        limited={"grasa_total", "triglicéridos"},
        recommended={"fibra_soluble", "omega3"},
        special={"hiperlipidemia_preventiva", "grasa_controlada"},
        alert=(
            "SCHNAUZER MINIATURA — Predisposición a hiperlipidemia y pancreatitis. "
            "Control estricto de grasa en la dieta."
        ),
    ),

    "gran_danes": _br(
        limited={"calcio_exceso_si_cachorro", "comida_única_gran_volumen"},
        recommended={"raciones_divididas_mínimo_2", "proteína_calidad"},
        special={"sin_comedero_elevado",
                 "sin_ejercicio_2h_post_comida",
                 "mínimo_2_comidas_diarias",
                 "adulto_a_los_24_meses_no_12"},
        alert=(
            "GRAN DANÉS — Riesgo de dilatación-vólvulo gástrico (GDV). "
            "Mínimo 2 comidas/día. Sin ejercicio 2h post-comida. "
            "Sin comedero elevado. Madurez nutricional a los 24 meses."
        ),
    ),

    "bernes_montania": _br(
        limited={"calcio_exceso_si_cachorro"},
        recommended={"proteína_calidad", "omega3_antiinflamatorio"},
        special={"adulto_a_los_24_meses",
                 "control_peso_displasia"},
        alert=(
            "BERNÉS DE LA MONTAÑA — Raza gigante, adulto a los 24 meses. "
            "Alta incidencia de cáncer (~40%). Omega-3 antiinflamatorio preventivo."
        ),
    ),

    "bulldog_frances": _br(
        recommended={"dieta_digestible_alta_calidad", "proteína_novela_si_alergia"},
        special={"transición_dieta_muy_lenta_3_4_semanas",
                 "evitar_croquetas_muy_grandes"},
        alert=(
            "BULLDOG FRANCÉS — Alta sensibilidad digestiva y predisposición a alergias. "
            "Transición de dieta muy gradual (3-4 semanas). "
            "Croquetas de tamaño apropiado para braquicéfalos."
        ),
    ),

    "pug": _br(
        limited={"calorías_totales"},
        recommended={"fibra_saciedad", "proteína_magra"},
        special={"control_bcs_estricto_tendencia_obesidad"},
        alert=(
            "PUG (CARLINO) — Alta tendencia a obesidad. "
            "Control calórico estricto desde cachorro. BCS objetivo: 4-5."
        ),
    ),

    "labrador_retriever": _br(
        limited={"calorías_totales"},
        recommended={"fibra_alta_saciedad", "proteína_magra"},
        special={"control_bcs_estricto_tendencia_obesidad",
                 "raciones_medidas_no_ad_libitum"},
        alert=(
            "LABRADOR RETRIEVER — Alta predisposición a obesidad. "
            "Nunca alimentar ad libitum. Control BCS estricto. "
            "Meta BCS 4-5 siempre."
        ),
    ),

    "golden_retriever": _br(
        recommended={"omega3_antitumoral_preventivo", "antioxidantes",
                     "proteína_magra_alta_calidad"},
        special={"dieta_antiinflamatoria_preventiva",
                 "60pct_riesgo_cancer_vida"},
        alert=(
            "GOLDEN RETRIEVER — 60% de riesgo de cáncer en vida. "
            "Dieta antiinflamatoria preventiva: omega-3 elevado y antioxidantes."
        ),
    ),

    "yorkshire_terrier": _br(
        recommended={"múltiples_comidas_pequeñas"},
        special={"hipoglucemia_cachorros_riesgo_alto",
                 "mínimo_3_comidas_dia_adulto",
                 "mínimo_4_comidas_dia_cachorro"},
        alert=(
            "YORKSHIRE TERRIER — Cachorros toy con alto riesgo de hipoglucemia. "
            "Mínimo 4 comidas/día en cachorros. Nunca saltarse comidas."
        ),
    ),

    # --- GATOS ---

    "maine_coon": _br(
        recommended={"taurina_elevada_preventiva", "omega3_cardioprotector"},
        special={"hcm_predisposición_preventiva",
                 "madurez_a_los_18_meses"},
        alert=(
            "MAINE COON — Predisposición a cardiomiopatía hipertrófica (HCM). "
            "Taurina elevada y omega-3 como prevención cardíaca. "
            "Madurez nutricional a los 18 meses."
        ),
    ),

    "ragdoll": _br(
        limited={"fósforo"},
        recommended={"taurina_elevada_preventiva", "omega3_cardioprotector",
                     "hidratación_alta"},
        special={"hcm_y_pkd_predisposición",
                 "madurez_a_los_18_meses"},
        alert=(
            "RAGDOLL — Predisposición a HCM y enfermedad renal poliquística (PKD). "
            "Taurina, omega-3 y fósforo moderado como prevención. "
            "Hidratación alta (dieta húmeda preferida)."
        ),
    ),

    "persa": _br(
        limited={"fósforo"},
        recommended={"hidratación_máxima", "dieta_húmeda_preferida"},
        special={"pkd_predisposición",
                 "fósforo_moderado_preventivo"},
        alert=(
            "PERSA — Predisposición a enfermedad renal poliquística (PKD). "
            "Fósforo moderado preventivo. Hidratación alta: dieta húmeda preferida."
        ),
    ),

    "siames": _br(
        recommended={"proteína_alta_digestibilidad"},
        special={"tendencia_bajo_peso_vejez",
                 "monitoreo_peso_frecuente_senior"},
        alert=(
            "SIAMÉS — Tendencia a bajo peso en edad avanzada. "
            "Monitoreo de peso frecuente en gatos senior (>10 años)."
        ),
    ),

    "sphynx": _br(
        recommended={"calorías_adicionales_10_15pct"},
        special={"mayor_metabolismo_basal_sin_pelo",
                 "hcm_predisposición"},
        alert=(
            "SPHYNX — Sin pelo: mayor pérdida de calor, metabolismo basal elevado. "
            "Requiere 10-15% más calorías que gatos con pelo del mismo peso. "
            "Predisposición a HCM."
        ),
    ),

    "bengal": _br(
        recommended={"dieta_digestible_alta_calidad"},
        special={"sensibilidad_digestiva_moderada",
                 "transición_dieta_gradual"},
        alert=(
            "BENGAL — Predisposición a enfermedad inflamatoria intestinal. "
            "Dieta altamente digestible. Transición gradual ante cambios."
        ),
    ),

    # Criollos — sin restricciones preventivas específicas
    "criollo_perro": _br(
        alert="Mestizo sin predisposiciones genéticas conocidas. Evaluación individual.",
    ),
    "criollo_gato": _br(
        alert="Mestizo sin predisposiciones genéticas conocidas. Evaluación individual.",
    ),
}


def get_breed_restrictions(breed_id: str) -> BreedPreventiveRestriction | None:
    """
    Retorna las restricciones preventivas para una raza.
    Retorna None si la raza no tiene restricciones específicas registradas.
    """
    return BREED_PREVENTIVE_RESTRICTIONS.get(breed_id.lower())


def has_breed_restrictions(breed_id: str) -> bool:
    """True si la raza tiene restricciones preventivas registradas."""
    return breed_id.lower() in BREED_PREVENTIVE_RESTRICTIONS
