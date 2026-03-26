"""
G1 — Golden Set: Cero tóxicos en planes generados.
G2 — 100% restricciones médicas aplicadas (17 condiciones).

Quality Gate: P0 — bloquea release si cualquier test falla.
Constitution REGLA 1: toxicidad hard-coded — tolerancia CERO.
Constitution REGLA 2: restricciones médicas — tolerancia CERO.

Estos tests son 100% determinísticos (sin LLM, sin red, sin DB).
Validan las capas de seguridad que el LLM NO puede sobrescribir.
"""
from __future__ import annotations

import pytest

from backend.domain.safety.food_safety_checker import FoodSafetyChecker
from backend.domain.safety.medical_restriction_engine import MedicalRestrictionEngine
from backend.domain.safety.medical_restrictions import RESTRICTIONS_BY_CONDITION


# ═══════════════════════════════════════════════════════════════════════════════
# G1 — Toxicidad: tolerancia CERO
# ═══════════════════════════════════════════════════════════════════════════════

class TestG1ToxicidadPerro:
    """
    G1-A: Verifica que cada ingrediente tóxico conocido para perros
    es rechazado correctamente por FoodSafetyChecker.
    60 ingredientes de prueba — incluyendo nombres científicos y aliases regionales.
    """

    _TOXICOS_PERRO = [
        # Allium spp.
        "cebolla", "cebolla cabezona", "cebollín", "puerro",
        "ajo", "ajo en polvo", "allium sativum", "allium cepa",
        # Uvas y derivados
        "uvas", "uva", "pasas", "pasa", "vitis vinifera",
        "uvas de corinto", "grosellas",
        # Xilitol
        "xilitol", "xylitol",
        # Chocolate
        "chocolate", "cacao", "cocoa", "theobroma cacao",
        # Cafeína
        "cafeína", "café",
        # Macadamia
        "macadamia", "nuez de macadamia",
        # Aguacate
        "aguacate", "palta", "persea americana",
        # Otros
        "alcohol", "etanol",
        "nuez moscada", "moscada",
        "masa de levadura cruda", "levadura cruda",
    ]

    @pytest.mark.parametrize("ingrediente", _TOXICOS_PERRO)
    def test_ingrediente_toxico_detectado_perro(self, ingrediente: str) -> None:
        """G1: ingrediente tóxico para perro es rechazado (tolerancia CERO)."""
        result = FoodSafetyChecker.check_ingredient(ingrediente, "perro")
        assert result.is_toxic, (
            f"FALLO G1: '{ingrediente}' debería ser tóxico para perro "
            f"pero no fue detectado. Resultado: is_toxic={result.is_toxic}"
        )

    @pytest.mark.parametrize("ingrediente", _TOXICOS_PERRO)
    def test_ingrediente_toxico_perro_tiene_razon(self, ingrediente: str) -> None:
        """G1: resultado tóxico incluye razón no vacía."""
        result = FoodSafetyChecker.check_ingredient(ingrediente, "perro")
        assert result.reason, f"'{ingrediente}': resultado sin razón explicativa"


class TestG1ToxicidadGato:
    """
    G1-B: Verifica ingredientes tóxicos específicos para gatos.
    Los gatos tienen sensibilidades distintas (lilium, paracetamol, propylene glycol).
    """

    _TOXICOS_GATO = [
        # Allium
        "cebolla", "ajo", "allium sativum", "allium cepa",
        # Uvas
        "uvas", "uva", "pasas", "vitis vinifera",
        # Lilium (crítico en gatos — solo el polen puede causar falla renal)
        "lilium", "lirio", "azucena",
        # Chocolate / cafeína
        "chocolate", "cacao", "cafeína", "café",
        # Xilitol
        "xilitol", "xylitol",
        # AINES — metabolismo hepático limitado en gatos
        "paracetamol", "acetaminofén",
        "ibuprofeno",
        # Propylene glycol
        "propilenglicol",
        # Alcohol
        "alcohol", "etanol",
    ]

    @pytest.mark.parametrize("ingrediente", _TOXICOS_GATO)
    def test_ingrediente_toxico_detectado_gato(self, ingrediente: str) -> None:
        """G1: ingrediente tóxico para gato es rechazado (tolerancia CERO)."""
        result = FoodSafetyChecker.check_ingredient(ingrediente, "gato")
        assert result.is_toxic, (
            f"FALLO G1: '{ingrediente}' debería ser tóxico para gato "
            f"pero no fue detectado."
        )


