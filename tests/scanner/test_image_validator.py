"""
Tests RED — ImageValidator (NUT-71 · Paso 2).

REGLA 7: solo acepta tabla nutricional o lista de ingredientes.
NUNCA logos, marcas o empaques frontales.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from backend.infrastructure.agent.nodes.image_validator import (
    IMAGE_TYPE_NUTRITION_TABLE,
    IMAGE_TYPE_INGREDIENT_LIST,
    IMAGE_TYPE_REJECTED,
    classify_image_type,
)


class TestImageValidator:
    """Tests del clasificador de tipo de imagen."""

    @pytest.mark.asyncio
    async def test_tabla_nutricional_aceptada(self) -> None:
        """Imagen de tabla nutricional → image_type = 'nutrition_table'."""
        with patch(
            "backend.infrastructure.agent.nodes.image_validator._call_vision_llm",
            new_callable=AsyncMock,
            return_value=IMAGE_TYPE_NUTRITION_TABLE,
        ):
            result = await classify_image_type(image_bytes=b"fake_image_bytes", mime_type="image/jpeg")
        assert result == IMAGE_TYPE_NUTRITION_TABLE

    @pytest.mark.asyncio
    async def test_ingredientes_aceptados(self) -> None:
        """Imagen de lista de ingredientes → image_type = 'ingredient_list'."""
        with patch(
            "backend.infrastructure.agent.nodes.image_validator._call_vision_llm",
            new_callable=AsyncMock,
            return_value=IMAGE_TYPE_INGREDIENT_LIST,
        ):
            result = await classify_image_type(image_bytes=b"fake_image_bytes", mime_type="image/jpeg")
        assert result == IMAGE_TYPE_INGREDIENT_LIST

    @pytest.mark.asyncio
    async def test_imagen_frontal_rechazada(self) -> None:
        """Imagen de logo/marca/empaque frontal → REJECTED (REGLA 7)."""
        with patch(
            "backend.infrastructure.agent.nodes.image_validator._call_vision_llm",
            new_callable=AsyncMock,
            return_value=IMAGE_TYPE_REJECTED,
        ):
            result = await classify_image_type(image_bytes=b"fake_image_bytes", mime_type="image/jpeg")
        assert result == IMAGE_TYPE_REJECTED

    @pytest.mark.asyncio
    async def test_imagen_ambigua_rechazada(self) -> None:
        """Imagen no reconocible → REJECTED por seguridad."""
        with patch(
            "backend.infrastructure.agent.nodes.image_validator._call_vision_llm",
            new_callable=AsyncMock,
            return_value=IMAGE_TYPE_REJECTED,
        ):
            result = await classify_image_type(image_bytes=b"fake_image_bytes", mime_type="image/jpeg")
        assert result == IMAGE_TYPE_REJECTED

    def test_constantes_son_strings_validos(self) -> None:
        """Las constantes de tipo deben ser strings no vacíos."""
        assert isinstance(IMAGE_TYPE_NUTRITION_TABLE, str) and len(IMAGE_TYPE_NUTRITION_TABLE) > 0
        assert isinstance(IMAGE_TYPE_INGREDIENT_LIST, str) and len(IMAGE_TYPE_INGREDIENT_LIST) > 0
        assert isinstance(IMAGE_TYPE_REJECTED, str) and len(IMAGE_TYPE_REJECTED) > 0

    def test_constantes_son_distintas(self) -> None:
        """Los tres tipos deben ser distintos entre sí."""
        assert IMAGE_TYPE_NUTRITION_TABLE != IMAGE_TYPE_INGREDIENT_LIST
        assert IMAGE_TYPE_NUTRITION_TABLE != IMAGE_TYPE_REJECTED
        assert IMAGE_TYPE_INGREDIENT_LIST != IMAGE_TYPE_REJECTED

    @pytest.mark.asyncio
    async def test_ocr_siempre_usa_gpt4o_para_clasificacion(self) -> None:
        """
        El clasificador usa gpt-4o (vision) — no cambia según tier (ADR-019).
        Verifica que _call_vision_llm recibe model='openai/gpt-4o'.
        """
        with patch(
            "backend.infrastructure.agent.nodes.image_validator._call_vision_llm",
            new_callable=AsyncMock,
            return_value=IMAGE_TYPE_NUTRITION_TABLE,
        ) as mock_llm:
            await classify_image_type(image_bytes=b"fake", mime_type="image/png")
            call_kwargs = mock_llm.call_args
            # El modelo usado debe ser gpt-4o
            assert call_kwargs is not None
            args, kwargs = call_kwargs
            model_arg = kwargs.get("model") or (args[0] if args else None)
            assert model_arg == "openai/gpt-4o"
