"""
Tests Sprint 4 — NutriVet.IA
Cubre: B-01 (suplementación clínica), B-06 (interacciones fármaco-nutriente),
       B-07 (especificación compra ingredientes), protocolos 4 condiciones nuevas
"""
import pytest


# ---------------------------------------------------------------------------
# B-01 — Suplementación clínica por condición
# ---------------------------------------------------------------------------

class TestClinicalSupplements:

    def test_icc_has_taurina_dose(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("insuficiencia_cardiaca")
        assert "taurina" in supls
        assert "100" in supls["taurina"].dosis_perro

    def test_icc_has_l_carnitina(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("insuficiencia_cardiaca")
        assert "l_carnitina" in supls

    def test_icc_has_omega3_alta_dosis(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("insuficiencia_cardiaca")
        assert "omega3_epa_dha" in supls
        # Dosis terapéutica ≥ 40 mg/kg/día
        assert "40" in supls["omega3_epa_dha"].dosis_perro

    def test_articular_has_glucosamina_condroitina(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("articular")
        assert "glucosamina" in supls
        assert "condroitina" in supls

    def test_epilepsia_has_magnesio_dha(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("epilepsia")
        assert "magnesio" in supls
        assert "dha" in supls

    def test_cancerigeno_has_omega3_antitumoral(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("cancerígeno")
        assert "omega3_epa_dha" in supls
        # Dosis antitumoral 50 mg/kg/día
        assert "50" in supls["omega3_epa_dha"].dosis_perro

    def test_unknown_condition_returns_empty(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        assert get_supplements_for_condition("condicion_inexistente") == {}

    def test_get_all_supplements_for_multiple_conditions(self):
        from backend.domain.nutrition.clinical_supplements import get_all_supplements_for_conditions
        result = get_all_supplements_for_conditions(["articular", "epilepsia"])
        assert "articular" in result
        assert "epilepsia" in result
        assert "glucosamina" in result["articular"]

    def test_doses_are_frozen_dataclasses(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("insuficiencia_cardiaca")
        dose = supls["taurina"]
        with pytest.raises((AttributeError, TypeError)):
            dose.dosis_perro = "0"  # type: ignore

    def test_hepatico_has_silimarina(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("hepático/hiperlipidemia")
        assert "silimarina" in supls

    def test_renal_has_omega3_and_b_complex(self):
        from backend.domain.nutrition.clinical_supplements import get_supplements_for_condition
        supls = get_supplements_for_condition("renal")
        assert "omega3_epa_dha" in supls
        assert "b_complex" in supls


# ---------------------------------------------------------------------------
# B-06 — Interacciones fármaco-nutriente
# ---------------------------------------------------------------------------

class TestDrugNutrientInteractions:

    def test_epilepsia_fenobarbital_alert_exists(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        alerts = get_drug_nutrient_alerts("epilepsia")
        assert len(alerts) >= 1
        feno_alert = next(
            (a for a in alerts if "fenobarbital" in a.farmaco_probable.lower()), None
        )
        assert feno_alert is not None

    def test_icc_ieca_alert_warns_potasio(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        alerts = get_drug_nutrient_alerts("insuficiencia_cardiaca")
        ieca_alert = next(
            (a for a in alerts if "ieca" in a.farmaco_probable.lower()), None
        )
        assert ieca_alert is not None
        assert "potasio" in ieca_alert.alerta_vet.lower()

    def test_icc_furosemida_alert_warns_magnesio(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        alerts = get_drug_nutrient_alerts("insuficiencia_cardiaca")
        furo = next(
            (a for a in alerts if "furosemida" in a.farmaco_probable.lower()), None
        )
        assert furo is not None
        assert "magnesio" in furo.nutrientes_afectados

    def test_hipotiroideo_levotiroxina_alert_calcium(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        alerts = get_drug_nutrient_alerts("hipotiroideo")
        levo = next(
            (a for a in alerts if "levotiroxina" in a.farmaco_probable.lower()), None
        )
        assert levo is not None
        assert "calcio" in levo.nutrientes_afectados

    def test_owner_alerts_dont_mention_drug_names(self):
        """Las alertas para propietarios NO deben mencionar fármacos por nombre."""
        from backend.domain.safety.drug_nutrient_interactions import get_owner_alerts_for_conditions
        alerts = get_owner_alerts_for_conditions(["epilepsia", "insuficiencia_cardiaca"])
        drug_names = ["fenobarbital", "enalapril", "benazepril", "furosemida",
                      "levotiroxina", "trilostano", "mitotano"]
        for alert in alerts:
            for drug in drug_names:
                assert drug.lower() not in alert.lower(), (
                    f"Alerta propietario menciona fármaco '{drug}': {alert}"
                )

    def test_vet_notes_include_technical_details(self):
        from backend.domain.safety.drug_nutrient_interactions import get_vet_notes_for_conditions
        notes = get_vet_notes_for_conditions(["epilepsia"])
        assert len(notes) >= 1
        assert any("fenobarbital" in n.lower() for n in notes)

    def test_unknown_condition_returns_empty_list(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        assert get_drug_nutrient_alerts("condicion_sin_alertas") == []

    def test_cushing_trilostano_alert_exists(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        alerts = get_drug_nutrient_alerts("hiperadrenocorticismo_cushing")
        assert len(alerts) >= 1

    def test_alerts_are_frozen_dataclasses(self):
        from backend.domain.safety.drug_nutrient_interactions import get_drug_nutrient_alerts
        alerts = get_drug_nutrient_alerts("epilepsia")
        with pytest.raises((AttributeError, TypeError)):
            alerts[0].alerta_vet = "modificado"  # type: ignore


# ---------------------------------------------------------------------------
# B-07 — Especificación de compra en IngredienteSchema
# ---------------------------------------------------------------------------

class TestIngredienteSchemaB07:

    def test_ingrediente_accepts_especificacion_compra(self):
        from backend.infrastructure.agent.prompts.json_schemas import IngredienteSchema
        ing = IngredienteSchema(
            nombre="Sardinas",
            cantidad_g=50.0,
            kcal=54.0,
            especificacion_compra="En agua, sin sal añadida. NO en aceite de girasol.",
        )
        assert ing.especificacion_compra is not None
        assert "sin sal" in ing.especificacion_compra

    def test_ingrediente_accepts_alternativas(self):
        from backend.infrastructure.agent.prompts.json_schemas import IngredienteSchema
        ing = IngredienteSchema(
            nombre="Pechuga de pollo",
            cantidad_g=100.0,
            kcal=110.0,
            alternativas_equivalentes=["Pechuga de pavo", "Pechuga de codorniz"],
        )
        assert len(ing.alternativas_equivalentes) == 2
        assert "Pechuga de pavo" in ing.alternativas_equivalentes

    def test_ingrediente_fields_optional_backward_compat(self):
        """Los campos nuevos son opcionales — backward compatible."""
        from backend.infrastructure.agent.prompts.json_schemas import IngredienteSchema
        ing = IngredienteSchema(
            nombre="Pollo",
            cantidad_g=100.0,
            kcal=110.0,
        )
        assert ing.especificacion_compra is None
        assert ing.alternativas_equivalentes == []

    def test_json_format_includes_especificacion(self):
        from backend.infrastructure.agent.prompts.json_schemas import JSON_FORMAT_INSTRUCTION
        assert "especificacion_compra" in JSON_FORMAT_INSTRUCTION
        assert "alternativas_equivalentes" in JSON_FORMAT_INSTRUCTION


# ---------------------------------------------------------------------------
# Nuevos protocolos de condición (A-04 + condition_protocols.py)
# ---------------------------------------------------------------------------

class TestNewConditionProtocols:

    def test_icc_protocol_in_all_protocols(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        assert "insuficiencia_cardiaca" in ALL_PROTOCOLS

    def test_cushing_protocol_in_all_protocols(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        assert "hiperadrenocorticismo_cushing" in ALL_PROTOCOLS

    def test_epilepsia_protocol_in_all_protocols(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        assert "epilepsia" in ALL_PROTOCOLS

    def test_megaesofago_protocol_in_all_protocols(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        assert "megaesofago" in ALL_PROTOCOLS

    def test_all_17_conditions_have_protocols(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        from backend.domain.safety.medical_restrictions import VALID_CONDITIONS
        missing = VALID_CONDITIONS - set(ALL_PROTOCOLS.keys())
        assert not missing, f"Condiciones sin protocolo: {missing}"

    def test_icc_protocol_has_taurina_supplement(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        icc = ALL_PROTOCOLS["insuficiencia_cardiaca"]
        nombres = [s.nombre.lower() for s in icc.suplementos]
        assert any("taurina" in n for n in nombres)

    def test_megaesofago_protocol_has_vertical_rule(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        mega = ALL_PROTOCOLS["megaesofago"]
        reglas = " ".join(mega.reglas_especiales).lower()
        assert "vertical" in reglas or "bailey" in reglas

    def test_icc_protocol_sodio_restringido(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        icc = ALL_PROTOCOLS["insuficiencia_cardiaca"]
        assert icc.sodio_mg_dia_max is not None
        assert icc.sodio_mg_dia_max <= 100

    def test_megaesofago_minimum_4_meals(self):
        from backend.infrastructure.agent.prompts.condition_protocols import ALL_PROTOCOLS
        mega = ALL_PROTOCOLS["megaesofago"]
        assert mega.numero_comidas_dia >= 4

    def test_get_protocols_for_new_conditions(self):
        from backend.infrastructure.agent.prompts.condition_protocols import get_protocols_for_conditions
        protos = get_protocols_for_conditions([
            "insuficiencia_cardiaca",
            "epilepsia",
            "megaesofago",
            "hiperadrenocorticismo_cushing",
        ])
        assert len(protos) == 4
