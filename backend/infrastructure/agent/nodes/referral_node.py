"""
ReferralNode — Nodo determinístico para remisión al veterinario.

Constitution REGLA 9: El agente NUNCA responde consultas médicas (síntomas,
medicamentos, diagnósticos). Las remite al vet con mensaje estructurado.
"""
from __future__ import annotations

from backend.infrastructure.agent.state import NutriVetState

_REFERRAL_TEMPLATE = (
    "⚕️ **Esta consulta requiere atención veterinaria profesional.**\n\n"
    "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario.\n\n"
    "**Te recomendamos:**\n"
    "• Contactar a tu veterinario de confianza.\n"
    "• Si es urgente, dirigirte al centro veterinario más cercano.\n\n"
    "_Para consultas sobre nutrición, ingredientes o planes alimentarios, ¡con gusto te ayudo!_"
)

_EMERGENCY_TEMPLATE = (
    "🚨 **¡EMERGENCIA VETERINARIA!**\n\n"
    "Basado en tu descripción, tu mascota puede necesitar atención inmediata.\n\n"
    "**Acción urgente:**\n"
    "• Lleva a tu mascota al veterinario o clínica de emergencias MÁS CERCANA de inmediato.\n"
    "• No administres medicamentos sin indicación veterinaria.\n\n"
    "NutriVet.IA — asesoría nutricional digital, no reemplaza atención médica veterinaria de urgencias."
)


def referral_node(state: NutriVetState) -> NutriVetState:
    """
    Nodo determinístico: genera mensaje de remisión estructurado.

    No llama LLM. Retorna respuesta fija según intent (referral vs emergency).
    """
    intent = state.get("intent", "referral")

    if intent == "emergency":
        response = _EMERGENCY_TEMPLATE
    else:
        response = _REFERRAL_TEMPLATE

    return {**state, "response": response}
