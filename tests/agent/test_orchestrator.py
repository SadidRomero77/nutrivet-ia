"""
Tests RED — Orquestador Completo (NUT-64 · Paso 4).

Tests de integración del grafo LangGraph orquestador.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.infrastructure.agent.nodes.emergency_detector import emergency_detector
from backend.infrastructure.agent.nodes.referral_node import referral_node
from backend.infrastructure.agent.orchestrator import build_orchestrator
from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.agent.subgraphs.consultation_stub import consultation_stub
from backend.infrastructure.agent.subgraphs.scanner_stub import scanner_stub


def _make_load_context_mock(with_pet: bool = True) -> AsyncMock:
    """Crea mock de load_context que retorna state con o sin pet_profile."""
    async def _load_context(state: NutriVetState) -> NutriVetState:
        if not with_pet:
            return {**state, "pet_profile": None, "active_plan": None, "error": "no encontrado"}
        return {
            **state,
            "pet_profile": {
                "pet_id": str(uuid.uuid4()),
                "species": "perro",
                "weight_kg": 10.08,
                "age_months": 96,
                "reproductive_status": "esterilizado",
                "activity_level": "sedentario",
                "bcs": 5,
                "medical_conditions": [],
                "allergies": [],
                "owner_id": str(uuid.uuid4()),
            },
            "active_plan": None,
        }
    return _load_context


def _make_intent_classifier_mock(intent: str) -> AsyncMock:
    """Crea mock de intent_classifier que devuelve el intent especificado."""
    async def _intent_classifier(state: NutriVetState) -> NutriVetState:
        return {**state, "intent": intent}
    return _intent_classifier


def _make_plan_generation_mock() -> AsyncMock:
    """Mock del plan generation subgraph."""
    async def _plan_generation(state: NutriVetState) -> NutriVetState:
        return {
            **state,
            "plan_id": str(uuid.uuid4()),
            "response": "Plan generado exitosamente.",
            "rer_kcal": 396.0,
            "der_kcal": 534.0,
        }
    return _plan_generation


def _build_test_orchestrator(intent: str = "consultation", with_pet: bool = True):
    """Construye orquestador de test con mocks inyectados."""
    return build_orchestrator(
        load_context_fn=_make_load_context_mock(with_pet=with_pet),
        intent_classifier_fn=_make_intent_classifier_mock(intent),
        plan_generation_fn=_make_plan_generation_mock(),
        consultation_fn=consultation_stub,
        scanner_fn=scanner_stub,
    )


# ─── Tests del Orquestador ────────────────────────────────────────────────────

class TestOrchestrator:
    """Tests de integración del grafo LangGraph."""

    def _initial_state(self, message: str = "quiero un plan") -> NutriVetState:
        return NutriVetState(
            user_id=str(uuid.uuid4()),
            pet_id=str(uuid.uuid4()),
            user_tier="FREE",
            user_role="owner",
            message=message,
            modality="natural",
            agent_traces=[],
            conversation_history=[],
            medical_restrictions=[],
            allergy_list=[],
            requires_vet_review=False,
        )

    @pytest.mark.asyncio
    async def test_orquestador_carga_contexto(self) -> None:
        """pet_profile y active_plan están en state tras load_context."""
        orchestrator = _build_test_orchestrator(intent="consultation")
        state = self._initial_state()
        result = await orchestrator.ainvoke(state)
        assert result.get("pet_profile") is not None

    @pytest.mark.asyncio
    async def test_routing_intent_consultation(self) -> None:
        """intent=consultation → stub de consulta retorna respuesta válida."""
        orchestrator = _build_test_orchestrator(intent="consultation")
        result = await orchestrator.ainvoke(self._initial_state())
        assert result.get("response") is not None
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_routing_intent_plan_generation(self) -> None:
        """intent=plan_generation → plan generation subgraph retorna plan_id."""
        orchestrator = _build_test_orchestrator(intent="plan_generation")
        result = await orchestrator.ainvoke(self._initial_state("quiero un plan nutricional"))
        assert result.get("plan_id") is not None
        assert result.get("response") is not None

    @pytest.mark.asyncio
    async def test_routing_intent_scanner(self) -> None:
        """intent=scanner → stub de scanner retorna respuesta válida."""
        orchestrator = _build_test_orchestrator(intent="scanner")
        result = await orchestrator.ainvoke(self._initial_state("analiza esta etiqueta"))
        assert result.get("response") is not None

    @pytest.mark.asyncio
    async def test_routing_intent_referral(self) -> None:
        """intent=referral → referral_node retorna mensaje estructurado."""
        orchestrator = _build_test_orchestrator(intent="referral")
        result = await orchestrator.ainvoke(self._initial_state("¿qué medicamento le doy?"))
        response = result.get("response", "")
        assert response is not None
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_emergency_bypass_llm(self) -> None:
        """Keyword de emergencia → intent=emergency sin pasar por intent_classifier."""
        # emergency_detector pone intent=emergency, routing va a referral_node directo
        orchestrator = _build_test_orchestrator(intent="consultation")  # classifier diría consultation
        state = self._initial_state(message="mi perro está convulsionando, ayuda")
        result = await orchestrator.ainvoke(state)
        # La respuesta debe ser de emergencia (no de consulta)
        response = result.get("response", "")
        assert response is not None
        # Intent final debe ser emergency
        assert result.get("intent") == "emergency"

    @pytest.mark.asyncio
    async def test_stub_consultation_retorna_respuesta(self) -> None:
        """Stub de consultation retorna respuesta válida (no None)."""
        state = NutriVetState(
            user_id="u1", pet_id="p1", user_tier="FREE", user_role="owner",
            message="¿cuántas calorías necesita mi perro?",
            agent_traces=[], conversation_history=[],
            medical_restrictions=[], allergy_list=[], requires_vet_review=False,
        )
        result = await consultation_stub(state)
        assert result.get("response") is not None
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_stub_scanner_retorna_respuesta(self) -> None:
        """Stub de scanner retorna respuesta válida (no None)."""
        state = NutriVetState(
            user_id="u1", pet_id="p1", user_tier="FREE", user_role="owner",
            message="analiza esta etiqueta",
            agent_traces=[], conversation_history=[],
            medical_restrictions=[], allergy_list=[], requires_vet_review=False,
        )
        result = await scanner_stub(state)
        assert result.get("response") is not None
        assert len(result["response"]) > 0
