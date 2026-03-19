"""
Tests RED — Consultation Subgraph (NUT-83 · Paso 4).

5 nodos: emergency_check → freemium_gate → query_classifier →
         nutritional_responder | referral_node → persist_conversation
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.infrastructure.agent.state import NutriVetState


def _chat_state(
    message: str = "¿qué proteínas necesita mi perro?",
    user_tier: str = "FREE",
    conditions: list[str] | None = None,
) -> NutriVetState:
    return NutriVetState(
        user_id=str(uuid.uuid4()),
        pet_id=str(uuid.uuid4()),
        user_tier=user_tier,
        user_role="owner",
        message=message,
        modality="natural",
        pet_profile={
            "pet_id": str(uuid.uuid4()),
            "species": "perro",
            "weight_kg": 10.0,
            "medical_conditions": conditions or [],
            "allergies": [],
            "owner_id": str(uuid.uuid4()),
        },
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
    )


class TestConversationSubgraph:

    @pytest.mark.asyncio
    async def test_flujo_nutricional_completo(self) -> None:
        """Consulta nutricional → respuesta con disclaimer en SSE."""
        from backend.infrastructure.agent.subgraphs.consultation import run_consultation_subgraph

        async def _fake_stream(*args, **kwargs):
            yield "El pollo es una excelente fuente de proteínas."
            yield "\n\n---\nNutriVet.IA es asesoría nutricional digital"

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._classify",
                new_callable=AsyncMock,
                return_value="nutritional",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._check_gate",
                new_callable=AsyncMock,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._stream_response",
                return_value=_fake_stream(),
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._persist",
                new_callable=AsyncMock,
            ),
        ):
            result = await run_consultation_subgraph(_chat_state())

        assert result.get("response") is not None
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_flujo_medico_remite_sin_llm_nutricion(self) -> None:
        """Consulta médica → referral_node, no llama nutritional_responder."""
        from backend.infrastructure.agent.subgraphs.consultation import run_consultation_subgraph

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._classify",
                new_callable=AsyncMock,
                return_value="medical",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._check_gate",
                new_callable=AsyncMock,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._stream_response",
            ) as mock_stream,
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._persist",
                new_callable=AsyncMock,
            ),
        ):
            result = await run_consultation_subgraph(
                _chat_state(message="mi perro vomitó sangre, qué hago")
            )

        mock_stream.assert_not_called()
        response = result.get("response", "")
        assert "veterinario" in response.lower() or "vet" in response.lower()

    @pytest.mark.asyncio
    async def test_disclaimer_presente_en_respuesta(self) -> None:
        """Toda respuesta incluye disclaimer (REGLA 8)."""
        from backend.infrastructure.agent.subgraphs.consultation import run_consultation_subgraph

        async def _fake_stream(*args, **kwargs):
            yield "El pollo es buena fuente de proteínas."

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._classify",
                new_callable=AsyncMock,
                return_value="nutritional",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._check_gate",
                new_callable=AsyncMock,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._stream_response",
                return_value=_fake_stream(),
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._persist",
                new_callable=AsyncMock,
            ),
        ):
            result = await run_consultation_subgraph(_chat_state())

        response = result.get("response", "")
        assert "NutriVet" in response or "nutricional digital" in response.lower()

    @pytest.mark.asyncio
    async def test_emergencia_no_llama_freemium_gate(self) -> None:
        """Emergencia → bypass del freemium gate sin llamarlo."""
        from backend.infrastructure.agent.subgraphs.consultation import run_consultation_subgraph

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._check_gate",
                new_callable=AsyncMock,
            ) as mock_gate,
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._classify",
                new_callable=AsyncMock,
                return_value="emergency",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._persist",
                new_callable=AsyncMock,
            ),
        ):
            result = await run_consultation_subgraph(
                _chat_state(message="mi perro está convulsionando")
            )

        mock_gate.assert_not_called()
        assert result.get("response") is not None

    @pytest.mark.asyncio
    async def test_historial_guardado_post_respuesta(self) -> None:
        """La conversación se persiste después de la respuesta."""
        from backend.infrastructure.agent.subgraphs.consultation import run_consultation_subgraph

        async def _fake_stream(*args, **kwargs):
            yield "Respuesta nutricional."

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._classify",
                new_callable=AsyncMock,
                return_value="nutritional",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._check_gate",
                new_callable=AsyncMock,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._stream_response",
                return_value=_fake_stream(),
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.consultation._persist",
                new_callable=AsyncMock,
            ) as mock_persist,
        ):
            await run_consultation_subgraph(_chat_state())

        mock_persist.assert_called_once()
