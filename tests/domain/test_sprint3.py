"""
Tests Sprint 3 — NutriVet.IA
Cubre: B-02 (razas gigantes NRC), B-03 (BARF alert), B-04 (IG diabéticos),
       B-05 (transición variable), C-06 (lipidosis felina + tiaminasa)
"""
import pytest


# ---------------------------------------------------------------------------
# B-02 — Razas gigantes: cronología adulto en NRCCalculator
# ---------------------------------------------------------------------------

class TestGiantBreedNRC:

    def test_gran_danes_14m_usa_factor_cachorro(self):
        """Gran Danés 14 meses → meses_adulto=24 → factor cachorro 2.0, no 1.2."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        # breed_adult_months=24 → a los 14m aún es cachorro
        factor = NRCCalculator._get_factor_edad("perro", age_months=14, breed_adult_months=24)
        assert factor == 2.0, f"Esperado 2.0 (cachorro), obtenido {factor}"

    def test_gran_danes_14m_sin_raza_usa_factor_adulto_joven(self):
        """Sin breed_adult_months, 14 meses cae en adulto joven (1.2)."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        factor = NRCCalculator._get_factor_edad("perro", age_months=14)
        assert factor == 1.2

    def test_gran_danes_25m_ya_es_adulto(self):
        """Gran Danés 25 meses ya superó madurez (24m) → adulto 1.0."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        factor = NRCCalculator._get_factor_edad("perro", age_months=25, breed_adult_months=24)
        assert factor == 1.0

    def test_gran_danes_2m_es_cachorro_temprano(self):
        """Gran Danés 2 meses → factor 3.0 (cachorro muy temprano)."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        factor = NRCCalculator._get_factor_edad("perro", age_months=2, breed_adult_months=24)
        assert factor == 3.0

    def test_rottweiler_18m_es_cachorro_con_raza(self):
        """Rottweiler meses_adulto=24, a los 18m → factor cachorro 2.0."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        factor = NRCCalculator._get_factor_edad("perro", age_months=18, breed_adult_months=24)
        assert factor == 2.0

    def test_labrador_12m_es_adulto_joven(self):
        """Labrador meses_adulto=12 (default), a los 12m → factor 2.0 (tabla genérica)."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        # 12 meses cae en rango (4,12) → factor 2.0
        factor = NRCCalculator._get_factor_edad("perro", age_months=12)
        assert factor == 2.0

    def test_calculate_der_accepts_breed_adult_months(self):
        """calculate_der acepta breed_adult_months sin romper."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(30.0)
        der = NRCCalculator.calculate_der(
            rer=rer,
            age_months=14,
            reproductive_status="esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=5,
            breed_adult_months=24,
        )
        # Con breed_adult_months=24, factor_edad=2.0 en vez de 1.2 → DER mayor
        der_sin_raza = NRCCalculator.calculate_der(
            rer=rer,
            age_months=14,
            reproductive_status="esterilizado",
            activity_level="moderado",
            species="perro",
            bcs=5,
        )
        assert der > der_sin_raza, "DER raza gigante debe ser mayor que sin raza (factor cachorro)"

    def test_gatos_no_afectados_por_breed_adult_months(self):
        """breed_adult_months no altera el comportamiento en gatos."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        # Gatos usan su propia tabla, breed_adult_months no aplica
        factor_con = NRCCalculator._get_factor_edad("gato", age_months=8, breed_adult_months=24)
        factor_sin = NRCCalculator._get_factor_edad("gato", age_months=8, breed_adult_months=0)
        assert factor_con == factor_sin


# ---------------------------------------------------------------------------
# B-05 — Transición variable por condición
# ---------------------------------------------------------------------------

class TestTransitionProtocol:

    def test_sano_transition_7_10_dias(self):
        from backend.domain.nutrition.transition_protocol import get_transition_protocol
        p = get_transition_protocol(conditions=[], current_diet="concentrado", new_diet="casero")
        assert p.min_dias == 7
        assert p.max_dias == 10

    def test_gastritis_transition_21_28_dias(self):
        from backend.domain.nutrition.transition_protocol import get_transition_protocol
        p = get_transition_protocol(
            conditions=["gastritis"],
            current_diet="concentrado",
            new_diet="natural",
        )
        assert p.max_dias >= 21

    def test_megaesofago_transition_30_42_dias(self):
        from backend.domain.nutrition.transition_protocol import get_transition_protocol
        p = get_transition_protocol(
            conditions=["megaesofago"],
            current_diet="concentrado",
            new_diet="natural",
        )
        assert p.min_dias >= 30
        assert p.max_dias >= 42

    def test_barf_a_concentrado_minimo_21_dias(self):
        from backend.domain.nutrition.transition_protocol import get_transition_protocol
        p = get_transition_protocol(
            conditions=[],
            current_diet="natural",
            new_diet="concentrado",
        )
        assert p.min_dias >= 21

    def test_condicion_mas_restrictiva_gana(self):
        """Si hay varias condiciones, se usa la que requiere más días."""
        from backend.domain.nutrition.transition_protocol import get_transition_protocol
        p_simple = get_transition_protocol(conditions=["gastritis"])
        p_mega = get_transition_protocol(conditions=["gastritis", "megaesofago"])
        assert p_mega.max_dias >= p_simple.max_dias

    def test_resultado_es_frozen_dataclass(self):
        from backend.domain.nutrition.transition_protocol import get_transition_protocol
        p = get_transition_protocol()
        with pytest.raises((AttributeError, TypeError)):
            p.min_dias = 99  # type: ignore

    def test_todos_los_contextos_estan_en_tabla(self):
        from backend.domain.nutrition.transition_protocol import TRANSITION_BY_CONDITION
        condiciones_esperadas = [
            "sano_no_sensible", "sano_sensible", "gastritis", "pancreático",
            "hepático/hiperlipidemia", "renal", "insuficiencia_cardiaca",
            "megaesofago", "diabético", "barf_a_concentrado", "concentrado_a_barf",
        ]
        for cond in condiciones_esperadas:
            assert cond in TRANSITION_BY_CONDITION, f"Falta '{cond}' en TRANSITION_BY_CONDITION"