class TestG1AliasesYNombresAlternativos:
    """
    G1-C: El LLM puede usar nombres científicos, aliases regionales o variantes.
    Todos deben ser detectados.
    """

    @pytest.mark.parametrize("alias,especie", [
        ("vitis vinifera", "perro"),     # uva — nombre científico
        ("vitis vinifera", "gato"),
        ("palta", "perro"),              # aguacate — alias regional (Perú/Chile)
        ("persea americana", "perro"),   # aguacate — nombre científico
        ("allium sativum", "perro"),     # ajo — nombre científico
        ("allium cepa", "perro"),        # cebolla — nombre científico
        ("theobroma cacao", "perro"),    # chocolate — nombre científico
        ("theobroma cacao", "gato"),
        ("xylitol", "perro"),            # xilitol — ortografía alternativa
        ("xylitol", "gato"),
        ("acetaminofén", "gato"),        # paracetamol — nombre genérico
        ("lilium longiflorum", "gato"),  # lirio — nombre científico
        ("hemerocallis", "gato"),        # lirio de día — también nefrotóxico
    ])
    def test_alias_toxico_detectado(self, alias: str, especie: str) -> None:
        """G1: alias y nombres científicos también son detectados."""
        result = FoodSafetyChecker.check_ingredient(alias, especie)
        assert result.is_toxic, (
            f"FALLO G1: alias '{alias}' para {especie} no fue detectado como tóxico"
        )


class TestG1IngredientesSegurosFalsoPositivo:
    """
    G1-D: Ingredientes seguros NO deben ser marcados como tóxicos (falsos positivos).
    Un falso positivo bloquea planes válidos innecesariamente.
    """

    _SEGUROS_PERRO = [
        "pollo", "pechuga de pollo", "pollo cocido",
        "arroz", "arroz blanco cocido",
        "batata", "papa cocida", "zanahoria",
        "brócoli cocido", "espinaca",
        "salmón cocido", "atún cocido",
        "huevo cocido", "claras de huevo",
        "avena cocida",
        "aceite de oliva", "aceite de coco",
        "hígado de pollo", "hígado de res",
        "calabaza", "ahuyama", "zapallo",
        "arándanos",
    ]

    _SEGUROS_GATO = [
        "pollo cocido", "atún cocido", "salmón cocido",
        "hígado de pollo", "riñones de pollo",
        "huevo cocido", "carne de res magra",
        "calabaza cocida", "zanahoria cocida",
    ]

    @pytest.mark.parametrize("ingrediente", _SEGUROS_PERRO)
    def test_ingrediente_seguro_no_es_toxico_perro(self, ingrediente: str) -> None:
        """G1: ingrediente seguro no genera falso positivo para perro."""
        result = FoodSafetyChecker.check_ingredient(ingrediente, "perro")
        assert not result.is_toxic, (
            f"FALSO POSITIVO G1: '{ingrediente}' fue marcado como tóxico para perro"
        )

    @pytest.mark.parametrize("ingrediente", _SEGUROS_GATO)
    def test_ingrediente_seguro_no_es_toxico_gato(self, ingrediente: str) -> None:
        """G1: ingrediente seguro no genera falso positivo para gato."""
        result = FoodSafetyChecker.check_ingredient(ingrediente, "gato")
        assert not result.is_toxic, (
            f"FALSO POSITIVO G1: '{ingrediente}' fue marcado como tóxico para gato"
        )


