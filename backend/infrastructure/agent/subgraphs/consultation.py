"""
ConsultationSubgraph — Subgrafo de consultas nutricionales conversacionales.

5 nodos:
  1. emergency_check   → detecta emergencias por keywords (sin LLM)
  2. freemium_gate     → verifica cuota Free (bypass para emergencias y tiers pagados)
  3. query_classifier  → clasifica: nutritional / medical / emergency
  4. nutritional_responder | referral_node → responde o remite según intent
  5. persist_conversation → guarda historial en DB

Constitution REGLA 8: disclaimer obligatorio en respuesta.
Constitution REGLA 9: consultas médicas → referral_node, nunca responde.
"""
from __future__ import annotations

import logging
from typing import AsyncGenerator

from backend.infrastructure.agent.nodes.emergency_detector import EMERGENCY_KEYWORDS
from backend.infrastructure.agent.state import NutriVetState

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "\n\n---\n"
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)

_REFERRAL_RESPONSE = (
    "Esta consulta requiere atención veterinaria profesional. "
    "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario. "
    "Te recomendamos contactar a tu veterinario de confianza."
)

_EMERGENCY_RESPONSE = (
    "¡EMERGENCIA VETERINARIA! "
    "Basado en tu descripción, tu mascota puede necesitar atención inmediata. "
    "Lleva a tu mascota al veterinario o clínica de emergencias más cercana de inmediato. "
    "NutriVet.IA — asesoría nutricional digital, no reemplaza atención médica veterinaria de urgencias."
)


# ── Funciones inyectables (para testabilidad sin LLM real ni DB) ──────────────

async def _classify(message: str, llm_client=None) -> str:
    """Clasifica el intent de la consulta."""
    from backend.infrastructure.agent.nodes.query_classifier import classify_query
    return await classify_query(message, llm_client=llm_client)


async def _check_gate(
    user_id: str,
    user_tier: str,
    intent: str,
    quota_repo=None,
) -> None:
    """Verifica la cuota freemium."""
    from backend.infrastructure.agent.nodes.freemium_gate import check_freemium_gate
    await check_freemium_gate(
        user_id=user_id,
        user_tier=user_tier,
        intent=intent,
        quota_repo=quota_repo,
    )


async def _stream_response(
    message: str,
    conversation_history: list[dict],
    user_tier: str,
    pet_profile: dict | None = None,
    llm_client=None,
) -> AsyncGenerator[str, None]:
    """Genera respuesta nutricional en streaming."""
    from backend.infrastructure.agent.nodes.nutritional_responder import stream_nutritional_response
    return stream_nutritional_response(
        message=message,
        conversation_history=conversation_history,
        user_tier=user_tier,
        pet_profile=pet_profile,
        llm_client=llm_client,
    )


async def _persist(
    pet_id: str,
    user_id: str,
    message: str,
    response: str,
    conversation_repo=None,
) -> None:
    """Persiste la conversación en DB."""
    if conversation_repo is None:
        logger.debug("conversation_repo no disponible — skip persist")
        return
    await conversation_repo.save(
        pet_id=pet_id,
        user_id=user_id,
        message=message,
        response=response,
    )


# ── Subgrafo principal ────────────────────────────────────────────────────────

async def run_consultation_subgraph(
    state: NutriVetState,
    llm_client=None,
    quota_repo=None,
    conversation_repo=None,
) -> dict:
    """
    Ejecuta el pipeline de consulta conversacional.

    Flujo:
      1. emergency_check — keywords determinísticos (sin LLM)
      2. Si emergencia → referral_node (bypass freemium_gate y LLM)
      3. freemium_gate — verifica cuota (solo tier FREE, no emergencias)
      4. query_classifier — LLM clasifica nutritional / medical
      5. nutritional_responder o referral_node
      6. persist_conversation

    Args:
        state: NutriVetState con message, user_id, pet_id, user_tier, etc.
        llm_client: Cliente LLM inyectable (para tests sin API key).
        quota_repo: Repositorio de cuota inyectable (para tests sin DB).
        conversation_repo: Repositorio de conversaciones inyectable.

    Returns:
        Dict con clave "response" (str) y estado actualizado.
    """
    message = state.get("message", "")
    user_id = state.get("user_id", "")
    pet_id = state.get("pet_id", "")
    user_tier = state.get("user_tier", "FREE")
    conversation_history = state.get("conversation_history", [])
    pet_profile = state.get("pet_profile")

    # Nodo 1: emergency_check — determinístico sin LLM
    message_lower = message.lower()
    is_emergency = any(kw in message_lower for kw in EMERGENCY_KEYWORDS)

    if is_emergency:
        # Bypass de freemium_gate y LLM — remisión directa
        response = _EMERGENCY_RESPONSE
        await _persist(
            pet_id=pet_id,
            user_id=user_id,
            message=message,
            response=response,
            conversation_repo=conversation_repo,
        )
        return {**state, "response": response}

    # Nodo 2: freemium_gate (no se llama en emergencias — ver bypass arriba)
    try:
        # Necesitamos el intent para el gate — pre-clasificamos
        # (en el subgrafo completo el gate usa el intent previo; aquí usamos "nutritional" por default)
        await _check_gate(
            user_id=user_id,
            user_tier=user_tier,
            intent="nutritional",  # intent provisional — el gate lo usa para emergencias
            quota_repo=quota_repo,
        )
    except Exception as gate_error:
        # FreemiumGateError u otra — bloquear con mensaje informativo
        response = str(gate_error)
        await _persist(
            pet_id=pet_id,
            user_id=user_id,
            message=message,
            response=response,
            conversation_repo=conversation_repo,
        )
        return {**state, "response": response}

    # Nodo 3: query_classifier — LLM
    intent = await _classify(message, llm_client=llm_client)

    # Nodo 4a: referral_node si es consulta médica
    if intent == "medical":
        response = _REFERRAL_RESPONSE
        await _persist(
            pet_id=pet_id,
            user_id=user_id,
            message=message,
            response=response,
            conversation_repo=conversation_repo,
        )
        return {**state, "response": response}

    # Nodo 4b: nutritional_responder — SSE streaming, colectar chunks
    gen = await _stream_response(
        message=message,
        conversation_history=conversation_history,
        user_tier=user_tier,
        pet_profile=pet_profile,
        llm_client=llm_client,
    )

    chunks: list[str] = []
    async for chunk in gen:
        chunks.append(chunk)

    response = "".join(chunks)

    # Añadir disclaimer si no está presente (Constitution REGLA 8)
    if "NutriVet" not in response and "nutricional digital" not in response.lower():
        response += _DISCLAIMER

    # Nodo 5: persist_conversation
    await _persist(
        pet_id=pet_id,
        user_id=user_id,
        message=message,
        response=response,
        conversation_repo=conversation_repo,
    )

    return {**state, "response": response}
