"""
Restricciones médicas hard-coded por condición — NutriVet.IA
Constitution REGLA 2: estas restricciones son la fuente de verdad.
El LLM NUNCA puede sobrescribir lo que está aquí.

Validado clínicamente por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar sin confirmación veterinaria.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConditionRestrictions:
    """
    Restricciones nutricionales para una condición médica.

    prohibited:    Ingredientes o categorías categóricamente prohibidos.
    limited:       Ingredientes o nutrientes a limitar significativamente.
    recommended:   Ingredientes o nutrientes que deben estar presentes.
    special_rules: Reglas de manejo no ligadas a ingredientes específicos.
    """

    prohibited: frozenset[str] = field(default_factory=frozenset)
    limited: frozenset[str] = field(default_factory=frozenset)
    recommended: frozenset[str] = field(default_factory=frozenset)
    special_rules: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        # Convertir iterables a frozenset si se pasaron como set o list
        for attr in ("prohibited", "limited", "recommended", "special_rules"):
            val = getattr(self, attr)
            if not isinstance(val, frozenset):
                object.__setattr__(self, attr, frozenset(val))


def _r(
    prohibited: set[str] | None = None,
    limited: set[str] | None = None,
    recommended: set[str] | None = None,
    special_rules: set[str] | None = None,
) -> ConditionRestrictions:
    """Helper para construir ConditionRestrictions con sets vacíos por defecto."""
    return ConditionRestrictions(
        prohibited=frozenset(prohibited or set()),
        limited=frozenset(limited or set()),
        recommended=frozenset(recommended or set()),
        special_rules=frozenset(special_rules or set()),
    )


# Mapa principal de restricciones — una entrada por cada una de las 13 condiciones
RESTRICTIONS_BY_CONDITION: dict[str, ConditionRestrictions] = {
    "diabético": _r(
        prohibited={"azúcar", "miel", "glucosa", "sacarosa", "fructosa",
                    "carbohidratos_simples", "almidón_refinado", "arroz_blanco_exceso",
                    "frutas_alto_ig", "dátiles", "plátano_maduro"},
        limited={"carbohidratos_totales", "frutas"},
        recommended={"fibra_soluble", "proteína_magra", "carbohidratos_complejos",
                     "avena_cocida", "batata_moderada"},
        special_rules={"control_glucémico_estricto",
                       "raciones_regulares_misma_hora",
                       "sin_picos_calóricos"},
    ),
    "hipotiroideo": _r(
        prohibited={"soya_cruda", "col_cruda", "brócoli_crudo",
                    "coliflor_cruda", "bociógenos_en_exceso"},
        limited={"crucíferas_crudas"},
        recommended={"proteína_adecuada", "yodo_fuente"},
        special_rules={"bociógenos_cocidos_en_pequeña_cantidad_aceptables",
                       "cocinar_crucíferas_siempre"},
    ),
    "cancerígeno": _r(
        prohibited={"azúcar", "azúcares_simples", "glucosa", "fructosa_libre",
                    "alimentos_ultraprocesados"},
        limited={"carbohidratos_refinados"},
        recommended={"antioxidantes", "arándanos", "brócoli_cocido",
                     "vitamina_e", "omega_3", "proteína_magra"},
        special_rules={"dieta_antiinflamatoria", "sin_exceso_calórico"},
    ),
    "articular": _r(
        prohibited={"sobrecarga_calórica_bcs_mayor_7"},
        limited={"grasas_saturadas", "omega_6_exceso"},
        recommended={"omega_3", "dha", "epa", "proteína_magra",
                     "glucosamina_fuente", "condroitina_fuente"},
        special_rules={"control_peso_estricto_si_bcs_mayor_7",
                       "antiinflamatorio_nutricional"},
    ),
    "renal": _r(
        prohibited={"fósforo_alto", "sodio_excesivo", "proteína_alta",
                    "potasio_alto_en_estadio_avanzado"},
        limited={"fósforo", "sodio", "proteína", "potasio"},
        recommended={"proteína_moderada_y_digestible", "hidratación_alta",
                     "omega_3"},
        special_rules={"restricción_fósforo_prioritaria",
                       "proteína_alta_calidad_baja_cantidad",
                       "monitoreo_vet_frecuente"},
    ),
    "hepático/hiperlipidemia": _r(
        prohibited={"grasas_saturadas_en_exceso", "proteína_alta_densidad",
                    "cobre_alto", "hierro_alto"},
        limited={"grasa_total", "proteína", "cobre", "sodio"},
        recommended={"carbohidratos_digestibles", "proteína_moderada_alta_calidad",
                     "fibra_soluble", "vitamina_e", "zinc"},
        special_rules={"hígado_contraindicado_hepatopatía",
                       "evitar_ayunos_prolongados"},
    ),
    "pancreático": _r(
        prohibited={"grasas_totales_mayor_10pct_ms", "ayuno_mayor_6h",
                    "comidas_grandes", "grasas_saturadas"},
        limited={"grasa_total"},
        recommended={"grasas_muy_bajas", "proteína_magra_digestible",
                     "carbohidratos_digestibles"},
        special_rules={"raciones_muy_pequeñas_y_frecuentes",
                       "sin_ayuno_mayor_6h",
                       "4_a_6_comidas_por_dia"},
    ),
    "neurodegenerativo": _r(
        prohibited=set(),
        limited={"grasas_saturadas"},
        recommended={"dha", "omega_3_origen_animal", "antioxidantes",
                     "vitamina_e", "vitamina_c", "arándanos"},
        special_rules={"dha_obligatorio", "dieta_neuroprotectora"},
    ),
    "bucal/periodontal": _r(
        prohibited={"azúcares_fermentables", "almidón_pegajoso",
                    "alimentos_adherentes"},
        limited={"carbohidratos_simples"},
        recommended={"textura_apropiada_según_severidad",
                     "masticación_adecuada"},
        special_rules={"textura_adaptada_a_severidad_dental",
                       "higiene_oral_complementaria"},
    ),
    "piel/dermatitis": _r(
        prohibited={"alérgenos_declarados_en_perfil"},
        limited={"proteínas_comunes_si_hay_sospecha_alergia"},
        recommended={"ácidos_grasos_esenciales", "omega_3", "omega_6_equilibrado",
                     "zinc", "biotina", "vitamina_a"},
        special_rules={"dieta_hipoalergénica_si_alergia_confirmada",
                       "proteína_novela_si_sospecha_alergia_alimentaria"},
    ),
    "gastritis": _r(
        prohibited={"irritantes_gastrointestinales", "especias", "ácidos_fuertes",
                    "chile", "ají", "pimentón_crudo", "tomate_crudo",
                    "comidas_muy_frías_o_calientes"},
        limited={"fibra_insoluble_exceso", "grasa_exceso"},
        recommended={"alimentos_blandos_cocidos", "proteína_magra_digestible",
                     "arroz_blanco", "pollo_sin_piel"},
        special_rules={"sin_ayunos_mayores_6h",
                       "raciones_pequeñas_y_frecuentes",
                       "mínimo_4_comidas_por_dia"},
    ),
    "cistitis/enfermedad_urinaria": _r(
        prohibited={"fósforo_alto", "sodio_excesivo", "oxalatos_muy_altos"},
        limited={"fósforo", "sodio", "magnesio"},
        recommended={"hidratación_alta_explícita", "agua_adicional_en_comida",
                     "dieta_húmeda_preferida"},
        special_rules={"hidratación_máxima_prioritaria",
                       "ph_urinario_monitorear"},
    ),
    "sobrepeso/obesidad": _r(
        prohibited={"exceso_calórico", "alimentos_hipercalóricos",
                    "snacks_no_planificados"},
        limited={"grasa_total", "carbohidratos_simples", "calorías_totales"},
        recommended={"fibra_alta_saciedad", "proteína_magra",
                     "vegetales_bajos_calorías"},
        special_rules={"rer_sobre_peso_ideal_x_0_8",
                       "control_estricto_de_porciones",
                       "ejercicio_complementario"},
    ),
}

# Conjunto de condiciones válidas para validación rápida
VALID_CONDITIONS: frozenset[str] = frozenset(RESTRICTIONS_BY_CONDITION.keys())