# ---------------------------------------------------------------------------
# C-06 — Lipidosis hepática felina + Tiaminasa
# ---------------------------------------------------------------------------

class TestFelineSafetyChecks:

    # --- Lipidosis hepática ---

    def test_gato_24h_sin_comer_genera_alerta(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_feline_fasting_risk(
            species="gato",
            hours_without_food=24,
        )
        assert alerta is not None
        assert "lipidosis" in alerta.lower()

    def test_gato_48h_genera_alerta_emergencia(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_feline_fasting_risk(
            species="gato",
            hours_without_food=48,
        )
        assert alerta is not None
        assert "emergencia" in alerta.lower() or "urgencias" in alerta.lower()

    def test_perro_48h_no_genera_alerta_lipidosis(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_feline_fasting_risk(
            species="perro",
            hours_without_food=48,
        )
        assert alerta is None

    def test_gato_12h_no_genera_alerta(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_feline_fasting_risk(
            species="gato",
            hours_without_food=12,
        )
        assert alerta is None

    def test_gato_none_horas_no_genera_alerta(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_feline_fasting_risk(
            species="gato",
            hours_without_food=None,
        )
        assert alerta is None

    def test_gato_sobrepeso_alerta_menciona_riesgo_elevado(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_feline_fasting_risk(
            species="gato",
            hours_without_food=24,
            conditions=["sobrepeso/obesidad"],
        )
        assert alerta is not None
        assert "sobrepeso" in alerta.lower() or "riesgo" in alerta.lower()

    # --- Tiaminasa ---

    def test_salmon_crudo_gato_barf_genera_alerta(self):
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_tiaminasa_risk(
            ingredients=["salmón crudo", "pollo cocido", "batata"],
            species="gato",
            diet_type="natural",
        )
        assert alerta is not None
        assert "tiaminasa" in alerta.lower() or "b1" in alerta.lower()

    def test_salmon_crudo_perro_no_genera_alerta_tiaminasa(self):
        """Tiaminasa solo es crítica en gatos."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_tiaminasa_risk(
            ingredients=["salmón crudo"],
            species="perro",
            diet_type="natural",
        )
        assert alerta is None

    def test_salmon_crudo_gato_concentrado_no_genera_alerta(self):
        """Si la dieta es concentrado, tiaminasa no aplica."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_tiaminasa_risk(
            ingredients=["salmón crudo"],
            species="gato",
            diet_type="concentrado",
        )
        assert alerta is None

    def test_sardinas_enlatadas_gato_barf_seguras(self):
        """Sardinas enlatadas están cocidas — sin tiaminasa."""
        from backend.domain.safety.food_safety_checker import FoodSafetyChecker
        alerta = FoodSafetyChecker.check_tiaminasa_risk(
            ingredients=["sardinas en agua", "pollo cocido"],
            species="gato",
            diet_type="natural",
        )
        assert alerta is None


# ---------------------------------------------------------------------------
# B-03 — BARF safety block en system prompt
# ---------------------------------------------------------------------------

class TestBARFPromptInjection:

    def test_barf_block_in_natural_diet_prompt(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=[],
            species="perro",
            modality="natural",
        )
        assert "salmonella" in prompt.lower() or "bacteriol" in prompt.lower()

    def test_barf_block_absent_for_concentrado_prompt(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=[],
            species="perro",
            modality="concentrado",
        )
        assert "salmonella" not in prompt.lower()


# ---------------------------------------------------------------------------
# B-04 — IG diabéticos en system prompt
# ---------------------------------------------------------------------------

class TestDiabeticIGPrompt:

    def test_ig_block_in_diabetico_prompt(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=["diabético"],
            species="perro",
            modality="natural",
        )
        assert "índice glucémico" in prompt.lower() or "ig" in prompt.lower()
        assert "avena" in prompt.lower()

    def test_ig_block_absent_when_no_diabetes(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=["renal"],
            species="perro",
            modality="natural",
        )
        assert "índice glucémico" not in prompt.lower()
