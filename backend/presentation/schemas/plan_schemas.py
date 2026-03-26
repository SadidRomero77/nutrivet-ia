"""
Pydantic schemas para plan-service.

Estructura del plan clínico (basado en plan de referencia Lady Carolina Castañeda, MV, BAMPYSVET):
  1. perfil_nutricional  — RER, DER, macros objetivo
  2. objetivos_clinicos  — 3-4 objetivos personalizados
  3. ingredientes_prohibidos — alimentos prohibidos para este paciente
  4. ingredientes        — lista con cantidades en gramos y detalle nutricional
  5. porciones           — cronograma diario por comida (proteína/carbo/vegetal)
  6. suplementos         — suplementos prescritos con dosis
  7. instrucciones_preparacion — pasos + instrucciones por grupo + adiciones permitidas
  8. snacks_saludables   — hasta 3 opciones de snacks aprobados
  9. protocolo_digestivo — qué hacer ante síntomas GI
  10. transicion_dieta   — protocolo de transición gradual
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
# Response schemas — estructura clínica completa
# ---------------------------------------------------------------------------

class NutritionalProfileSection(BaseModel):
    """Sección 1: Perfil nutricional calculado."""
    rer_kcal: float
    der_kcal: float
    weight_phase: str
    protein_pct: Optional[float] = None
    fat_pct: Optional[float] = None
    carbs_pct: Optional[float] = None
    racion_total_g_dia: Optional[float] = None
    relacion_ca_p: Optional[float] = None
    omega3_mg_dia: Optional[float] = None


class IngredientItem(BaseModel):
    """Un ingrediente con cantidad en gramos y detalle nutricional."""
    nombre: str
    cantidad_g: Optional[float] = None  # Campo correcto del LLM
    kcal: Optional[float] = None
    proteina_g: Optional[float] = None
    grasa_g: Optional[float] = None
    fuente: Optional[str] = None
    frecuencia: Optional[str] = None
    notas: Optional[str] = None


class IngredientsSection(BaseModel):
    """Sección 2: Lista de ingredientes con aporte nutricional."""
    items: list[IngredientItem] = []


class ComidaDistribucion(BaseModel):
    """Distribución de una comida con detalle por grupo de alimento."""
    horario: str
    porcentaje: Optional[float] = None
    gramos: Optional[float] = None
    proteina_g: Optional[float] = None
    carbo_g: Optional[float] = None
    vegetal_g: Optional[float] = None


class PortionsSection(BaseModel):
    """Sección 3: Cronograma diario de comidas."""
    comidas_por_dia: int = 2
    total_g_dia: Optional[float] = None
    g_por_comida: Optional[float] = None
    distribucion_comidas: list[ComidaDistribucion] = []
    # Legacy fields for backward compat
    porcion_por_comida_gramos: Optional[float] = None
    notas: Optional[str] = None


class SupplementItem(BaseModel):
    """Un suplemento prescrito."""
    nombre: str
    dosis: str
    frecuencia: str
    forma: str
    justificacion: str


class InstruccionesPorGrupo(BaseModel):
    """Instrucciones de preparación por grupo de alimento."""
    proteinas: list[str] = []
    carbohidratos: list[str] = []
    vegetales: list[str] = []


class PreparationSection(BaseModel):
    """Sección 4: Instrucciones de preparación completas."""
    metodo: Optional[str] = None
    pasos: list[str] = []
    tiempo_preparacion_minutos: Optional[int] = None
    almacenamiento: Optional[str] = None
    advertencias: list[str] = []
    instrucciones_por_grupo: InstruccionesPorGrupo = InstruccionesPorGrupo()
    adiciones_permitidas: list[str] = []
    # Legacy fields
    tiempo_estimado_minutos: Optional[int] = None
    notas: Optional[str] = None


class SnackSaludable(BaseModel):
    """Un snack saludable aprobado."""
    nombre: str
    descripcion: str
    cantidad_g: float
    frecuencia: str


class FaseTransicion(BaseModel):
    """Una fase del protocolo de transición."""
    dias: str
    descripcion: str


class TransitionSection(BaseModel):
    """Sección 5: Protocolo de transición gradual."""
    requiere_transicion: bool = True
    duracion_dias: int = 7
    fases: list[FaseTransicion] = []
    senales_de_alerta: list[str] = []
    # Legacy fields for backward compat
    semana_1_pct_nuevo: int = 25
    semana_2_pct_nuevo: int = 50
    semana_3_pct_nuevo: int = 75
    semana_4_pct_nuevo: int = 100
    notas: Optional[str] = None


class PlanResponse(BaseModel):
    """
    Respuesta completa del plan nutricional.
    Estructura clínica completa (Lady Carolina Castañeda, MV, BAMPYSVET).
    Disclaimer obligatorio (Constitution REGLA 8).
    """
    plan_id: UUID
    pet_id: UUID
    owner_id: UUID
    plan_type: str
    status: str
    modality: str
    llm_model_used: str
    # Secciones clínicas
    perfil_nutricional: NutritionalProfileSection
    objetivos_clinicos: list[str] = []
    ingredientes_prohibidos: list[str] = []
    ingredientes: IngredientsSection = IngredientsSection()
    porciones: PortionsSection = PortionsSection()
    suplementos: list[SupplementItem] = []
    instrucciones_preparacion: PreparationSection = PreparationSection()
    snacks_saludables: list[SnackSaludable] = []
    protocolo_digestivo: list[str] = []
    transicion_dieta: Optional[TransitionSection] = None
    notas_clinicas: list[str] = []
    alertas_propietario: list[str] = []
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
    conditions_count: int = 0
    created_at: Optional[str] = None
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
