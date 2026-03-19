"""
ConsultationSubgraph — Stub (implementado en unit-07).

Retorna respuesta válida (no None) para consultas nutricionales.
"""
from __future__ import annotations

from backend.infrastructure.agent.state import NutriVetState


async def consultation_stub(state: NutriVetState) -> NutriVetState:
    """
    Stub del subgrafo de consultas nutricionales.

    Retorna respuesta placeholder — implementación completa en unit-07.
    Nunca retorna None (requisito del orquestador).
    """
    response = (
        "🥗 Gracias por tu consulta nutricional. "
        "El módulo de consultas estará disponible próximamente. "
        "Mientras tanto, puedo ayudarte a generar un plan nutricional personalizado."
    )
    return {**state, "response": response}
