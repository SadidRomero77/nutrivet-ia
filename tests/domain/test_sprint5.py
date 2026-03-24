"""
Tests Sprint 5 — NutriVet.IA
Cubre: C-01 (_build_supplements_block integrado en plan prompt),
       C-02 (_build_drug_nutrient_block integrado en plan prompt),
       C-03 (_build_drug_awareness_block integrado en conversation prompt)
"""
import pytest


# ---------------------------------------------------------------------------
# C-01 — _build_supplements_block en plan_generation_prompts
# ---------------------------------------------------------------------------

class TestBuildSupplementsBlock:

    def test_icc_perro_includes_taurina_dosis(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block(["insuficiencia_cardiaca"], "perro")
        assert "taurina" in block.lower()
        assert "100 mg/kg/día" in block

    def test_icc_gato_uses_gato_dose(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block(["insuficiencia_cardiaca"], "gato")
        assert "250 mg/kg/día" in block  # dosis_gato taurina

    def test_empty_for_no_conditions(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block([], "perro")
        assert block == ""

    def test_empty_for_unknown_condition(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block(["condicion_sin_suplementos"], "perro")
        assert block == ""

    def test_includes_header_obligatorio(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block(["articular"], "perro")
        assert "OBLIGATORIO" in block or "SUPLEMENTOS" in block

    def test_multiple_conditions_merged(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block(
            ["insuficiencia_cardiaca", "articular"], "perro"
        )
        assert "taurina" in block.lower()
        assert "glucosamina" in block.lower()

    def test_hepatico_includes_silimarina(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_supplements_block,
        )
        block = _build_supplements_block(["hepático/hiperlipidemia"], "perro")
        assert "silimarina" in block.lower()


# ---------------------------------------------------------------------------
# C-02 — _build_drug_nutrient_block en plan_generation_prompts
# ---------------------------------------------------------------------------

class TestBuildDrugNutrientBlock:

    def test_epilepsia_includes_fenobarbital_vet_note(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_drug_nutrient_block,
        )
        block = _build_drug_nutrient_block(["epilepsia"])
        assert "fenobarbital" in block.lower()

    def test_icc_includes_ieca_and_furosemida(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_drug_nutrient_block,
        )
        block = _build_drug_nutrient_block(["insuficiencia_cardiaca"])
        assert "ieca" in block.lower() or "furosemida" in block.lower()

    def test_empty_for_no_conditions(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_drug_nutrient_block,
        )
        block = _build_drug_nutrient_block([])
        assert block == ""

    def test_empty_for_unknown_condition(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_drug_nutrient_block,
        )
        block = _build_drug_nutrient_block(["articular"])  # sin alertas fármaco
        assert block == ""

    def test_owner_alert_section_without_drug_names(self):
        """Las alertas propietario en el bloque no deben mencionar fármacos por nombre."""
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_drug_nutrient_block,
        )
        block = _build_drug_nutrient_block(["epilepsia"])
        # Separar la sección de owner de la de vet
        if "PARA PROPIETARIO" in block:
            owner_section = block.split("PARA PROPIETARIO")[-1]
            drug_names = ["fenobarbital", "enalapril", "furosemida", "levotiroxina"]
            for drug in drug_names:
                assert drug.lower() not in owner_section.lower(), (
                    f"Fármaco '{drug}' aparece en sección propietario"
                )

    def test_includes_notas_clinicas_header(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            _build_drug_nutrient_block,
        )
        block = _build_drug_nutrient_block(["epilepsia"])
        assert "notas_clinicas" in block.lower() or "VET" in block


# ---------------------------------------------------------------------------
# C-01+C-02 — Integración en build_plan_system_prompt
# ---------------------------------------------------------------------------

class TestPlanSystemPromptIntegration:

    def test_plan_prompt_includes_supplement_block_for_icc(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=["insuficiencia_cardiaca"],
            species="perro",
            modality="natural",
        )
        assert "taurina" in prompt.lower()

    def test_plan_prompt_includes_drug_block_for_epilepsia(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=["epilepsia"],
            species="perro",
            modality="natural",
        )
        assert "fenobarbital" in prompt.lower()

    def test_plan_prompt_no_supplement_block_for_healthy_pet(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=[],
            species="perro",
            modality="natural",
        )
        assert "SUPLEMENTOS TERAPÉUTICOS OBLIGATORIOS" not in prompt

    def test_plan_prompt_no_drug_block_for_healthy_pet(self):
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        prompt = build_plan_system_prompt(
            conditions=[],
            species="perro",
            modality="natural",
        )
        assert "FÁRMACO-NUTRIENTE" not in prompt

    def test_sally_prompt_includes_all_5_condition_blocks(self):
        """Caso Sally (5 condiciones) debe incluir suplementos y alertas fármaco."""
        from backend.infrastructure.agent.prompts.plan_generation_prompts import (
            build_plan_system_prompt,
        )
        sally_conditions = [
            "diabético",
            "hepático/hiperlipidemia",
            "gastritis",
            "cistitis/enfermedad_urinaria",
            "hipotiroideo",
        ]
        prompt = build_plan_system_prompt(
            conditions=sally_conditions,
            species="perro",
            modality="natural",
        )
        # Debe tener bloque de condición
        assert "PROTOCOLOS ACTIVOS" in prompt
        # Debe tener bloque IG (diabético)
        assert "ÍNDICE GLICÉMICO" in prompt or "IG" in prompt
        # Hipotiroideo tiene levotiroxina alert
        assert "levotiroxina" in prompt.lower()
        # Silimarina para hepático
        assert "silimarina" in prompt.lower()


# ---------------------------------------------------------------------------
# C-03 — _build_drug_awareness_block en conversation_prompts
# ---------------------------------------------------------------------------

class TestDrugAwarenessBlock:

    def test_vet_tier_includes_technical_drug_names(self):
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            _build_drug_awareness_block,
        )
        block = _build_drug_awareness_block(["epilepsia"], "VET")
        assert "fenobarbital" in block.lower()

    def test_owner_tier_excludes_drug_names(self):
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            _build_drug_awareness_block,
        )
        block = _build_drug_awareness_block(["epilepsia"], "FREE")
        drug_names = ["fenobarbital", "enalapril", "furosemida", "levotiroxina"]
        for drug in drug_names:
            assert drug.lower() not in block.lower(), (
                f"Fármaco '{drug}' no debería aparecer para tier FREE"
            )

    def test_empty_for_no_conditions(self):
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            _build_drug_awareness_block,
        )
        block = _build_drug_awareness_block([], "VET")
        assert block == ""

    def test_empty_for_condition_without_drug_alerts(self):
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            _build_drug_awareness_block,
        )
        block = _build_drug_awareness_block(["articular"], "FREE")
        assert block == ""

    def test_conversation_prompt_includes_drug_block_for_vet(self):
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            build_conversation_system_prompt,
        )
        prompt = build_conversation_system_prompt(
            pet_profile=None,
            active_plan=None,
            user_tier="VET",
            conditions=["epilepsia"],
        )
        assert "fenobarbital" in prompt.lower()

    def test_conversation_prompt_no_drug_block_for_healthy_pet(self):
        """Sin condiciones, el bloque condicional B-06 NO se inyecta.
        (El conocimiento base general puede mencionar fármacos como ejemplos educativos.)
        """
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            build_conversation_system_prompt,
        )
        prompt = build_conversation_system_prompt(
            pet_profile=None,
            active_plan=None,
            user_tier="VET",
            conditions=[],
        )
        # El bloque CONDICIONAL de contexto fármaco no se inyecta para mascota sana
        assert "CONTEXTO FÁRMACO-NUTRIENTE" not in prompt

    def test_conversation_prompt_backward_compat_no_conditions_param(self):
        """conditions es opcional — no rompe llamadas existentes."""
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            build_conversation_system_prompt,
        )
        prompt = build_conversation_system_prompt(
            pet_profile=None,
            active_plan=None,
            user_tier="FREE",
        )
        assert len(prompt) > 100  # se construye sin error

    def test_basico_tier_with_condition_excludes_drug_names(self):
        from backend.infrastructure.agent.prompts.conversation_prompts import (
            _build_drug_awareness_block,
        )
        block = _build_drug_awareness_block(["hipotiroideo"], "BASICO")
        assert "levotiroxina" not in block.lower()
        # Pero sí tiene alguna alerta simplificada
        if block:
            assert len(block) > 10
