# Plan: Functional Design — Unit 04: plan-service

**Unidad**: unit-04-plan-service
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del servicio de planes nutricionales: generación asíncrona
(ARQ), máquina de estados del plan, HITL review, sustitución de ingredientes,
LLM routing y agent_traces append-only.

## Generación Asíncrona (ARQ Job Pattern)

```
POST /v1/plans/generate
  → valida request (pet_id, modalidad, owner_id)
  → encola job en Redis (ARQ)
  → retorna inmediatamente: { job_id: UUID, status: "QUEUED" }

GET /v1/plans/jobs/{job_id}
  → retorna: { status: "QUEUED|PROCESSING|READY|FAILED", plan_id? }
  → cliente hace polling cada 3s (máx 60s / 20 intentos)

ARQ Worker (background):
  → procesa job: pasos 1-11 del business-logic-model.md
  → actualiza job status → READY (con plan_id) o FAILED (con error)
```

**Justificación**: La generación puede tomar hasta 30s (LLM). Un job asíncrono evita
timeouts HTTP y permite UX con barra de progreso.

## Máquina de Estados del Plan

```
[Sano]              → ACTIVE (directo, sin HITL)
[Con condición]     → PENDING_VET → (firma vet) → ACTIVE
                                 → (devuelve vet) → PENDING_VET (con comentario)

ACTIVE → (trigger médico) → UNDER_REVIEW → ARCHIVED (plan anterior)
                          → nuevo plan PENDING_VET
ACTIVE → (owner agrega condición) → PENDING_VET
ACTIVE → (solo ACTIVE es exportable a PDF)
```

**Status válidos**: `PENDING_VET` · `ACTIVE` · `UNDER_REVIEW` · `ARCHIVED`

**No existe `REJECTED`**: el vet solo puede aprobar o devolver con comentario obligatorio.
**No existe `DRAFT`**: el plan se crea directamente al completar el wizard.

## HITL Review — Flujo del Veterinario

```
Vet ve dashboard: lista de planes PENDING_VET asignados a su clínica

Opción A — Aprobar:
  → para plan temporal_medical: review_date obligatorio
  → plan → ACTIVE
  → owner notificado (push)

Opción B — Devolver con comentario:
  → comentario no puede estar vacío (regla hard-coded)
  → plan vuelve a PENDING_VET con comentario visible al owner
  → owner notificado con el comentario
```

## Sustitución de Ingredientes (Ingredient Substitution)

```
Owner solicita sustituir ingrediente en plan ACTIVE

Pre-approved substitute set (almacenado en tabla substitute_sets):
  → sustituto DENTRO del set → plan permanece ACTIVE (sin HITL)
  → sustituto FUERA del set → plan vuelve a PENDING_VET

Flujo de validación del sustituto:
  1. FoodSafetyChecker.check(sustituto, species) → debe pasar
  2. MedicalRestrictionEngine.validate(sustituto, conditions) → debe pasar
  3. Si en substitute_set → ACTIVE · Si fuera → PENDING_VET
```

## LLM Routing (ADR-019)

| Condición | Modelo | Proveedor |
|-----------|--------|-----------|
| Free tier | `meta-llama/llama-3.3-70b` | OpenRouter |
| Básico tier | `openai/gpt-4o-mini` | OpenRouter |
| Premium / Vet tier | `anthropic/claude-sonnet-4-5` | OpenRouter |
| 3+ condiciones médicas (any tier) | `anthropic/claude-sonnet-4-5` | OpenRouter (override) |

**Override clínico**: 3+ condiciones siempre usa `claude-sonnet-4-5`, independientemente del tier.
El `LLMRouter` es determinista — no involucra ningún LLM para tomar la decisión de routing.

## Estructura del Plan — 5 Secciones (ADR-020)

```
Sección 1: Resumen nutricional (RER, DER, macros objetivo)
Sección 2: Plan semanal (Lun→Dom, ingredientes + porciones en gramos)
Sección 3: Instrucciones de preparación
Sección 4: Protocolo de transición (7 días — solo si has_transition_protocol=True)
Sección 5: Sustitutos aprobados (pre-approved set)
```

## agent_traces — Append-Only

```
Cada generación de plan crea una traza:
  - trace_id: UUID
  - pet_id: UUID (anónimo — no nombre ni especie)
  - model_used: str
  - tokens_in: int
  - tokens_out: int
  - latency_ms: int
  - result: "success" | "failed"
  - created_at: datetime

Regla: SOLO INSERT — nunca UPDATE sobre trazas existentes.
Correcciones = nueva traza con reference a la original.
```

## Casos de Prueba Críticos

- [ ] Golden case Sally: RER ≈ 396 kcal, DER ≈ 534 kcal (±0.5) — BLOQUEANTE
- [ ] Plan sano → status ACTIVE directo (sin HITL)
- [ ] Plan con condición → status PENDING_VET
- [ ] LLMRouter con 3 condiciones → siempre `claude-sonnet-4-5`
- [ ] Tóxico en output del LLM → plan rechazado, error controlado
- [ ] Ajuste dentro del substitute set → ACTIVE
- [ ] Ajuste fuera del substitute set → PENDING_VET
- [ ] Vet aprueba plan temporal_medical con review_date → ACTIVE
- [ ] Vet devuelve sin comentario → 422
- [ ] agent_traces: INSERT, no UPDATE
- [ ] Free tier intenta segundo plan (no en mismo mes) → 403

## Referencias

- Spec: `aidlc-docs/inception/units/unit-04-plan-service.md`
- ADR-019: LLM routing por tier + override clínico
- ADR-020: estructura 5 secciones del plan
- ADR-022: async jobs con ARQ
- Business logic model: `_shared/business-logic-model.md`
