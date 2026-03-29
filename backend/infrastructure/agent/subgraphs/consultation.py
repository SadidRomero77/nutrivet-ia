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

Streaming:
  run_consultation_subgraph_streaming() → AsyncGenerator[str, None] para SSE real.
  run_consultation_subgraph()            → str completo (tests, plan generation pipeline).
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
# Marker token único en el disclaimer — usado para verificar presencia (REGLA 8).
# No aparece en respuestas normales del LLM, evita falsos positivos.
_DISCLAIMER_MARKER = "asesoría nutricional digital"

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


# ── Lógica compartida de pre-procesamiento ────────────────────────────────────

async def _run_pre_llm_pipeline(
    state: NutriVetState,
    llm_client=None,
    quota_repo=None,
    conversation_repo=None,
) -> tuple[str | None, str]:
    """
    Ejecuta los nodos determinísticos previos al LLM.

    Returns:
        (short_circuit_response, intent)
        Si short_circuit_response es no-None, se debe retornar esa respuesta directamente
        sin llamar al LLM (emergencia, gate bloqueado, consulta médica).
        intent es el clasificador ("nutritional", "medical", "emergency").
    """
    message = state.get("message", "")
    user_id = state.get("user_id", "")
    pet_id = state.get("pet_id", "")
    user_tier = state.get("user_tier", "FREE")

    # Nodo 1: emergency_check — determinístico sin LLM
    message_lower = message.lower()
    is_emergency = any(kw in message_lower for kw in EMERGENCY_KEYWORDS)

    if is_emergency:
        await _persist(
            pet_id=pet_id, user_id=user_id,
            message=message, response=_EMERGENCY_RESPONSE,
            conversation_repo=conversation_repo,
        )
        return _EMERGENCY_RESPONSE, "emergency"

    # Nodo 2: freemium_gate
    # El intent real se determina DESPUÉS de clasificar, pero el gate necesita
    # un intent para verificar si es emergencia (bypass). Usamos el intent
    # clasificado a continuación para mayor precisión.
    intent = await _classify(message, llm_client=llm_client)

    try:
        await _check_gate(
            user_id=user_id,
            user_tier=user_tier,
            intent=intent,
            quota_repo=quota_repo,
        )
    except Exception as gate_error:
        response = str(gate_error)
        await _persist(
            pet_id=pet_id, user_id=user_id,
            message=message, response=response,
            conversation_repo=conversation_repo,
        )
        return response, intent

    # Nodo 3: referral si es consulta médica
    if intent == "medical":
        await _persist(
            pet_id=pet_id, user_id=user_id,
            message=message, response=_REFERRAL_RESPONSE,
            conversation_repo=conversation_repo,
        )
        return _REFERRAL_RESPONSE, intent

    return None, intent


# ── Subgrafo principal — modo streaming (para SSE real en el router) ──────────

async def run_consultation_subgraph_streaming(
    state: NutriVetState,
    llm_client=None,
    quota_repo=None,
    conversation_repo=None,
) -> AsyncGenerator[str, None]:
    """
    Ejecuta el pipeline de consulta conversacional en modo streaming real.

    Yields chunks de texto progresivamente, incluyendo disclaimer al final.
    Usado por agent_router.py para SSE real (Constitution REGLA 8).

    Args:
        state: NutriVetState con message, user_id, pet_id, user_tier, etc.
        llm_client: Cliente LLM inyectable (para tests sin API key).
        quota_repo: Repositorio de cuota inyectable.
        conversation_repo: Repositorio de conversaciones inyectable.

    Yields:
        Chunks de texto del LLM + disclaimer final.
    """
    return _streaming_generator(
        state=state,
        llm_client=llm_client,
        quota_repo=quota_repo,
        conversation_repo=conversation_repo,
    )


async def _streaming_generator(
    state: NutriVetState,
    llm_client=None,
    quota_repo=None,
    conversation_repo=None,
) -> AsyncGenerator[str, None]:
    """Generador interno del streaming real."""
    message = state.get("message", "")
    user_id = state.get("user_id", "")
    pet_id = state.get("pet_id", "")
    conversation_history = state.get("conversation_history", [])
    user_tier = state.get("user_tier", "FREE")
    pet_profile = state.get("pet_profile")
    active_plan = state.get("active_plan")
    plan_history = state.get("plan_history", [])

    # Nodos determinísticos (sin LLM) — si hay short-circuit, yield y termina
    short_circuit, intent = await _run_pre_llm_pipeline(
        state=state,
        llm_client=llm_client,
        quota_repo=quota_repo,
        conversation_repo=conversation_repo,
    )

    if short_circuit is not None:
        yield short_circuit
        return

    # Nodo 4b: nutritional_responder — streaming real chunk-a-chunk
    from backend.infrastructure.agent.nodes.nutritional_responder import stream_nutritional_response

    full_response = ""
    async for chunk in stream_nutritional_response(
        message=message,
        conversation_history=conversation_history,
        user_tier=user_tier,
        pet_profile=pet_profile,
        active_plan=active_plan,
        plan_history=plan_history,
        llm_client=llm_client,
    ):
        full_response += chunk
        yield chunk

    # Verificar disclaimer (Constitution REGLA 8) — el nutritional_responder
    # ya lo incluye al final, pero verificamos con marker específico.
    if _DISCLAIMER_MARKER not in full_response:
        yield _DISCLAIMER
        full_response += _DISCLAIMER

    # Nodo 5: persist_conversation (después de completar el stream)
    await _persist(
        pet_id=pet_id,
        user_id=user_id,
        message=message,
        response=full_response,
        conversation_repo=conversation_repo,
    )


# ── Subgrafo principal — modo batch (para tests y compatibilidad) ─────────────

async def run_consultation_subgraph(
    state: NutriVetState,
    llm_client=None,
    quota_repo=None,
    conversation_repo=None,
) -> dict:
    """
    Ejecuta el pipeline de consulta conversacional en modo batch.

    Acumula todos los chunks y retorna el state con "response" completo.
    Usar en tests y en contextos donde no se necesita streaming real.

    Returns:
        Dict con clave "response" (str) y estado actualizado.
    """
    message = state.get("message", "")
    user_id = state.get("user_id", "")
    pet_id = state.get("pet_id", "")
    conversation_history = state.get("conversation_history", [])
    user_tier = state.get("user_tier", "FREE")
    pet_profile = state.get("pet_profile")
    active_plan = state.get("active_plan")
    plan_history = state.get("plan_history", [])

    # Nodos determinísticos
    short_circuit, intent = await _run_pre_llm_pipeline(
        state=state,
        llm_client=llm_client,
        quota_repo=quota_repo,
        conversation_repo=conversation_repo,
    )

    if short_circuit is not None:
        return {**state, "response": short_circuit}

    # Nodo 4b: nutritional_responder — acumular chunks
    from backend.infrastructure.agent.nodes.nutritional_responder import stream_nutritional_response

    chunks: list[str] = []
    async for chunk in stream_nutritional_response(
        message=message,
        conversation_history=conversation_history,
        user_tier=user_tier,
        pet_profile=pet_profile,
        active_plan=active_plan,
        plan_history=plan_history,
        llm_client=llm_client,
    ):
        chunks.append(chunk)

    response = "".join(chunks)

    # Verificar disclaimer con marker específico (Constitution REGLA 8)
    if _DISCLAIMER_MARKER not in response:
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
