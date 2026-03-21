"""
NutritionalResponder — Nodo de respuesta nutricional con streaming SSE.

Responde SOLO consultas nutricionales (no médicas, no emergencias).
Historial: últimos 12 mensajes para contexto.
Disclaimer obligatorio en el último chunk (Constitution REGLA 8).
Usa prompts expertos con conocimiento NRC/AAFCO embebido y contexto completo de la mascota.

Constitution REGLA 8: disclaimer en cada respuesta.
Constitution REGLA 9: no responde consultas médicas.
Constitution REGLA 6: sin PII del propietario en prompts.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncGenerator

from backend.infrastructure.agent.prompts.conversation_prompts import (
    build_conversation_system_prompt,
    select_conversation_model,
)

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "\n\n---\n"
    "*NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario.*"
)

# Temperatura baja para respuestas clínicas precisas y consistentes
_CONVERSATION_TEMPERATURE = 0.4

# Máximo de mensajes del historial a incluir (contexto)
_MAX_HISTORY_MESSAGES = 12


async def stream_nutritional_response(
    message: str,
    conversation_history: list[dict],
    user_tier: str,
    pet_profile: dict[str, Any] | None = None,
    active_plan: dict[str, Any] | None = None,
    llm_client=None,
) -> AsyncGenerator[str, None]:
    """
    Genera respuesta nutricional en streaming (SSE).

    Usa prompts expertos con 6 bloques:
    - Identidad y límites de competencia
    - Conocimiento clínico NRC/AAFCO embebido
    - Contexto completo de la mascota (13 campos) + plan activo
    - Clasificación nutricional vs médica con respuestas apropiadas
    - Manejo de escenarios difíciles (mitos, emergencias, tóxicos)
    - Guardarraíles anti-alucinación

    Incluye disclaimer obligatorio en el último chunk.

    Args:
        message: Mensaje actual del usuario.
        conversation_history: Historial previo de la conversación.
        user_tier: Tier del usuario para LLM routing y tono ("FREE", "BASICO", "PREMIUM", "VET").
        pet_profile: PetProfile serializado con todos los 13 campos (opcional).
        active_plan: NutritionPlan activo serializado con content (opcional).
        llm_client: Cliente LLM inyectable (para tests).

    Yields:
        Chunks de texto incluyendo disclaimer al final.
    """
    import httpx

    # Determinar si la mascota tiene condiciones médicas (para routing)
    has_conditions = bool(
        pet_profile and pet_profile.get("medical_conditions")
    )

    # Seleccionar modelo según tier + contexto clínico
    model = select_conversation_model(user_tier=user_tier, has_conditions=has_conditions)

    api_key = os.getenv("OPENROUTER_API_KEY", "")

    # Construir system prompt experto con contexto completo de la mascota
    system_prompt = build_conversation_system_prompt(
        pet_profile=pet_profile,
        active_plan=active_plan,
        user_tier=user_tier,
    )

    # Construir mensajes con historial (últimos N mensajes)
    history = (
        conversation_history[-_MAX_HISTORY_MESSAGES:]
        if len(conversation_history) > _MAX_HISTORY_MESSAGES
        else conversation_history
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": _CONVERSATION_TEMPERATURE,
        "max_tokens": 2000,
    }

    logger.info(
        "streaming_nutritional_response",
        extra={
            "model": model,
            "user_tier": user_tier,
            "has_conditions": has_conditions,
            "has_pet": pet_profile is not None,
            "has_plan": active_plan is not None,
            "history_len": len(history),
        },
    )

    full_response = ""
    async with httpx.AsyncClient(timeout=90.0) as client:
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
                try:
                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"].get("content", "")
                    if delta:
                        full_response += delta
                        yield delta
                except (KeyError, json.JSONDecodeError):
                    continue

    logger.info(
        "nutritional_response_completed",
        extra={
            "model": model,
            "response_len": len(full_response),
        },
    )

    # Disclaimer obligatorio al final (Constitution REGLA 8)
    yield _DISCLAIMER
