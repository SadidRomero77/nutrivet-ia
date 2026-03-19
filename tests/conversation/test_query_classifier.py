"""
Tests RED — QueryClassifier (NUT-81 · Paso 2).

Clasifica: NUTRITIONAL / MEDICAL / EMERGENCY
EMERGENCY es determinístico (EMERGENCY_KEYWORDS) — sin LLM.
Default si LLM falla: NUTRITIONAL (comportamiento seguro).
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from backend.infrastructure.agent.nodes.query_classifier import (
    INTENT_NUTRITIONAL,
    INTENT_MEDICAL,
    INTENT_EMERGENCY,
    classify_query,
)


class TestQueryClassifier:

    @pytest.mark.asyncio
    async def test_emergencia_detectada_antes_llm(self) -> None:
        """Keyword de emergencia → EMERGENCY sin llamar LLM."""
        with patch(
            "backend.infrastructure.agent.nodes.query_classifier._call_classifier_llm",
            new_callable=AsyncMock,
        ) as mock_llm:
            result = await classify_query("mi perro está convulsionando")
        assert result == INTENT_EMERGENCY
        mock_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_consulta_nutricional_respondida(self) -> None:
        """Consulta nutricional → NUTRITIONAL."""
        with patch(
            "backend.infrastructure.agent.nodes.query_classifier._call_classifier_llm",
            new_callable=AsyncMock,
            return_value=INTENT_NUTRITIONAL,
        ):
            result = await classify_query("¿cuántas proteínas necesita mi perro al día?")
        assert result == INTENT_NUTRITIONAL

    @pytest.mark.asyncio
    async def test_consulta_medica_remite_vet(self) -> None:
        """Consulta médica (síntoma) → MEDICAL."""
        with patch(
            "backend.infrastructure.agent.nodes.query_classifier._call_classifier_llm",
            new_callable=AsyncMock,
            return_value=INTENT_MEDICAL,
        ):
            result = await classify_query("mi perro vomitó tres veces hoy")
        assert result == INTENT_MEDICAL

    @pytest.mark.asyncio
    async def test_consulta_medicamentos_medica(self) -> None:
        """Consulta sobre medicamentos → MEDICAL."""
        with patch(
            "backend.infrastructure.agent.nodes.query_classifier._call_classifier_llm",
            new_callable=AsyncMock,
            return_value=INTENT_MEDICAL,
        ):
            result = await classify_query("¿qué dosis de antibiótico le doy a mi gato?")
        assert result == INTENT_MEDICAL

    @pytest.mark.asyncio
    async def test_default_nutricional_si_llm_falla(self) -> None:
        """Si el LLM falla → NUTRITIONAL por defecto (comportamiento seguro)."""
        with patch(
            "backend.infrastructure.agent.nodes.query_classifier._call_classifier_llm",
            new_callable=AsyncMock,
            side_effect=Exception("LLM timeout"),
        ):
            result = await classify_query("¿qué le doy de comer?")
        assert result == INTENT_NUTRITIONAL

    def test_constantes_son_strings_distintos(self) -> None:
        """Los tres intents son strings distintos."""
        assert INTENT_NUTRITIONAL != INTENT_MEDICAL
        assert INTENT_NUTRITIONAL != INTENT_EMERGENCY
        assert INTENT_MEDICAL != INTENT_EMERGENCY

    @pytest.mark.asyncio
    async def test_consulta_diagnostico_medica(self) -> None:
        """Consulta sobre diagnóstico → MEDICAL."""
        with patch(
            "backend.infrastructure.agent.nodes.query_classifier._call_classifier_llm",
            new_callable=AsyncMock,
            return_value=INTENT_MEDICAL,
        ):
            result = await classify_query("creo que mi perro tiene una infección urinaria")
        assert result == INTENT_MEDICAL
