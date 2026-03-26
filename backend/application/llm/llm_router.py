"""
LLMRouter — Routing determinístico de modelos LLM por tier y condiciones médicas.

Constitution REGLA 5 (no negociable):
  Free tier                → openai/gpt-4o-mini
  Básico tier              → openai/gpt-4o-mini
  Premium / Vet tier       → anthropic/claude-sonnet-4-5
  2+ condiciones (any tier)→ anthropic/claude-sonnet-4-5  ← override no negociable
  OCR (todos los tiers)    → openai/gpt-4o (vision) — ver select_ocr_model()

Sin modelos locales (Ollama) ni endpoints :free — ver ADR-019.
Umbral clínico en 2 porque 2 condiciones simultáneas (ej: diabetes+renal) implica
restricciones contradictorias que requieren el modelo de mayor capacidad.

IDs verificados contra OpenRouter API (2026-03-25).
"""
from __future__ import annotations

from backend.domain.aggregates.user_account import UserTier

# Modelos por tier (proveedor: OpenRouter) — IDs exactos verificados
_MODEL_BY_TIER: dict[UserTier, str] = {
    UserTier.FREE:    "openai/gpt-4o-mini",
    UserTier.BASICO:  "openai/gpt-4o-mini",
    UserTier.PREMIUM: "anthropic/claude-sonnet-4-5",
    UserTier.VET:     "anthropic/claude-sonnet-4-5",
}

# Override clínico: 2+ condiciones médicas → modelo máximo (bajado de 3 a 2)
# 2 condiciones simultáneas (diabetes+renal, hepático+pancreático) son clínicamente
# complejas — restricciones contradictorias requieren razonamiento superior.
_CLINICAL_OVERRIDE_MODEL = "anthropic/claude-sonnet-4-5"
_CLINICAL_OVERRIDE_THRESHOLD = 2

# Modelo OCR (siempre, independiente del tier)
_OCR_MODEL = "openai/gpt-4o"


class LLMRouter:
    """
    Router determinístico de modelos LLM.
    Stateless — todos los métodos son classmethods.
    """

    @classmethod
    def select_model(cls, tier: UserTier, conditions_count: int) -> str:
        """
        Selecciona el modelo LLM según tier y número de condiciones médicas.

        Args:
            tier: Tier de suscripción del usuario.
            conditions_count: Número de condiciones médicas activas de la mascota.

        Returns:
            Identificador del modelo en OpenRouter (e.g. "anthropic/claude-sonnet-4-5").
        """
        # Override clínico no negociable (REGLA 5)
        if conditions_count >= _CLINICAL_OVERRIDE_THRESHOLD:
            return _CLINICAL_OVERRIDE_MODEL

        return _MODEL_BY_TIER[tier]

    @classmethod
    def select_ocr_model(cls) -> str:
        """Retorna el modelo OCR — siempre gpt-4o vision, todos los tiers."""
        return _OCR_MODEL
