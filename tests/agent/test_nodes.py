"""
Tests RED — Nodos del Orquestador (NUT-62 · Paso 2).

Tests de: emergency_detector, intent_classifier, referral_node.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.infrastructure.agent.nodes.emergency_detector import (
    EMERGENCY_KEYWORDS,
    emergency_detector,
)
from backend.infrastructure.agent.nodes.referral_node import referral_node
from backend.infrastructure.agent.state import NutriVetState


# ─── Emergency Detector ───────────────────────────────────────────────────────

class TestEmergencyDetector:
    """Tests del nodo emergency_detector (determinístico, sin LLM)."""

    def _base_state(self, message: str) -> NutriVetState:
        return NutriVetState(
            user_id="user-1",
            pet_id="pet-1",
            user_tier="FREE",
            user_role="owner",
            message=message,
            agent_traces=[],
            conversation_history=[],
            medical_restrictions=[],
            allergy_list=[],
            requires_vet_review=False,
        )

    def test_keyword_convulsion_detecta_emergencia(self) -> None:
        """'convulsión' → intent = 'emergency'."""
        state = self._base_state("mi perro está convulsionando, qué hago")
        result = emergency_detector(state)
        assert result["intent"] == "emergency"

    def test_keyword_envenenado_detecta_emergencia(self) -> None:
        """'envenenado' → intent = 'emergency'."""
        state = self._base_state("creo que mi gato fue envenenado")
        result = emergency_detector(state)
        assert result["intent"] == "emergency"

    def test_mensaje_nutricional_no_es_emergencia(self) -> None:
        """Consulta nutricional normal → intent no cambia."""
        state = self._base_state("¿qué cantidad de pollo le doy a mi perro?")
        result = emergency_detector(state)
        assert result.get("intent") != "emergency"

    def test_mensaje_plan_no_es_emergencia(self) -> None:
        """Solicitud de plan → intent no cambia."""
        state = self._base_state("quiero un plan nutricional para mi gato")
        result = emergency_detector(state)
        assert result.get("intent") != "emergency"

    def test_emergency_keywords_es_frozenset(self) -> None:
        """EMERGENCY_KEYWORDS debe ser frozenset (inmutable)."""
        assert isinstance(EMERGENCY_KEYWORDS, frozenset)

    def test_emergency_keywords_no_esta_vacio(self) -> None:
        """EMERGENCY_KEYWORDS no debe estar vacío."""
        assert len(EMERGENCY_KEYWORDS) > 0

    def test_estado_se_preserva_en_emergencia(self) -> None:
        """Todos los campos del state se preservan al detectar emergencia."""
        state = self._base_state("mi perro está inconsciente")
        result = emergency_detector(state)
        assert result["user_id"] == "user-1"
        assert result["pet_id"] == "pet-1"
        assert result["intent"] == "emergency"

    def test_sangrado_detecta_emergencia(self) -> None:
        """'sangrado' → intent = 'emergency'."""
        state = self._base_state("mi perro tiene mucho sangrado en la pata")
        result = emergency_detector(state)
        assert result["intent"] == "emergency"


# ─── Referral Node ────────────────────────────────────────────────────────────

class TestReferralNode:
    """Tests del nodo referral_node (determinístico, sin LLM)."""

    def test_referral_genera_respuesta_estructurada(self) -> None:
        """intent=referral → respuesta con referencia al vet."""
        state = NutriVetState(
            intent="referral",
            message="mi perro tiene fiebre, qué medicamento le doy?",
            agent_traces=[],
            conversation_history=[],
            medical_restrictions=[],
            allergy_list=[],
            requires_vet_review=False,
        )
        result = referral_node(state)
        assert result.get("response") is not None
        assert len(result["response"]) > 0
        assert "veterinario" in result["response"].lower() or "vet" in result["response"].lower()

    def test_emergency_genera_respuesta_urgente(self) -> None:
        """intent=emergency → respuesta de emergencia más urgente."""
        state = NutriVetState(
            intent="emergency",
            message="mi perro está convulsionando",
            agent_traces=[],
            conversation_history=[],
            medical_restrictions=[],
            allergy_list=[],
            requires_vet_review=False,
        )
        result = referral_node(state)
        response = result.get("response", "")
        assert response is not None
        assert len(response) > 0
        # La respuesta de emergencia debe ser más urgente
        assert "urgente" in response.lower() or "emergencia" in response.lower() or "inmediato" in response.lower()

    def test_referral_no_llama_llm(self) -> None:
        """referral_node es determinístico — sin llamadas LLM."""
        # Si referral_node llamara LLM, necesitaría async. Al ser sync, verificamos que funciona.
        state = NutriVetState(
            intent="referral",
            message="¿qué pastillas le doy a mi gato?",
            agent_traces=[],
            conversation_history=[],
            medical_restrictions=[],
            allergy_list=[],
            requires_vet_review=False,
        )
        # Llamada sync exitosa = no hay LLM interno
        result = referral_node(state)
        assert result.get("response") is not None

    def test_emergencia_no_consume_cuota_agente(self) -> None:
        """Emergency no debe decrementar cuota conversacional del usuario."""
        state = NutriVetState(
            intent="emergency",
            message="mi perro colapsó",
            agent_traces=[],
            conversation_history=[],
            medical_restrictions=[],
            allergy_list=[],
            requires_vet_review=False,
        )
        result = referral_node(state)
        # El referral_node no modifica agent_traces (no es una consulta LLM)
        assert result.get("agent_traces", []) == []
