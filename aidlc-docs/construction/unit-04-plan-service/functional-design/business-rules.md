# Business Rules — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Plan Service

### BR-PLAN-01: Generación Asíncrona via ARQ
- La generación de un plan NUNCA es síncrona (puede tardar hasta 30s con LLM).
- El endpoint devuelve inmediatamente un `job_id` (HTTP 202 Accepted).
- El cliente hace polling a `GET /plans/jobs/{job_id}` hasta `status == "completed"`.
- El worker ARQ en Redis ejecuta la generación en background.

### BR-PLAN-02: HITL Routing
- Mascota sin condiciones médicas (`condiciones_medicas == []`):
  → Plan se crea con status `ACTIVE` directamente.
- Mascota con condición(es) médica(s):
  → Plan se crea con status `PENDING_VET`.
  → El plan no puede usarse hasta que un vet lo firme.

### BR-PLAN-03: LLM Routing por Tier + Override Clínico
```
n_conditions >= 3 (cualquier tier) → anthropic/claude-sonnet-4-5 (override clínico)
tier == "premium" o "vet"          → anthropic/claude-sonnet-4-5
tier == "basico"                   → openai/gpt-4o-mini
tier == "free"                     → meta-llama/llama-3.3-70b
```
El modelo usado se registra en `NutritionPlan.llm_model_used` y en `AgentTrace`.

### BR-PLAN-04: 0 Ingredientes Tóxicos en el Plan
- Antes de persistir el plan, TODOS los ingredientes pasan por `FoodSafetyChecker`.
- Si se detecta un tóxico → el job falla con `status = "failed"` y error descriptivo.
- El plan NUNCA se persiste con un ingrediente tóxico.
- Quality Gate G1: golden set de 60 casos → 0 tóxicos.

### BR-PLAN-05: 5 Secciones Fijas
- El plan siempre tiene exactamente 5 secciones generadas por LLM:
  1. Resumen nutricional
  2. Ingredientes y porciones por día
  3. Instrucciones de preparación
  4. Protocolo de transición (7 días si cambia de dieta)
  5. Advertencias y consideraciones especiales
- El LLM decide el contenido de cada sección (con guardarraíles deterministas activos).

### BR-PLAN-06: AgentTrace — Insert Only
- Cada invocación al LLM durante la generación crea un `AgentTrace`.
- Las trazas son append-only — NUNCA se modifican post-inserción.
- No existe ningún método UPDATE en el repositorio de trazas.
- Retención: 90 días en PostgreSQL, luego archivado a Cloudflare R2.

### BR-PLAN-07: Firma de Vet
- Solo un usuario con `role == "vet"` puede firmar un plan `PENDING_VET`.
- El vet puede: aprobar (→ ACTIVE) o devolver con comentario (→ PENDING_VET).
- No existe estado "RECHAZADO" — devolver con comentario permite al owner corregir.
- El comentario de devolución es obligatorio.
- Al aprobar, el vet puede modificar secciones del plan (con registro de cambios).

### BR-PLAN-08: Disclaimer Obligatorio
- El campo `disclaimer` es fijo e inmutable: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
- Debe aparecer en cada vista del plan en la app.

### BR-PLAN-09: Solo Planes ACTIVE son Exportables
- Solo planes con `status == ACTIVE` pueden exportarse a PDF.
- El export service verifica el status antes de generar el PDF.

### BR-PLAN-10: Límites de Plan por Tier
- Free: 1 plan total (puede incluir 1 con condición médica).
- Básico: 1 plan nuevo por mes.
- Premium: ilimitados.
- Vet: ilimitados (pacientes).
