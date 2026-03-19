"""
ImageValidator — Clasifica el tipo de imagen enviada al scanner.

Constitution REGLA 7: solo acepta tabla nutricional o lista de ingredientes.
NUNCA logos, marcas o empaques frontales.

Usa gpt-4o (vision) para clasificación — siempre, sin importar el tier (ADR-019).
"""
from __future__ import annotations

import base64

from backend.infrastructure.llm.openrouter_client import OpenRouterClient

# Constantes de tipo de imagen
IMAGE_TYPE_NUTRITION_TABLE = "nutrition_table"
IMAGE_TYPE_INGREDIENT_LIST = "ingredient_list"
IMAGE_TYPE_REJECTED = "rejected"

_OCR_MODEL = "openai/gpt-4o"

_CLASSIFICATION_SYSTEM_PROMPT = """Eres un clasificador de imágenes para una app de nutrición veterinaria.
Analiza la imagen y determina qué tipo de contenido muestra.

Responde SOLO con uno de estos valores exactos:
- "nutrition_table" — si la imagen muestra una tabla nutricional con valores (proteínas, grasas, etc.)
- "ingredient_list" — si la imagen muestra una lista de ingredientes de un producto
- "rejected" — si la imagen muestra logo, marca, empaque frontal, foto de producto, o cualquier otra cosa

Responde ÚNICAMENTE con el valor, sin explicación."""


async def _call_vision_llm(
    model: str,
    image_base64: str,
    mime_type: str,
    llm_client: OpenRouterClient | None = None,
) -> str:
    """Llama al LLM de visión con la imagen codificada en base64."""
    client = llm_client or OpenRouterClient()

    # OpenRouter vision: la imagen se pasa como URL data: en el user prompt
    user_prompt = f"data:{mime_type};base64,{image_base64}"

    response = await client.generate(
        model=model,
        system_prompt=_CLASSIFICATION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
    )

    raw = (response.content or "").strip().lower().strip('"').strip("'")

    if raw == IMAGE_TYPE_NUTRITION_TABLE:
        return IMAGE_TYPE_NUTRITION_TABLE
    if raw == IMAGE_TYPE_INGREDIENT_LIST:
        return IMAGE_TYPE_INGREDIENT_LIST
    return IMAGE_TYPE_REJECTED


async def classify_image_type(
    image_bytes: bytes,
    mime_type: str,
    llm_client: OpenRouterClient | None = None,
) -> str:
    """
    Clasifica el tipo de imagen usando gpt-4o (vision).

    Args:
        image_bytes: Bytes de la imagen.
        mime_type: MIME type (image/jpeg, image/png, etc.).
        llm_client: Cliente LLM inyectable (para tests).

    Returns:
        IMAGE_TYPE_NUTRITION_TABLE | IMAGE_TYPE_INGREDIENT_LIST | IMAGE_TYPE_REJECTED
    """
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return await _call_vision_llm(
        model=_OCR_MODEL,
        image_base64=image_base64,
        mime_type=mime_type,
        llm_client=llm_client,
    )
