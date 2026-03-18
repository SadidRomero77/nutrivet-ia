# Domain Entities — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Plan Service

### NutritionPlan (Aggregate Raíz)
- `plan_id: UUID`
- `pet_id: UUID` — FK a PetProfile
- `owner_id: UUID` — owner de la mascota
- `status: PlanStatus` — PENDING_VET | ACTIVE | UNDER_REVIEW | ARCHIVED
- `modalidad: Literal["natural", "concentrado"]`
- `plan_type: Literal["estandar", "temporal_medical", "life_stage"]`
- `rer_kcal: Decimal` — calculado por NRCCalculator (NUNCA por LLM)
- `der_kcal: Decimal` — calculado por NRCCalculator (NUNCA por LLM)
- `sections: list[PlanSection]` — exactamente 5 secciones
- `llm_model_used: str` — modelo OpenRouter usado en generación
- `review_date: date | None` — solo para temporal_medical, seteado por vet
- `vet_id: UUID | None` — vet que firmó el plan
- `vet_comment: str | None` — comentario al devolver a PENDING_VET
- `disclaimer: str` — fijo: "NutriVet.IA es asesoría nutricional digital..."
- `created_at: datetime`
- `activated_at: datetime | None`
- `archived_at: datetime | None`

### PlanSection
5 secciones fijas del plan generado por LLM:
- `section_id: UUID`
- `plan_id: UUID`
- `order: int` — 1–5
- `title: str` — ej: "Resumen nutricional", "Ingredientes y porciones", etc.
- `content: str` — generado por LLM, validado por guardarraíles

### PlanJob
Job asíncrono en ARQ para generación de plan.
- `job_id: UUID`
- `pet_id: UUID`
- `owner_id: UUID`
- `modalidad: str`
- `status: Literal["queued", "processing", "completed", "failed"]`
- `arq_job_id: str | None` — ID del job en Redis/ARQ
- `result_plan_id: UUID | None` — plan generado
- `error_message: str | None`
- `enqueued_at: datetime`
- `completed_at: datetime | None`

### SubstituteSet
Alternativas de ingredientes para mascotas con alergias o restricciones.
- `substitute_id: UUID`
- `plan_id: UUID`
- `original_ingredient: str`
- `substitutes: list[str]`
- `reason: str` — alergia / restricción médica / toxicidad

### AgentTrace (Append-Only)
Traza inmutable de cada invocación al LLM durante la generación del plan.
- `trace_id: UUID`
- `plan_id: UUID`
- `pet_id: UUID` — UUID anónimo (nunca nombre ni especie en texto)
- `llm_model: str`
- `prompt_tokens: int`
- `completion_tokens: int`
- `latency_ms: int`
- `node_name: str` — nodo LangGraph que generó la traza
- `created_at: datetime`
- **NUNCA tiene UPDATE** — insert-only en PostgreSQL

## Value Objects del Plan

### PlanStatus (Enum)
```python
class PlanStatus(str, Enum):
    PENDING_VET = "PENDING_VET"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    ARCHIVED = "ARCHIVED"
```

### PlanGenerationRequest
```python
@dataclass
class PlanGenerationRequest:
    pet_id: UUID
    owner_id: UUID
    modalidad: Literal["natural", "concentrado"]
    tier: str
```
