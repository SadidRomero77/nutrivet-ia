"""
Tests RED — Scanner Subgraph (NUT-73 · Paso 4).

5 nodos: image_validator → upload_to_r2 → ocr_with_gpt4o → evaluate_nutrition → persist_scan
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.infrastructure.agent.nodes.image_validator import (
    IMAGE_TYPE_NUTRITION_TABLE,
    IMAGE_TYPE_REJECTED,
)
from backend.infrastructure.agent.nodes.nutritional_evaluator import (
    SEMAPHORE_ROJO,
    SEMAPHORE_VERDE,
)
from backend.infrastructure.agent.state import NutriVetState


def _scan_state(
    species: str = "perro",
    conditions: list[str] | None = None,
    allergies: list[str] | None = None,
) -> NutriVetState:
    """State base para tests del scanner."""
    return NutriVetState(
        user_id=str(uuid.uuid4()),
        pet_id=str(uuid.uuid4()),
        user_tier="FREE",
        user_role="owner",
        message="analiza esta etiqueta",
        modality="concentrado",
        pet_profile={
            "pet_id": str(uuid.uuid4()),
            "species": species,
            "weight_kg": 10.0,
            "medical_conditions": conditions or [],
            "allergies": allergies or [],
            "owner_id": str(uuid.uuid4()),
        },
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
        scan_image_bytes=b"fake_image_data",
        scan_mime_type="image/jpeg",
    )


class TestScannerSubgraph:
    """Tests del subgrafo scanner (5 nodos)."""

    @pytest.mark.asyncio
    async def test_siempre_usa_gpt4o(self) -> None:
        """OCR siempre usa openai/gpt-4o — independiente del tier (ADR-019)."""
        from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph

        ocr_response = json.dumps({
            "image_type": IMAGE_TYPE_NUTRITION_TABLE,
            "ingredients": ["pollo", "arroz"],
            "nutritional_profile": {},
        })

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._classify_image",
                new_callable=AsyncMock,
                return_value=IMAGE_TYPE_NUTRITION_TABLE,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._upload_to_r2",
                new_callable=AsyncMock,
                return_value="https://r2.example.com/scan.jpg",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._run_ocr",
                new_callable=AsyncMock,
                return_value=ocr_response,
            ) as mock_ocr,
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._persist_scan",
                new_callable=AsyncMock,
                return_value=str(uuid.uuid4()),
            ),
        ):
            state = _scan_state()
            result = await run_scanner_subgraph(state)

            # Verificar que OCR se llamó con gpt-4o
            assert mock_ocr.called
            call_args = mock_ocr.call_args
            model_used = call_args.kwargs.get("model") or call_args.args[0]
            assert model_used == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_imagen_rechazada_no_llama_ocr(self) -> None:
        """Imagen rechazada (logo/marca) → no llama OCR (REGLA 7)."""
        from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._classify_image",
                new_callable=AsyncMock,
                return_value=IMAGE_TYPE_REJECTED,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._upload_to_r2",
                new_callable=AsyncMock,
                return_value="",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._run_ocr",
                new_callable=AsyncMock,
            ) as mock_ocr,
        ):
            state = _scan_state()
            result = await run_scanner_subgraph(state)

            mock_ocr.assert_not_called()
            assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_flujo_completo_tabla_nutricional_verde(self) -> None:
        """Flujo completo con tabla nutricional válida y sin tóxicos → VERDE."""
        from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph

        ocr_response = json.dumps({
            "image_type": IMAGE_TYPE_NUTRITION_TABLE,
            "ingredients": ["pollo", "arroz", "zanahoria"],
            "nutritional_profile": {"proteinas": 25, "grasas": 10},
        })

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._classify_image",
                new_callable=AsyncMock,
                return_value=IMAGE_TYPE_NUTRITION_TABLE,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._upload_to_r2",
                new_callable=AsyncMock,
                return_value="https://r2.example.com/scan.jpg",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._run_ocr",
                new_callable=AsyncMock,
                return_value=ocr_response,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._persist_scan",
                new_callable=AsyncMock,
                return_value=str(uuid.uuid4()),
            ),
        ):
            result = await run_scanner_subgraph(_scan_state())
            assert result.get("scan_semaphore") == SEMAPHORE_VERDE
            assert result.get("response") is not None

    @pytest.mark.asyncio
    async def test_flujo_completo_toxico_rojo(self) -> None:
        """Ingrediente tóxico detectado → semáforo ROJO."""
        from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph

        ocr_response = json.dumps({
            "image_type": IMAGE_TYPE_NUTRITION_TABLE,
            "ingredients": ["pollo", "cebolla"],  # cebolla tóxico para perro
            "nutritional_profile": {},
        })

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._classify_image",
                new_callable=AsyncMock,
                return_value=IMAGE_TYPE_NUTRITION_TABLE,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._upload_to_r2",
                new_callable=AsyncMock,
                return_value="https://r2.example.com/scan.jpg",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._run_ocr",
                new_callable=AsyncMock,
                return_value=ocr_response,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._persist_scan",
                new_callable=AsyncMock,
                return_value=str(uuid.uuid4()),
            ),
        ):
            result = await run_scanner_subgraph(_scan_state(species="perro"))
            assert result.get("scan_semaphore") == SEMAPHORE_ROJO

    @pytest.mark.asyncio
    async def test_disclaimer_en_resultado(self) -> None:
        """Resultado de scanner incluye disclaimer (REGLA 8)."""
        from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph

        ocr_response = json.dumps({
            "image_type": IMAGE_TYPE_NUTRITION_TABLE,
            "ingredients": ["pollo", "arroz"],
            "nutritional_profile": {},
        })

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._classify_image",
                new_callable=AsyncMock,
                return_value=IMAGE_TYPE_NUTRITION_TABLE,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._upload_to_r2",
                new_callable=AsyncMock,
                return_value="https://r2.example.com/scan.jpg",
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._run_ocr",
                new_callable=AsyncMock,
                return_value=ocr_response,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._persist_scan",
                new_callable=AsyncMock,
                return_value=str(uuid.uuid4()),
            ),
        ):
            result = await run_scanner_subgraph(_scan_state())
            response = result.get("response", "")
            assert "NutriVet.IA" in response or "nutricional" in response.lower()

    @pytest.mark.asyncio
    async def test_resultado_sin_brand_name(self) -> None:
        """ScanResult no incluye campo brand_name (principio de imparcialidad)."""
        from backend.presentation.schemas.scan_schemas import ScanResult
        scan_fields = ScanResult.model_fields
        assert "brand_name" not in scan_fields

    @pytest.mark.asyncio
    async def test_upload_ocurre_antes_de_ocr(self) -> None:
        """El upload a R2 ocurre antes de llamar al OCR (secuencia correcta)."""
        from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph

        call_order: list[str] = []

        async def mock_upload(*args, **kwargs) -> str:
            call_order.append("upload")
            return "https://r2.example.com/scan.jpg"

        async def mock_ocr(*args, **kwargs) -> str:
            call_order.append("ocr")
            return json.dumps({
                "image_type": IMAGE_TYPE_NUTRITION_TABLE,
                "ingredients": ["pollo"],
                "nutritional_profile": {},
            })

        with (
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._classify_image",
                new_callable=AsyncMock,
                return_value=IMAGE_TYPE_NUTRITION_TABLE,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._upload_to_r2",
                side_effect=mock_upload,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._run_ocr",
                side_effect=mock_ocr,
            ),
            patch(
                "backend.infrastructure.agent.subgraphs.scanner._persist_scan",
                new_callable=AsyncMock,
                return_value=str(uuid.uuid4()),
            ),
        ):
            await run_scanner_subgraph(_scan_state())

        assert call_order.index("upload") < call_order.index("ocr")
