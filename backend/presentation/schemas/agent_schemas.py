"""
Schemas Pydantic para el endpoint del agente (POST /v1/agent/process).

Constitution REGLA 8: el disclaimer está presente en cada respuesta del agente.
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

_DISCLAIMER = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)


class AgentRequest(BaseModel):
    """Request al endpoint del agente."""

    pet_id: str = Field(..., description="UUID de la mascota objetivo")
    message: str = Field(..., min_length=1, max_length=2000, description="Mensaje del usuario")
    modality: Optional[str] = Field(
        default="natural",
        description="Modalidad del plan: natural | concentrado | mixto",
    )


class AgentResponse(BaseModel):
    """Respuesta del orquestador al usuario."""

    intent: Optional[str] = Field(None, description="Intent clasificado")
    response: str = Field(..., description="Respuesta del agente al usuario")
    plan_id: Optional[str] = Field(None, description="ID del plan generado (si aplica)")
    requires_vet_review: bool = Field(
        default=False, description="Si el plan requiere revisión veterinaria"
    )
    disclaimer: str = Field(
        default=_DISCLAIMER,
        description="Aviso legal obligatorio (REGLA 8)",
    )

    @classmethod
    def from_state(cls, state: dict) -> "AgentResponse":
        """Construye la respuesta desde el state final del grafo."""
        return cls(
            intent=state.get("intent"),
            response=state.get("response") or "Procesado.",
            plan_id=state.get("plan_id"),
            requires_vet_review=state.get("requires_vet_review", False),
        )
