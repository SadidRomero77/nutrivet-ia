"""
EmergencyDetector — Nodo determinístico de detección de emergencias.

Regla: sin LLM, < 1ms, keywords hard-coded.
Si detecta emergencia → intent = "emergency" y bypass del intent_classifier.

Constitution REGLA 9: ante emergencia médica → remite al vet, nunca responde.
"""
from __future__ import annotations

from backend.infrastructure.agent.state import NutriVetState

# Keywords de emergencia — hard-coded, sin LLM (Constitution REGLA 9)
EMERGENCY_KEYWORDS: frozenset[str] = frozenset({
    "convulsión", "convulsiones", "convulsionando",
    "desmayo", "desmayado", "desmayándose",
    "no respira", "sin respiración", "respiración dificultosa",
    "sangrado", "hemorragia", "sangre",
    "veneno", "envenenado", "intoxicado", "intoxicación",
    "atropellado", "accidente", "trauma",
    "no come hace días", "no bebe hace días",
    "colapso", "colapsó", "colapsando",
    "urgente", "emergencia", "muriéndose",
    "inconsciente", "no despierta",
    "vómito con sangre", "diarrea con sangre",
    "no puede caminar", "parálisis",
    "crisis", "ataque",
})


def emergency_detector(state: NutriVetState) -> NutriVetState:
    """
    Nodo determinístico: detecta emergencias por keyword matching.

    No llama LLM. O(n) sobre longitud del mensaje — < 1ms garantizado.
    Si hay keyword → intent = "emergency".
    Si no → deja intent sin cambio (se clasifica en intent_classifier).
    """
    message = (state.get("message") or "").lower()

    detected = any(kw in message for kw in EMERGENCY_KEYWORDS)

    if detected:
        return {**state, "intent": "emergency"}

    return state
