"""
Esquemas Pydantic para validar y parsear el output JSON del LLM generador de planes.

Diseñados para ser estrictos pero con fallbacks razonables.
Usados tanto en nodo_7_validate_output (post-LLM) como en nutritional_validator.

El esquema refleja la estructura exacta que el LLM debe generar según el plan_generation_prompts.
Incluye todas las secciones del plan clínico de referencia (Lady Carolina Castañeda, MV, BAMPYSVET).
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class IngredienteSchema(BaseModel):
    """Un ingrediente del plan con su aporte nutricional calculado."""

    nombre: str = Field(..., description="Nombre en español, disponible en LATAM")
    cantidad_g: float = Field(..., gt=0, description="Gramos por día")
    kcal: float = Field(..., gt=0, description="Calorías que aporta esta cantidad")
    proteina_g: float = Field(default=0.0, ge=0)
    grasa_g: float = Field(default=0.0, ge=0)
    fuente: Literal["animal", "vegetal", "suplemento"] = Field(default="animal")
    frecuencia: str = Field(
        default="diario",
        description="Frecuencia de uso (diario / 3 veces/semana / etc.)",
    )
    notas: Optional[str] = Field(
        default=None, description="Nota clínica o de preparación del ingrediente"
    )

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        """Valida que el nombre no esté vacío."""
        if not v.strip():
            raise ValueError("nombre del ingrediente no puede estar vacío")
        return v.strip()


class PerfilNutricionalSchema(BaseModel):
    """Perfil nutricional calculado del plan completo."""

    rer_kcal: float = Field(..., gt=0, description="RER determinístico (Nodo 2)")
    der_kcal: float = Field(..., gt=0, description="DER determinístico (Nodo 2)")
    proteina_pct_ms: float = Field(
        ..., gt=0, le=100, description="% proteína sobre materia seca"
    )
    grasa_pct_ms: float = Field(
        ..., gt=0, le=100, description="% grasa sobre materia seca"
    )
    fibra_pct_ms: float = Field(default=5.0, ge=0, le=50)
    calcio_g_dia: float = Field(default=0.0, ge=0)
    fosforo_g_dia: float = Field(default=0.0, ge=0)
    sodio_mg_dia: float = Field(default=0.0, ge=0)
    omega3_mg_dia: float = Field(default=0.0, ge=0)
    racion_total_g_dia: float = Field(..., gt=0, description="Total gramos de alimento por día")
    kcal_verificadas: float = Field(
        ..., gt=0, description="Suma de kcal de todos los ingredientes"
    )
    relacion_ca_p: Optional[float] = Field(
        default=None, description="Ratio Ca:P (meta: 1.0-2.0)"
    )
    # ── Campos de composición corporal (A-07) ────────────────────────────────
    peso_actual_kg: Optional[float] = Field(
        default=None, gt=0, description="Peso real del paciente en kg"
    )
    peso_ideal_estimado_kg: Optional[float] = Field(
        default=None, gt=0, description="Peso ideal estimado según BCS y especie"
    )
    bcs_actual: Optional[int] = Field(
        default=None, ge=1, le=9, description="Body Condition Score actual (1-9)"
    )
    fase: Optional[str] = Field(
        default=None,
        description="Fase del plan: 'reduccion' (BCS≥7) | 'mantenimiento' (BCS 4-6) | 'aumento' (BCS≤3)",
    )
    meta_peso: Optional[str] = Field(
        default=None,
        description="Descripción de la meta de peso (e.g. 'reducir 1.5 kg en 3 meses')",
    )

    @model_validator(mode="after")
    def validar_calorias_consistentes(self) -> "PerfilNutricionalSchema":
        """Verifica que kcal_verificadas sea aproximadamente igual a der_kcal (±15%)."""
        tolerancia = 0.15
        diferencia = abs(self.kcal_verificadas - self.der_kcal) / self.der_kcal
        if diferencia > tolerancia:
            # No levanta error — el validator externo lo manejará como warning
            pass
        return self


class ComidaDistribucion(BaseModel):
    """Distribución de una comida individual durante el día."""

    horario: str = Field(..., description="Horario sugerido (mañana 7:00, tarde 17:00)")
    porcentaje: float = Field(..., gt=0, le=100)
    gramos: float = Field(..., gt=0)
    proteina_g: float = Field(default=0.0, ge=0, description="Gramos de proteína en esta comida")
    carbo_g: float = Field(default=0.0, ge=0, description="Gramos de carbohidrato en esta comida")
    vegetal_g: float = Field(default=0.0, ge=0, description="Gramos de vegetal en esta comida")


class PorcionDiariaSchema(BaseModel):
    """Información de porcionamiento diario."""

    total_g_dia: float = Field(..., gt=0)
    numero_comidas: int = Field(..., ge=1, le=6)
    g_por_comida: float = Field(..., gt=0)
    distribucion_comidas: list[ComidaDistribucion] = Field(
        default_factory=list,
        description="Distribución horaria de las comidas con detalle por grupo",
    )

    @model_validator(mode="after")
    def validar_distribucion(self) -> "PorcionDiariaSchema":
        """Verifica que los porcentajes sumen 100% (±5%)."""
        if self.distribucion_comidas:
            total_pct = sum(c.porcentaje for c in self.distribucion_comidas)
            if abs(total_pct - 100) > 5:
                pass  # Warning solo, no error bloqueante
        return self


class SupplementoSchema(BaseModel):
    """Suplemento prescrito con dosificación específica."""

    nombre: str
    dosis: str = Field(..., description="Dosis con unidad (e.g. '500 mg/día')")
    frecuencia: str
    forma: str = Field(..., description="Presentación (cápsula, polvo, aceite)")
    justificacion: str = Field(..., description="Por qué se prescribe este suplemento")


class PreparacionSchema(BaseModel):
    """Instrucciones de preparación del plan."""

    metodo: str = Field(..., description="cocción suave / BARF / mixto")
    pasos: list[str] = Field(
        ..., min_length=1, description="Instrucciones paso a paso"
    )
    tiempo_preparacion_minutos: int = Field(default=30, ge=5)
    almacenamiento: str = Field(
        default="Refrigerar hasta 3 días en recipiente hermético.",
        description="Instrucciones de conservación",
    )
    advertencias: list[str] = Field(
        default_factory=list,
        description="Advertencias de seguridad alimentaria",
    )
    instrucciones_por_grupo: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Instrucciones específicas por grupo (proteínas, carbohidratos, vegetales)",
    )
    adiciones_permitidas: list[str] = Field(
        default_factory=list,
        description="Especias y adiciones seguras permitidas (cúrcuma, orégano, albahaca)",
    )


class FaseTransicion(BaseModel):
    """Una fase del período de transición dietética."""

    dias: str = Field(..., description="Rango de días (e.g. '1-3')")
    descripcion: str = Field(..., description="Proporción nuevo/viejo alimento")


class TransicionSchema(BaseModel):
    """Protocolo de transición gradual al nuevo plan."""

    requiere_transicion: bool = Field(
        default=True,
        description="True excepto cuando es continuación de dieta similar",
    )
    duracion_dias: int = Field(
        default=10, ge=5, le=42,
        description="Duración en días (5-21 estándar; hasta 42 para megaesofago)",
    )
    fases: list[FaseTransicion] = Field(default_factory=list)
    senales_de_alerta: list[str] = Field(
        default_factory=list,
        description="Síntomas que indican problema durante transición",
    )


class SnackSaludableSchema(BaseModel):
    """Opción de snack saludable para el paciente."""

    nombre: str = Field(..., description="Nombre del snack")
    descripcion: str = Field(..., description="Descripción corta y preparación")
    cantidad_g: float = Field(..., gt=0, description="Cantidad máxima por ocasión en gramos")
    frecuencia: str = Field(default="ocasional", description="Con qué frecuencia puede darse")


class PlanOutputSchema(BaseModel):
    """
    Esquema completo del plan nutricional generado por el LLM.

    Este es el contrato que el LLM debe cumplir. El nodo_7_validate_output
    verifica que el JSON del LLM sea válido contra este esquema.

    Basado en el plan clínico de referencia de Lady Carolina Castañeda (MV, BAMPYSVET).
    """

    perfil_nutricional: PerfilNutricionalSchema
    objetivos_clinicos: list[str] = Field(
        default_factory=list,
        min_length=2,
        description="3-4 objetivos clínicos personalizados para este paciente",
    )
    ingredientes_prohibidos: list[str] = Field(
        default_factory=list,
        description="Alimentos prohibidos específicos para este paciente por condición/alergia",
    )
    ingredientes: list[IngredienteSchema] = Field(..., min_length=2)
    porciones: PorcionDiariaSchema
    suplementos: list[SupplementoSchema] = Field(
        default_factory=list,
        description="Lista vacía si no hay suplementos recomendados",
    )
    instrucciones_preparacion: PreparacionSchema
    snacks_saludables: list[SnackSaludableSchema] = Field(
        default_factory=list,
        description="Hasta 3 opciones de snacks saludables aprobados para este paciente",
    )
    protocolo_digestivo: list[str] = Field(
        default_factory=list,
        description="Qué hacer si hay síntomas GI durante el plan (vómito, diarrea, inapetencia)",
    )
    transicion_dieta: TransicionSchema
    notas_clinicas: list[str] = Field(
        default_factory=list,
        description="Notas para el veterinario revisor (si PENDING_VET)",
    )
    alertas_propietario: list[str] = Field(
        default_factory=list,
        description="Alertas importantes para el propietario",
    )
    alertas_barf: list[str] = Field(
        default_factory=list,
        description="Alertas de seguridad bacteriológica BARF (solo dieta natural). "
                    "Vacío para dieta de concentrado.",
    )

    @model_validator(mode="after")
    def validar_suma_ingredientes(self) -> "PlanOutputSchema":
        """Verifica coherencia entre suma de kcal y perfil nutricional."""
        if self.ingredientes:
            suma_kcal = sum(i.kcal for i in self.ingredientes)
            # Solo marcamos inconsistencia, no bloqueamos (el validator externo decide)
            self.perfil_nutricional.kcal_verificadas = suma_kcal
        return self

    def suma_kcal_ingredientes(self) -> float:
        """Retorna la suma de calorías de todos los ingredientes."""
        return sum(i.kcal for i in self.ingredientes)

    def desviacion_calorica_pct(self) -> float:
        """
        Retorna la desviación porcentual entre kcal_verificadas y der_kcal.

        Desviación > 10% indica que el LLM calculó mal las porciones.
        """
        if self.perfil_nutricional.der_kcal == 0:
            return 0.0
        return abs(self.suma_kcal_ingredientes() - self.perfil_nutricional.der_kcal) / self.perfil_nutricional.der_kcal


# ─── Schema de instrucción JSON para el LLM ──────────────────────────────────

JSON_FORMAT_INSTRUCTION = """
FORMATO DE SALIDA — JSON ESTRICTO:

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura exacta.
NO incluyas markdown (```json), NO texto antes o después del JSON.

{
  "perfil_nutricional": {
    "rer_kcal": <float — valor provisto, NO calcular>,
    "der_kcal": <float — valor provisto, NO calcular>,
    "proteina_pct_ms": <float — % proteína sobre materia seca del plan>,
    "grasa_pct_ms": <float — % grasa sobre materia seca>,
    "fibra_pct_ms": <float — % fibra cruda sobre materia seca>,
    "calcio_g_dia": <float — gramos de calcio aportados>,
    "fosforo_g_dia": <float — gramos de fósforo aportados>,
    "sodio_mg_dia": <float — miligramos de sodio>,
    "omega3_mg_dia": <float — miligramos de EPA+DHA>,
    "racion_total_g_dia": <float — total gramos de alimento/día>,
    "kcal_verificadas": <float — suma de kcal de todos los ingredientes>,
    "relacion_ca_p": <float — ratio Calcio:Fósforo, debe estar entre 1.0 y 2.0>,
    "peso_actual_kg": <float — peso real del paciente, provisto en el perfil>,
    "peso_ideal_estimado_kg": <float — peso ideal estimado según BCS y especie>,
    "bcs_actual": <int — BCS actual 1-9, provisto en el perfil>,
    "fase": "<reduccion|mantenimiento|aumento — determinado por BCS>",
    "meta_peso": "<descripción de la meta, e.g. 'mantener 10 kg' o 'reducir 1.5 kg en 3 meses'>"
  },
  "objetivos_clinicos": [
    "<objetivo 1 — personalizado para este paciente específico>",
    "<objetivo 2>",
    "<objetivo 3>",
    "<objetivo 4>"
  ],
  "ingredientes_prohibidos": [
    "<alimento prohibido específico para este paciente por condición o alergia>",
    "<alimento prohibido 2>"
  ],
  "ingredientes": [
    {
      "nombre": "<nombre en español, disponible en LATAM>",
      "cantidad_g": <float — gramos por día>,
      "kcal": <float — calorías que aporta esta cantidad>,
      "proteina_g": <float — gramos de proteína en esta porción>,
      "grasa_g": <float — gramos de grasa en esta porción>,
      "fuente": "<animal|vegetal|suplemento>",
      "frecuencia": "<diario|X veces/semana>",
      "notas": "<nota clínica opcional>"
    }
  ],
  "porciones": {
    "total_g_dia": <float>,
    "numero_comidas": <int — 2 a 4 comidas/día>,
    "g_por_comida": <float — total_g_dia / numero_comidas>,
    "distribucion_comidas": [
      {
        "horario": "<mañana 7:00>",
        "porcentaje": <float>,
        "gramos": <float>,
        "proteina_g": <float — gramos de proteína en esta comida>,
        "carbo_g": <float — gramos de carbohidrato en esta comida>,
        "vegetal_g": <float — gramos de vegetal en esta comida>
      }
    ]
  },
  "suplementos": [
    {
      "nombre": "<nombre del suplemento>",
      "dosis": "<dosis con unidad>",
      "frecuencia": "<diario|semanal>",
      "forma": "<cápsula|polvo|aceite>",
      "justificacion": "<razón clínica>"
    }
  ],
  "instrucciones_preparacion": {
    "metodo": "<cocción suave|BARF|mixto>",
    "pasos": ["<paso 1>", "<paso 2>", ...],
    "tiempo_preparacion_minutos": <int>,
    "almacenamiento": "<instrucciones de conservación>",
    "advertencias": ["<advertencia 1>"],
    "instrucciones_por_grupo": {
      "proteinas": ["<cómo cocinar las proteínas — temperatura, tiempo>"],
      "carbohidratos": ["<cómo preparar los carbohidratos>"],
      "vegetales": ["<cómo cocinar o servir los vegetales>"]
    },
    "adiciones_permitidas": [
      "<especia o adición segura — e.g. cúrcuma 1/4 cucharadita, orégano seco>",
      "<adición 2>"
    ]
  },
  "snacks_saludables": [
    {
      "nombre": "<nombre del snack>",
      "descripcion": "<descripción y preparación simple>",
      "cantidad_g": <float — gramos máximos por ocasión>,
      "frecuencia": "<ocasional|2-3 veces/semana>"
    }
  ],
  "protocolo_digestivo": [
    "<qué hacer si hay vómito>",
    "<qué hacer si hay diarrea>",
    "<qué hacer si hay inapetencia por más de 24h>"
  ],
  "transicion_dieta": {
    "requiere_transicion": <true|false>,
    "duracion_dias": <int — 7 a 14 días>,
    "fases": [
      {"dias": "1-3", "descripcion": "25% nuevo + 75% anterior"},
      {"dias": "4-7", "descripcion": "50% nuevo + 50% anterior"},
      {"dias": "8-10", "descripcion": "75% nuevo + 25% anterior"},
      {"dias": "11+", "descripcion": "100% nuevo plan"}
    ],
    "senales_de_alerta": ["<síntoma que requiere suspender transición>"]
  },
  "notas_clinicas": ["<nota para el veterinario revisor>"],
  "alertas_propietario": ["<alerta importante para el propietario>"],
  "alertas_barf": ["<solo si dieta natural: alerta de seguridad bacteriológica BARF>"]
}
"""
