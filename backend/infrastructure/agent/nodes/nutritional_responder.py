"""
NutritionalResponder — Nodo de respuesta nutricional con streaming SSE.

- Responde SOLO consultas nutricionales (no médicas, no emergencias).
- Historial: últimos 10 mensajes para contexto.
- Disclaimer obligatorio en el último chunk (Constitution REGLA 8).
- Usa LLM via OpenRouter según tier del usuario.

Constitution REGLA 8: disclaimer en cada respuesta.
Constitution REGLA 9: no responde consultas médicas.
"""
from __future__ import annotations

import logging
import os
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "\n\n---\n"
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)

_SYSTEM_PROMPT = (
    "Eres NutriVet.IA, un asistente de nutrición veterinaria especializado. "
    "Respondes ÚNICAMENTE consultas sobre alimentación, nutrición y dieta de mascotas. "
    "Ante cualquier síntoma, medicamento o diagnóstico médico, indica al usuario "
    "que consulte a su veterinario. Responde en español."
)


def _select_model(user_tier: str) -> str:
    """Selecciona el modelo LLM según el tier del usuario."""
    tier = user_tier.upper()
    if tier in ("PREMIUM", "VET"):
        return "anthropic/claude-sonnet-4-5"
    if tier == "BASICO":
        return "openai/gpt-4o-mini"
    return "meta-llama/llama-3.3-70b-instruct"


async def stream_nutritional_response(
    message: str,
    conversation_history: list[dict],
    user_tier: str,
    pet_profile: dict | None = None,
    llm_client=None,
) -> AsyncGenerator[str, None]:
    """
    Genera respuesta nutricional en streaming (SSE).

    Incluye disclaimer obligatorio en el último chunk.
    Usa historial de conversación (últimos 10 mensajes).

    Args:
        message: Mensaje actual del usuario.
        conversation_history: Historial previo de la conversación.
        user_tier: Tier del usuario para LLM routing.
        pet_profile: Perfil de la mascota para contexto (opcional).
        llm_client: Cliente LLM inyectable (para tests).

    Yields:
        Chunks de texto incluyendo disclaimer al final.
    """
    import httpx

    model = _select_model(user_tier)
    api_key = os.getenv("OPENROUTER_API_KEY", "")

    # Contexto de mascota si está disponible
    system = _SYSTEM_PROMPT
    if pet_profile:
        species = pet_profile.get("species", "mascota")
        weight = pet_profile.get("weight_kg", "?")
        conditions = pet_profile.get("medical_conditions", [])
        system += (
            f"\n\nContexto de la mascota: especie={species}, peso={weight}kg"
            + (f", condiciones médicas={conditions}" if conditions else "")
        )

    # Construir mensajes con historial (últimos 10)
    history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
    }

    full_response = ""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://nutrivet.ia",
                "X-Title": "NutriVet.IA",
            },
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                import json
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        full_response += delta
                        yield delta
                except (KeyError, json.JSONDecodeError):
                    continue

    # Disclaimer obligatorio al final (Constitution REGLA 8)
    yield _DISCLAIMER
