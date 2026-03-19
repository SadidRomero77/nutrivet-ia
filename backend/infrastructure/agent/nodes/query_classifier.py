"""
QueryClassifier — Nodo de clasificación de intención de consulta.

Clasifica: NUTRITIONAL / MEDICAL / EMERGENCY
- EMERGENCY: determinístico por keywords (sin LLM) — < 1ms
- MEDICAL / NUTRITIONAL: LLM (llama-3.3-70b via OpenRouter)
- Default si LLM falla: NUTRITIONAL (comportamiento seguro)

Constitution REGLA 9: consultas médicas → remite al vet, nunca responde.
"""
from __future__ import annotations

import logging

from backend.infrastructure.agent.nodes.emergency_detector import EMERGENCY_KEYWORDS

logger = logging.getLogger(__name__)

# Constantes de intención
INTENT_NUTRITIONAL = "nutritional"
INTENT_MEDICAL = "medical"
INTENT_EMERGENCY = "emergency"

_CLASSIFIER_PROMPT = """Eres un clasificador de consultas veterinarias. Clasifica la siguiente consulta en UNA de estas categorías:

- NUTRITIONAL: preguntas sobre alimentación, nutrición, dieta, ingredientes, porciones, suplementos
- MEDICAL: preguntas sobre síntomas, enfermedades, medicamentos, diagnósticos, tratamientos

Responde SOLO con la palabra: NUTRITIONAL o MEDICAL

Consulta: {message}"""


async def _call_classifier_llm(message: str, llm_client=None) -> str:
    """
    Llama al LLM para clasificar la consulta.

    Usa llama-3.3-70b (tier Free) — consulta de clasificación, no de generación.
    Retorna INTENT_NUTRITIONAL o INTENT_MEDICAL.
    Raises: Exception si el LLM falla (manejado en classify_query).
    """
    import os

    import httpx

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = "meta-llama/llama-3.3-70b-instruct"

    prompt = _CLASSIFIER_PROMPT.format(message=message)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 10,
        "temperature": 0.0,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://nutrivet.ia",
                "X-Title": "NutriVet.IA",
            },
            json=payload,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip().upper()

    if "MEDICAL" in content:
        return INTENT_MEDICAL
    return INTENT_NUTRITIONAL


async def classify_query(message: str, llm_client=None) -> str:
    """
    Clasifica la consulta del usuario en uno de tres intents.

    Orden de evaluación:
    1. Keywords de emergencia → EMERGENCY (determinístico, sin LLM)
    2. LLM classifier → MEDICAL o NUTRITIONAL
    3. Si LLM falla → NUTRITIONAL (default seguro)

    Args:
        message: Mensaje del usuario en lenguaje natural.
        llm_client: Cliente LLM inyectable (para tests).

    Returns:
        INTENT_NUTRITIONAL | INTENT_MEDICAL | INTENT_EMERGENCY
    """
    message_lower = message.lower()

    # Paso 1: detección determinística de emergencia (sin LLM)
    if any(kw in message_lower for kw in EMERGENCY_KEYWORDS):
        return INTENT_EMERGENCY

    # Paso 2: clasificación via LLM
    try:
        return await _call_classifier_llm(message, llm_client=llm_client)
    except Exception:
        logger.warning("LLM classifier falló — usando NUTRITIONAL como default seguro")
        return INTENT_NUTRITIONAL
