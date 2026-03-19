"""
FreemiumGate — Nodo de control de cuota para tier Free.

Reglas:
- Free tier: 3 preguntas/día × 3 días = 9 total
- Emergencias: bypass incondicional (nunca bloquear)
- Tiers pagados (BASICO, PREMIUM, VET): bypass incondicional
- El incremento de cuota ocurre ANTES de llamar al LLM (atómico)

Constitution REGLA 9: emergencias no se bloquean bajo ninguna circunstancia.
"""
from __future__ import annotations

DAILY_LIMIT = 3
TOTAL_LIMIT = 9

FREE_TIER = "FREE"
_PAID_TIERS = {"BASICO", "PREMIUM", "VET"}


class FreemiumGateError(Exception):
    """
    Excepción levantada cuando el usuario Free supera su cuota.

    El mensaje indica si el bloqueo es por límite diario o total,
    e incluye la palabra "upgrade" o "día" para facilitar el test.
    """


async def check_freemium_gate(
    user_id: str,
    user_tier: str,
    intent: str,
    quota_repo=None,
) -> None:
    """
    Verifica y aplica el gate de cuota freemium.

    Args:
        user_id: ID anónimo del usuario.
        user_tier: Tier del usuario (FREE / BASICO / PREMIUM / VET).
        intent: Intención clasificada (nutritional / medical / emergency).
        quota_repo: Repositorio de cuota inyectable (para tests).

    Raises:
        FreemiumGateError: Si el usuario Free superó su cuota diaria o total.
    """
    # Bypass incondicional para emergencias (Constitution REGLA 9)
    if intent == "emergency":
        return

    # Bypass para tiers pagados
    tier_upper = user_tier.upper()
    if tier_upper in _PAID_TIERS:
        return

    # Control de cuota para tier FREE
    quota = await quota_repo.get_or_create(user_id)

    if quota.total_count >= TOTAL_LIMIT:
        raise FreemiumGateError(
            f"Has agotado las {TOTAL_LIMIT} preguntas gratuitas. "
            "Para continuar, realiza un upgrade a Básico o Premium."
        )

    if quota.daily_count >= DAILY_LIMIT:
        raise FreemiumGateError(
            f"Has alcanzado el límite de {DAILY_LIMIT} preguntas por día. "
            "Vuelve mañana o haz upgrade para acceso ilimitado."
        )

    # Incremento atómico ANTES de llamar al LLM
    await quota_repo.increment(user_id)
