# Plan: NFR Requirements — Unit 04: plan-service

**Unidad**: unit-04-plan-service
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del plan-service

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| Plan generation p95 | < 30s end-to-end (async via ARQ) | LLM call es el cuello de botella |
| POST /v1/plans/generate | < 200ms | Solo encola job en Redis — no espera LLM |
| GET /v1/plans/jobs/{job_id} | < 50ms p95 | DB lookup del job status |
| GET /v1/plans/{plan_id} | < 100ms p95 | Join plans + plan_sections |
| HITL endpoints (approve/return) | < 100ms p95 | Estado + notify |
| GET /v1/plans/{plan_id}/substitutes | < 50ms p95 | Lookup substitute_sets |

**Alerta**: si `plan_generation_p95 > 30s` → P1 — investigar latencia de OpenRouter.

### Seguridad y Datos

**Prompts a LLMs externos**:
- Solo `pet_id` (UUID anónimo) en prompts — NUNCA nombre, especie, condiciones en texto plano.
- Usar IDs para referenciar condiciones: `cond_01`, `cond_05`... no `diabético`, `renal`.
- El sistema prompt incluye las restricciones sin identificar al paciente por nombre.

**agent_traces**:
- Inmutables post-generación: solo INSERT, sin UPDATE.
- La tabla `agent_traces` no tiene trigger ni endpoint que permita UPDATE.
- Retención: 90 días en PostgreSQL, luego archivado a R2 via purge job mensual.

**Monitoreo crítico**:
- `toxic_food_bypass_rate > 0%` → P0 INMEDIATO — rollback.
- `hitl_skip_rate > 0%` para mascotas con condición médica → P0 INMEDIATO.

### Confiabilidad

**LLM Fallback**:
```
Timeout 30s → retry × 2 (backoff exponencial: 2s, 4s)
  → si aún falla → modelo fallback (tier inferior)
  → si fallback falla → error controlado con mensaje al usuario
  → job status → FAILED con error_code y mensaje accionable
```

**Retry logic**: máximo 3 intentos total (1 + 2 retries) antes de fallback.

**Idempotencia**: si el mismo `job_id` ya existe en DB → retornar el job existente (no crear duplicado).

### Mantenibilidad

- Cobertura mínima: **80%** en `application/` y `domain/` relacionados.
- Golden case Sally debe estar en CI como test bloqueante.
- Type hints obligatorios. Docstrings en español.
- Ruff + bandit: 0 errores antes de PR.

## Checklist NFR plan-service

- [ ] Golden case Sally: `pytest tests/domain/test_nrc_calculator.py::test_sally_golden_case` pasa (±0.5 kcal)
- [ ] `toxic_food_bypass_rate == 0%` en golden set de 60 casos
- [ ] LLM override: 3+ condiciones → siempre `claude-sonnet-4-5` (test determinista)
- [ ] Prompts no contienen nombre ni especie en texto plano (test de sanitización)
- [ ] agent_traces: no existe endpoint PATCH /traces — verificar en OpenAPI spec
- [ ] job polling: status QUEUED → PROCESSING → READY en test de integración
- [ ] Fallback activo: mock OpenRouter timeout → job FAILED con mensaje claro
- [ ] Cobertura ≥ 80%
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM

## Referencias

- Global: `_shared/nfr-requirements.md`
- ADR-019: LLM routing
- ADR-022: async ARQ jobs
- Constitution: REGLA 6 (datos en prompts), REGLA 5 (LLM routing)
- Operations rules: `03-operations.md` (métricas P0)
