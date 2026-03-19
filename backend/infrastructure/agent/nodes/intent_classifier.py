"""
IntentClassifier — Nodo LLM que clasifica la intención del mensaje.

Intents válidos: plan_generation | consultation | scanner | referral | emergency

Constitution REGLA 9: Si el mensaje es sobre síntomas/diagnósticos/medicamentos
→ clasificar como "referral", no como "consultation".
"""
from __future__ import annotations

import json

from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.llm.openrouter_client import OpenRouterClient

_SYSTEM_PROMPT = """Eres un clasificador de intenciones para una app de nutrición veterinaria.
Clasifica el mensaje del usuario en exactamente uno de estos intents:
- plan_generation: El usuario quiere crear o actualizar un plan nutricional para su mascota.
- consultation: El usuario hace una pregunta nutricional (alimentos, porciones, ingredientes).
- scanner: El usuario quiere escanear/analizar la etiqueta de un alimento o concentrado.
- referral: El usuario pregunta sobre síntomas, enfermedades, medicamentos, diagnósticos — debe ser referido al vet.
- emergency: Situación de emergencia médica o peligro inmediato.

Responde SOLO con JSON: {"intent": "<valor>"}"""


async def intent_classifier(
    state: NutriVetState,
    llm_client: OpenRouterClient | None = None,
) -> NutriVetState:
    """
    Nodo LLM: clasifica la intención del mensaje del usuario.

    Usa el modelo Free tier (llama-3.3-70b) para clasificación — no requiere
    contexto clínico completo, solo semántica del mensaje.
    """
    client = llm_client or OpenRouterClient()
    message = state.get("message", "")

    response = await client.generate(
        model="meta-llama/llama-3.3-70b",
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=message,
        temperature=0.0,
    )

    try:
        parsed = json.loads(response.content)
        intent = parsed.get("intent", "consultation")
    except (json.JSONDecodeError, AttributeError):
        intent = "consultation"

    valid_intents = {"plan_generation", "consultation", "scanner", "referral", "emergency"}
    if intent not in valid_intents:
        intent = "consultation"

    return {**state, "intent": intent}
