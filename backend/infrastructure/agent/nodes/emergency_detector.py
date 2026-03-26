"""
EmergencyDetector — Nodo determinístico de detección de emergencias.

Regla: sin LLM, < 1ms, keywords hard-coded.
Si detecta emergencia → intent = "emergency" y bypass del intent_classifier.

Constitution REGLA 9: ante emergencia médica → remite al vet, nunca responde.
"""
from __future__ import annotations

from backend.infrastructure.agent.state import NutriVetState

# Keywords de emergencia — hard-coded, sin LLM (Constitution REGLA 9)
# NUNCA modificar sin validación veterinaria de Lady Carolina Castañeda (MV).
EMERGENCY_KEYWORDS: frozenset[str] = frozenset({
    # Neurológico
    "convulsión", "convulsiones", "convulsionando",
    "desmayo", "desmayado", "desmayándose",
    "pérdida de conciencia", "inconsciente", "no despierta",
    "crisis epiléptica", "crisis", "ataque",
    "parálisis", "no puede caminar",
    # Respiratorio — crítico
    "no respira", "sin respiración", "respiración dificultosa",
    "dificultad respiratoria", "no puede respirar",
    "ahogando", "asfixia", "asfixiando",
    # Cardiovascular / circulatorio
    "sangrado", "hemorragia", "vómito con sangre", "diarrea con sangre",
    "colapso", "colapsó", "colapsando",
    # Intoxicación / envenenamiento
    "veneno", "envenenado", "envenenó", "intoxicado", "intoxicación",
    "ingirió chocolate", "comió chocolate",
    "ingirió uva", "comió uva", "ingirió uvas", "comió uvas",
    "ingirió cebolla", "comió cebolla",
    "ingirió ajo", "comió ajo",
    "ingirió xilitol", "ingirió plantas tóxicas",
    "se envenenó", "posible intoxicación",
    # Trauma
    "atropellado", "accidente", "trauma",
    # Estado general grave
    "muriéndose", "urgente", "emergencia",
    "no come hace días", "no bebe hace días",
    "sangre",
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
