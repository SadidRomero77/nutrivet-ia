"""
Tests RED — Plan Generation Subgraph (NUT-63 · Paso 3).

Tests de los 10 nodos del subgrafo de generación de planes.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.agent.subgraphs.plan_generation import (
    nodo_2_calculate_nutrition,
    nodo_3_apply_restrictions,
    nodo_4_check_safety_pre,
    nodo_5_select_llm,
    nodo_7_validate_output,
    nodo_8_generate_substitutes,
    nodo_9_determine_hitl,
)


def _state_with_pet(
    conditions: list[str] | None = None,
    allergies: list[str] | None = None,
    bcs: int = 5,
    species: str = "perro",
    user_tier: str = "FREE",
) -> NutriVetState:
    """Helper: crea un state con pet_profile para tests de nodos 2-9."""
    return NutriVetState(
        user_id="user-1",
        pet_id=str(uuid.uuid4()),
        user_tier=user_tier,
        user_role="owner",
        message="quiero un plan nutricional",
        modality="natural",
        pet_profile={
            "pet_id": str(uuid.uuid4()),
            "species": species,
            "weight_kg": 10.08,
            "age_months": 96,
            "reproductive_status": "esterilizado",
            "activity_level": "sedentario",
            "bcs": bcs,
            "medical_conditions": conditions or [],
            "allergies": allergies or [],
            "owner_id": str(uuid.uuid4()),
        },
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
    )


# ─── Nodo 2: calculate_nutrition ──────────────────────────────────────────────

class TestCalculateNutrition:
    """Nodos 1-5 son determinísticos — sin llamadas LLM."""

    def test_nrc_no_llm_calcula_rer_der(self) -> None:
        """nodo_2 calcula RER/DER sin LLM (determinístico)."""
        state = _state_with_pet()
        result = nodo_2_calculate_nutrition(state)
        assert result["rer_kcal"] > 0
        assert result["der_kcal"] > 0

    def test_sally_golden_case_rer_der(self) -> None:
        """
        Caso Sally: RER ≈ 396 kcal · DER ≈ 534 kcal (±0.5 kcal) — G8.

        French Poodle · 10.08 kg · 8 años · esterilizada · sedentaria · BCS 6/9
        """
        state = _state_with_pet(
            conditions=["diabético", "hepático/hiperlipidemia", "gastritis",
                        "cistitis/enfermedad_urinaria", "hipotiroideo"],
            bcs=6,
        )
        # Override peso exacto para Sally
        state["pet_profile"]["weight_kg"] = 10.08
        state["pet_profile"]["age_months"] = 96  # 8 años
        state["pet_profile"]["reproductive_status"] = "esterilizado"
        state["pet_profile"]["activity_level"] = "sedentario"

        result = nodo_2_calculate_nutrition(state)
        assert abs(result["rer_kcal"] - 396.0) <= 0.5, f"RER={result['rer_kcal']}"
        assert abs(result["der_kcal"] - 534.0) <= 0.5, f"DER={result['der_kcal']}"


# ─── Nodo 3: apply_restrictions ───────────────────────────────────────────────

class TestApplyRestrictions:
    def test_restricciones_por_condicion_medica(self) -> None:
        """Mascota con condición → tiene restricciones."""
        state = _state_with_pet(conditions=["renal"])
        result = nodo_3_apply_restrictions(state)
        assert isinstance(result["medical_restrictions"], list)
        assert len(result["medical_restrictions"]) > 0

    def test_mascota_sana_sin_restricciones(self) -> None:
        """Mascota sana → lista de restricciones puede ser vacía o mínima."""
        state = _state_with_pet(conditions=[])
        result = nodo_3_apply_restrictions(state)
        assert isinstance(result["medical_restrictions"], list)


# ─── Nodo 4: check_safety_pre ─────────────────────────────────────────────────

class TestCheckSafetyPre:
    def test_alergias_se_preservan_en_state(self) -> None:
        """Las alergias del perfil se preservan en allergy_list del state."""
        state = _state_with_pet(allergies=["pollo", "trigo"])
        result = nodo_4_check_safety_pre(state)
        assert "pollo" in result["allergy_list"]
        assert "trigo" in result["allergy_list"]

    def test_sin_alergias_lista_vacia(self) -> None:
        """Sin alergias → allergy_list vacía."""
        state = _state_with_pet(allergies=[])
        result = nodo_4_check_safety_pre(state)
        assert result["allergy_list"] == []


# ─── Nodo 5: select_llm ───────────────────────────────────────────────────────

class TestSelectLLM:
    def test_free_tier_sin_condiciones_usa_llama(self) -> None:
        """FREE tier, 0 condiciones → llama-3.3-70b."""
        state = _state_with_pet(user_tier="FREE", conditions=[])
        result = nodo_5_select_llm(state)
        assert result["llm_model"] == "meta-llama/llama-3.3-70b-instruct:free"

    def test_sally_override_clinico_usa_claude(self) -> None:
        """5 condiciones médicas → claude-sonnet-4-5 (override REGLA 5)."""
        state = _state_with_pet(
            user_tier="FREE",
            conditions=["diabético", "hepático/hiperlipidemia", "gastritis",
                        "cistitis/enfermedad_urinaria", "hipotiroideo"],
        )
        result = nodo_5_select_llm(state)
        assert result["llm_model"] == "anthropic/claude-sonnet-4.5"

    def test_premium_tier_usa_claude(self) -> None:
        """PREMIUM tier → claude-sonnet-4-5."""
        state = _state_with_pet(user_tier="PREMIUM", conditions=[])
        result = nodo_5_select_llm(state)
        assert result["llm_model"] == "anthropic/claude-sonnet-4.5"


# ─── Nodo 7: validate_output ──────────────────────────────────────────────────

class TestValidateOutput:
    def _state_with_llm_response(
        self,
        ingredients: list[str],
        species: str = "perro",
    ) -> NutriVetState:
        content = json.dumps({
            "perfil_nutricional": {
                "rer_kcal": 396.0, "der_kcal": 534.0,
                "proteina_pct_ms": 28.0, "grasa_pct_ms": 12.0, "fibra_pct_ms": 5.0,
                "calcio_g_dia": 1.2, "fosforo_g_dia": 0.9, "sodio_mg_dia": 300,
                "omega3_mg_dia": 500, "racion_total_g_dia": 320.0, "kcal_verificadas": 530.0,
            },
            "ingredientes": [
                {"nombre": ing, "cantidad_g": 100, "kcal": 165, "proteina_g": 20, "grasa_g": 5,
                 "fuente": "animal", "frecuencia": "diario"}
                for ing in ingredients
            ],
            "porciones": {"total_g_dia": 320.0, "numero_comidas": 2, "g_por_comida": 160.0},
            "instrucciones_preparacion": {"metodo": "cocción", "pasos": ["Hervir ingredientes"]},
            "transicion_dieta": {"requiere_transicion": True, "duracion_dias": 10, "fases": []},
        })
        state = _state_with_pet(species=species)
        state["llm_response_content"] = content
        state["rer_kcal"] = 396.0
        state["der_kcal"] = 534.0
        state["bcs_phase"] = "mantenimiento"
        return state

    def test_plan_valida_output_post_llm_rechaza_toxicos(self) -> None:
        """Nodo 7 rechaza plan con ingrediente tóxico (REGLA 1 post-LLM)."""
        state = self._state_with_llm_response(
            ingredients=["pollo", "arroz", "uvas"],  # uvas tóxico para perros
            species="perro",
        )
        with pytest.raises(ValueError, match="tóxico"):
            nodo_7_validate_output(state)

    def test_plan_valido_sin_toxicos_pasa(self) -> None:
        """Plan sin ingredientes tóxicos → pasa validación."""
        state = self._state_with_llm_response(
            ingredients=["pollo", "arroz", "zanahoria"],
            species="perro",
        )
        result = nodo_7_validate_output(state)
        assert result.get("plan_content") is not None

    def test_json_invalido_levanta_error(self) -> None:
        """JSON inválido del LLM → ValueError."""
        state = _state_with_pet()
        state["llm_response_content"] = "esto no es JSON"
        state["rer_kcal"] = 396.0
        state["der_kcal"] = 534.0
        state["bcs_phase"] = "mantenimiento"
        with pytest.raises(ValueError):
            nodo_7_validate_output(state)


# ─── Nodo 9: determine_hitl ───────────────────────────────────────────────────

class TestDetermineHITL:
    def test_plan_sano_active_directo(self) -> None:
        """Mascota sana → requires_vet_review = False (REGLA 4)."""
        state = _state_with_pet(conditions=[])
        result = nodo_9_determine_hitl(state)
        assert result["requires_vet_review"] is False

    def test_plan_condicion_pending_vet(self) -> None:
        """Mascota con condición → requires_vet_review = True (REGLA 4)."""
        state = _state_with_pet(conditions=["diabético"])
        result = nodo_9_determine_hitl(state)
        assert result["requires_vet_review"] is True

    def test_plan_acumula_traces_en_state(self) -> None:
        """State preserva agent_traces acumulados."""
        state = _state_with_pet()
        state["agent_traces"] = [{"llm_model": "meta-llama/llama-3.3-70b-instruct:free", "latency_ms": 1200}]
        result = nodo_9_determine_hitl(state)
        assert len(result["agent_traces"]) == 1


# ─── Nodo 8: generate_substitutes ─────────────────────────────────────────────

class TestGenerateSubstitutes:
    def test_substitute_set_excluye_prohibidos(self) -> None:
        """substitute_set no incluye ingredientes de medical_restrictions."""
        state = _state_with_pet()
        state["medical_restrictions"] = ["fósforo", "sodio"]
        state["plan_content"] = {
            "ingredientes": ["pollo", "arroz", "fósforo", "zanahoria"],
        }
        result = nodo_8_generate_substitutes(state)
        sub_set = result["plan_content"]["substitute_set"]
        assert "fósforo" not in [s.lower() for s in sub_set]
        assert "pollo" in sub_set or "arroz" in sub_set

    def test_substitute_set_se_agrega_a_plan_content(self) -> None:
        """substitute_set queda almacenado en plan_content."""
        state = _state_with_pet()
        state["medical_restrictions"] = []
        state["plan_content"] = {"ingredientes": ["pollo", "arroz"]}
        result = nodo_8_generate_substitutes(state)
        assert "substitute_set" in result["plan_content"]