class TestG1CheckPlanCompleto:
    """
    G1-E: check_ingredients con lista mixta — plan real simulado.
    Un plan que mezcla ingredientes seguros con uno tóxico debe fallar.
    """

    def test_plan_con_un_toxico_falla_todo(self) -> None:
        """G1: si el plan tiene 1 tóxico entre 10 ingredientes — se detecta."""
        plan_ingredientes = [
            "pollo cocido", "arroz", "zanahoria", "brócoli cocido",
            "batata", "aceite de oliva", "calabaza", "espinaca",
            "huevo cocido",
            "uvas",  # ← TÓXICO
        ]
        results = FoodSafetyChecker.validate_plan_ingredients(plan_ingredientes, "perro")
        toxicos = [r for r in results if r.is_toxic]
        assert len(toxicos) == 1
        assert toxicos[0].ingredient == "uvas"

    def test_plan_sin_toxicos_pasa(self) -> None:
        """G1: plan completamente seguro — ningún resultado tóxico."""
        plan_ingredientes = [
            "pollo cocido", "arroz blanco", "zanahoria cocida",
            "brócoli cocido", "batata cocida", "aceite de oliva",
        ]
        results = FoodSafetyChecker.validate_plan_ingredients(plan_ingredientes, "perro")
        assert not any(r.is_toxic for r in results)

    def test_plan_gato_con_lirio_falla(self) -> None:
        """G1: lirio en plan de gato — detectado inmediatamente (P0 crítico)."""
        ingredientes = ["pollo cocido", "arroz", "lilium", "zanahoria"]
        results = FoodSafetyChecker.validate_plan_ingredients(ingredientes, "gato")
        toxicos = [r for r in results if r.is_toxic]
        assert any(r.ingredient == "lilium" for r in toxicos)


# ═══════════════════════════════════════════════════════════════════════════════
# G2 — Restricciones médicas: 17 condiciones, tolerancia CERO
# ═══════════════════════════════════════════════════════════════════════════════

class TestG2RestriccionesExisten:
    """
    G2-A: Las 17 condiciones están definidas en RESTRICTIONS_BY_CONDITION.
    Si falta alguna, el agente no puede aplicar restricciones para esa condición.
    """

    _CONDICIONES_ESPERADAS = [
        # 13 originales
        "diabético", "hipotiroideo", "cancerígeno", "articular", "renal",
        "hepático/hiperlipidemia", "pancreático", "neurodegenerativo",
        "bucal/periodontal", "piel/dermatitis", "gastritis",
        "cistitis/enfermedad_urinaria", "sobrepeso/obesidad",
        # 4 Sprint 4
        "insuficiencia_cardiaca", "hiperadrenocorticismo_cushing",
        "epilepsia", "megaesofago",
    ]

    @pytest.mark.parametrize("condicion", _CONDICIONES_ESPERADAS)
    def test_condicion_tiene_restricciones_definidas(self, condicion: str) -> None:
        """G2: cada condición existe en RESTRICTIONS_BY_CONDITION."""
        assert condicion in RESTRICTIONS_BY_CONDITION, (
            f"FALLO G2: condición '{condicion}' no tiene restricciones definidas"
        )

    def test_total_condiciones_es_17(self) -> None:
        """G2: hay exactamente 17 condiciones registradas."""
        assert len(RESTRICTIONS_BY_CONDITION) == 17, (
            f"Se esperaban 17 condiciones, hay {len(RESTRICTIONS_BY_CONDITION)}: "
            f"{sorted(RESTRICTIONS_BY_CONDITION.keys())}"
        )


