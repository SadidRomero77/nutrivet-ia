# Fase Operations

**Propósito**: Deploy, monitoreo, respuesta a incidentes y mantenimiento continuo del sistema en producción.

---

## Cuándo Estás en Operations

- Desplegando a staging o producción.
- Monitoreando métricas de salud y calidad clínica.
- Respondiendo a incidentes (P0/P1/P2/P3).
- Actualizando listas de alimentos tóxicos o restricciones médicas.
- Ejecutando evals del agente LLM.
- Actualizando el modelo LLM o el LLM routing.

## Infraestructura

```
Hetzner CPX31 + Coolify (ver ADR-022)
  ├── dev     → local docker-compose
  ├── staging → rama develop → GitHub Actions CI → Coolify webhook → staging.api.nutrivet.app
  └── prod    → rama main → GitHub Actions CI → aprobación manual → Coolify webhook → api.nutrivet.app

GitHub Actions CI/CD:
  PR abierto   → ruff + bandit + safety + pytest + caso Sally
  Merge a develop → quality gates → Coolify deploy staging (automático)
  Merge a main    → quality gates → Coolify deploy prod (aprobación manual requerida)
```

## Métricas Clave

| Categoría | Métrica | Umbral Normal |
|-----------|---------|---------------|
| Performance | `plan_generation_p95` | < 30s |
| Calidad clínica | `toxic_food_bypass_rate` | 0% siempre |
| HITL | `hitl_skip_rate` (con condición) | 0% siempre |
| LLM | `llm_fallback_rate` | < 10% |
| OCR | `ocr_success_rate` | ≥ 85% |
| Auth | `jwt_refresh_failure_rate` | < 0.1% |
| DB | `query_p99` | < 200ms |

## North Star Metric

> "Mascotas con plan nutricional activo y seguimiento ≥ 30 días"

Plan ACTIVE + generado hace ≥30 días + owner interactuó en los últimos 7 días.

Targets: Mes 1: 10 · Mes 3: 80 · Mes 6: 300 · Mes 12: 1.000

## Evals del Agente LLM

Correr evals cuando:
- Se cambia un prompt del agente.
- Se cambia el modelo LLM o el routing.
- Se agrega/modifica una tool de LangGraph.
- Antes de cada release.
- Cuando un test falla en producción.

Usar el skill `eval-runner` de Claude Code.

## Reglas de Steering para Esta Fase

Ver `.claude/rules/03-operations.md`

## Referencia

- Procedimientos de incidentes → `RUNBOOK.md`
- Pre-release checklist → `SHIPPING-CHECKLIST.md`
- Quality gates → `tests/quality-gates.md`
