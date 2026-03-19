"""
Pydantic schemas para plan-service.

ADR-020: Plan estructurado en 5 secciones:
  1. perfil_nutricional  — RER, DER, macros objetivo
  2. ingredientes        — lista con cantidades en gramos
  3. porciones           — distribución diaria (comidas/día)
  4. instrucciones_preparacion — pasos de elaboración
  5. transicion_dieta    — solo si has_transition_protocol=True
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class PlanGenerateRequest(BaseModel):
    """Solicitud de generación de plan nutricional."""
    pet_id: UUID
    modality: str = Field(..., pattern="^(concentrado|natural)$")


class PlanApproveRequest(BaseModel):
    """Aprobación de plan por veterinario."""
    review_date: Optional[date] = None  # Obligatorio para TEMPORAL_MEDICAL


class PlanReturnRequest(BaseModel):
    """Devolución de plan por veterinario con comentario obligatorio."""
    comment: str = Field(..., min_length=10)


class SubstituteRequest(BaseModel):
    """Solicitud de sustitución de ingrediente."""
    original_ingredient: str
    substitute_ingredient: str


# ---------------------------------------------------------------------------
# Response schemas — 5 secciones (ADR-020)
# ---------------------------------------------------------------------------

class NutritionalProfileSection(BaseModel):
    """Sección 1: Perfil nutricional calculado."""
    rer_kcal: float
    der_kcal: float
    weight_phase: str
    protein_pct: Optional[float] = None
    fat_pct: Optional[float] = None
    carbs_pct: Optional[float] = None


class IngredientItem(BaseModel):
    """Un ingrediente con cantidad en gramos."""
    nombre: str
    cantidad_gramos: Optional[float] = None
    notas: Optional[str] = None


class IngredientsSection(BaseModel):
    """Sección 2: Lista de ingredientes."""
    items: list[IngredientItem] = []


class PortionsSection(BaseModel):
    """Sección 3: Distribución de porciones diarias."""
    comidas_por_dia: int = 2
    porcion_por_comida_gramos: Optional[float] = None
    notas: Optional[str] = None


class PreparationSection(BaseModel):
    """Sección 4: Instrucciones de preparación."""
    pasos: list[str] = []
    tiempo_estimado_minutos: Optional[int] = None
    notas: Optional[str] = None


class TransitionSection(BaseModel):
    """Sección 5: Protocolo de transición (solo si applies)."""
    duracion_dias: int = 7
    semana_1_pct_nuevo: int = 25
    semana_2_pct_nuevo: int = 50
    semana_3_pct_nuevo: int = 75
    semana_4_pct_nuevo: int = 100
    notas: Optional[str] = None


class PlanResponse(BaseModel):
    """
    Respuesta completa del plan con 5 secciones (ADR-020).
    Disclaimer obligatorio (Constitution REGLA 8).
    """
    plan_id: UUID
    pet_id: UUID
    owner_id: UUID
    plan_type: str
    status: str
    modality: str
    llm_model_used: str
    # Secciones
    perfil_nutricional: NutritionalProfileSection
    ingredientes: IngredientsSection = IngredientsSection()
    porciones: PortionsSection = PortionsSection()
    instrucciones_preparacion: PreparationSection = PreparationSection()
    transicion_dieta: Optional[TransitionSection] = None  # solo si has_transition_protocol
    # HITL
    approved_by_vet_id: Optional[UUID] = None
    review_date: Optional[date] = None
    vet_comment: Optional[str] = None
    # Disclaimer obligatorio (REGLA 8)
    disclaimer: str = (
        "NutriVet.IA es asesoría nutricional digital — "
        "no reemplaza el diagnóstico médico veterinario."
    )


class PlanSummaryResponse(BaseModel):
    """Resumen de plan para listados."""
    plan_id: UUID
    pet_id: UUID
    plan_type: str
    status: str
    modality: str
    rer_kcal: float
    der_kcal: float
    llm_model_used: str
    approved_by_vet_id: Optional[UUID] = None
    disclaimer: str = (
        "NutriVet.IA es asesoría nutricional digital — "
        "no reemplaza el diagnóstico médico veterinario."
    )


class PlanJobResponse(BaseModel):
    """Estado del job de generación (para polling)."""
    job_id: UUID
    status: str  # QUEUED | PROCESSING | READY | FAILED
    plan_id: Optional[UUID] = None
    error_message: Optional[str] = None


class SubstituteResponse(BaseModel):
    """Respuesta de sustitución de ingrediente."""
    original_ingredient: str
    substitute_ingredient: str
    requires_vet_review: bool
    plan_status: str