class TestG2RestriccionesProhibidos:
    """
    G2-B: Los ingredientes prohibidos por cada condición son rechazados
    por MedicalRestrictionEngine.validate_ingredient_against_conditions().
    Un ingrediente prohibido en el plan de un paciente con esa condición
    debe generar una violación detectable — tolerancia CERO.
    """

    _CASOS_PROHIBIDOS: list[tuple[str, str]] = [
        # (condicion, ingrediente_prohibido)
        ("diabético", "azúcar"),
        ("diabético", "miel"),
        ("diabético", "glucosa"),
        ("hipotiroideo", "soya_cruda"),
        ("hipotiroideo", "col_cruda"),
        ("cancerígeno", "azúcar"),
        ("cancerígeno", "alimentos_ultraprocesados"),
        ("renal", "fósforo_alto"),
        ("renal", "sodio_excesivo"),
        ("renal", "proteína_alta"),
        ("hepático/hiperlipidemia", "grasas_saturadas_en_exceso"),
        ("hepático/hiperlipidemia", "cobre_alto"),
        ("pancreático", "grasas_totales_mayor_10pct_ms"),
        ("pancreático", "ayuno_mayor_6h"),
        ("pancreático", "comidas_grandes"),
        ("bucal/periodontal", "azúcares_fermentables"),
        ("bucal/periodontal", "almidón_pegajoso"),
        ("gastritis", "especias"),
        ("gastritis", "chile"),
        ("gastritis", "tomate_crudo"),
        ("cistitis/enfermedad_urinaria", "fósforo_alto"),
        ("cistitis/enfermedad_urinaria", "sodio_excesivo"),
        ("sobrepeso/obesidad", "exceso_calórico"),
        ("sobrepeso/obesidad", "snacks_no_planificados"),
        ("insuficiencia_cardiaca", "sodio_alto"),
        ("insuficiencia_cardiaca", "embutidos"),
        ("insuficiencia_cardiaca", "jamón"),
        ("insuficiencia_cardiaca", "tocino"),
        ("hiperadrenocorticismo_cushing", "azúcares_simples"),
        ("hiperadrenocorticismo_cushing", "sodio_alto"),
        ("epilepsia", "glutamato_monosódico"),
        ("epilepsia", "colorantes_artificiales"),
        ("megaesofago", "huesos"),
        ("megaesofago", "sólidos_grandes"),
        ("megaesofago", "croquetas_secas_sin_remojar"),
    ]

    @pytest.mark.parametrize("condicion,ingrediente", _CASOS_PROHIBIDOS)
    def test_ingrediente_prohibido_detectado(
        self, condicion: str, ingrediente: str
    ) -> None:
        """G2: ingrediente prohibido genera violación para la condición dada."""
        violations = MedicalRestrictionEngine.validate_ingredient_against_conditions(
            ingredient=ingrediente,
            conditions=[condicion],
        )
        assert violations, (
            f"FALLO G2: '{ingrediente}' es prohibido en '{condicion}' "
            f"pero no generó violación. Tolerancia CERO."
        )

    def test_ingrediente_no_prohibido_no_genera_violacion(self) -> None:
        """G2: ingrediente seguro no genera falsa violación."""
        violations = MedicalRestrictionEngine.validate_ingredient_against_conditions(
            ingredient="pollo cocido",
            conditions=["diabético"],
        )
        real_violations = [v for v in violations if v.is_violation]
        assert not real_violations, (
            "'pollo cocido' no es ingrediente prohibido para diabético "
            f"pero generó violación: {real_violations}"
        )


