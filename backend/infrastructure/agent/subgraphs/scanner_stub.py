"""
ScannerSubgraph — Stub (implementado en unit-06).

Retorna respuesta válida (no None) para análisis de etiquetas nutricionales.
"""
from __future__ import annotations

from backend.infrastructure.agent.state import NutriVetState


async def scanner_stub(state: NutriVetState) -> NutriVetState:
    """
    Stub del subgrafo de scanner OCR.

    Retorna respuesta placeholder — implementación completa en unit-06.
    Nunca retorna None (requisito del orquestador).
    """
    response = (
        "📷 Función de escáner nutricional en desarrollo. "
        "Próximamente podrás analizar etiquetas de alimentos para evaluar "
        "si son adecuados para el perfil de tu mascota."
    )
    return {**state, "response": response}
