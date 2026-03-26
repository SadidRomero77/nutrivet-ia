"""
Feature flags de NutriVet.IA — control de features por fase de desarrollo.

Para activar/desactivar una feature, cambiar el valor de la constante correspondiente.
En producción, estas se pueden sobreescribir con variables de entorno.

MVP_FREEMIUM_DISABLED:
    True  → todas las restricciones de tier/cuota desactivadas (todos tienen acceso ilimitado).
    False → freemium activo con límites reales de tier.

    Activar en False antes del launch comercial, cuando PayU y tier management
    estén validados con usuarios reales.
"""
from __future__ import annotations

import os


def _bool_flag(env_var: str, default: bool) -> bool:
    """Lee un feature flag como variable de entorno. Default si no está definida."""
    raw = os.environ.get(env_var, "").strip().lower()
    if raw == "true":
        return True
    if raw == "false":
        return False
    return default


# ── MVP: restricciones de tier/cuota desactivadas ─────────────────────────────
# Durante el piloto (BAMPYSVET), todos los usuarios tienen acceso ilimitado.
# Cambiar a False (o setear MVP_FREEMIUM_DISABLED=false en el entorno)
# antes del launch comercial.
MVP_FREEMIUM_DISABLED: bool = _bool_flag("MVP_FREEMIUM_DISABLED", default=True)