class TestG2RestriccionesMultiplesCondiciones:
    """
    G2-C: Con múltiples condiciones simultáneas, se aplican todas las restricciones.
    El caso Sally (5 condiciones) es el golden case de referencia.
    """

    def test_sally_restricciones_acumuladas(self) -> None:
        """
        G2: Sally tiene 5 condiciones — sus restricciones se acumulan.
        Diabético + Hepático + Gastritis + Cistitis + Hipotiroideo.
        """
        condiciones = [
            "diabético", "hepático/hiperlipidemia",
            "gastritis", "cistitis/enfermedad_urinaria", "hipotiroideo",
        ]
        result = MedicalRestrictionEngine.get_restrictions_for_conditions(condiciones)

        # Cada condición debe aportar al menos 1 elemento prohibido
        assert len(result.prohibited) > 0, "Sally debe tener ingredientes prohibidos"

        # Específicos esperados en la unión
        assert "azúcar" in result.prohibited, "diabético → azúcar prohibida"
        assert "grasas_saturadas_en_exceso" in result.prohibited, \
            "hepático → grasas_saturadas_en_exceso prohibidas"
        assert "chile" in result.prohibited, "gastritis → chile prohibido"
        assert "fósforo_alto" in result.prohibited, \
            "cistitis → fósforo_alto prohibido"
        assert "soya_cruda" in result.prohibited, "hipotiroideo → soya_cruda prohibida"

    def test_cardiopatia_renal_restricciones_combinadas(self) -> None:
        """G2: insuficiencia_cardiaca + renal — sodio y fósforo prohibidos."""
        condiciones = ["insuficiencia_cardiaca", "renal"]
        result = MedicalRestrictionEngine.get_restrictions_for_conditions(condiciones)
        assert "sodio_alto" in result.prohibited
        assert "fósforo_alto" in result.prohibited

    def test_condicion_invalida_es_rechazada(self) -> None:
        """G2: condición desconocida → DomainError (fail fast — no aplicación parcial)."""
        from backend.domain.exceptions.domain_errors import DomainError
        with pytest.raises(DomainError, match="Condición médica desconocida"):
            MedicalRestrictionEngine.get_restrictions_for_conditions(
                ["diabético", "condicion_inexistente"]
            )


class TestG2ReglasEspeciales:
    """
    G2-D: Reglas especiales críticas — ayuno máximo (REGLA 10), posición vertical (megaesófago).
    """

    def test_megaesofago_tiene_regla_posicion_vertical(self) -> None:
        """G2: megaesófago incluye regla de Bailey chair (posición vertical obligatoria)."""
        r = RESTRICTIONS_BY_CONDITION["megaesofago"]
        posicion_rules = [
            rule for rule in r.special_rules
            if "vertical" in rule.lower() or "bailey" in rule.lower()
        ]
        assert posicion_rules, (
            "megaesofago debe tener regla de posición vertical — "
            "riesgo de neumonía aspirativa (P0)"
        )

    def test_pancreatico_sin_ayuno_mayor_6h(self) -> None:
        """G2: pancreático prohíbe ayuno > 6h (REGLA 10 derivada)."""
        r = RESTRICTIONS_BY_CONDITION["pancreático"]
        assert "ayuno_mayor_6h" in r.prohibited

    def test_gastritis_sin_ayuno_mayor_6h_regla(self) -> None:
        """G2: gastritis prohíbe ayunos mayores a 6h."""
        r = RESTRICTIONS_BY_CONDITION["gastritis"]
        ayuno_rules = [ru for ru in r.special_rules if "ayuno" in ru]
        assert ayuno_rules

    def test_insuficiencia_cardiaca_taurina_recomendada(self) -> None:
        """G2: ICC debe incluir taurina como recomendada (esencial cardíaco)."""
        r = RESTRICTIONS_BY_CONDITION["insuficiencia_cardiaca"]
        assert "taurina" in r.recommended

    def test_epilepsia_sin_glutamato(self) -> None:
        """G2: epilepsia prohíbe glutamato monosódico."""
        r = RESTRICTIONS_BY_CONDITION["epilepsia"]
        assert "glutamato_monosódico" in r.prohibited

    def test_todas_condiciones_tienen_al_menos_una_regla(self) -> None:
        """G2: ninguna condición tiene restricciones completamente vacías."""
        for condicion, restr in RESTRICTIONS_BY_CONDITION.items():
            tiene_algo = (
                bool(restr.prohibited)
                or bool(restr.limited)
                or bool(restr.recommended)
                or bool(restr.special_rules)
            )
            assert tiene_algo, (
                f"Condición '{condicion}' no tiene ninguna restricción definida"
            )
