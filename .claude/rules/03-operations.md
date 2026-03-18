# Reglas de Steering — Fase Operations

Estas reglas aplican al deploy, monitoreo, incidentes y mantenimiento.

---

## Logs — Formato y Restricciones

```json
{
  "timestamp": "ISO8601",
  "level": "INFO|WARNING|ERROR|CRITICAL",
  "service": "nutrivet-backend",
  "trace_id": "uuid",
  "event": "plan_generated",
  "pet_id": "uuid-anónimo",
  "llm_model": "gpt-4o",
  "latency_ms": 1234,
  "tokens_used": 850
}
```

**NUNCA** incluir en logs: nombres de mascotas, nombres de owners, condiciones médicas en texto plano, especies, pesos. Solo IDs anónimos (UUIDs).

## Métricas de Salud — Revisar en Cada Deploy

| Métrica | Umbral Alerta |
|---------|--------------|
| `plan_generation_p95` | > 30s → P1 |
| `toxic_food_bypass_rate` | > 0% → P0 INMEDIATO |
| `hitl_skip_rate` (mascotas con condición) | > 0% → P0 INMEDIATO |
| `llm_fallback_rate` | > 10% → P2 |
| `ocr_success_rate` | < 85% → P2 |

## Incidentes — Clasificación

- **P0**: tóxico en plan generado, HITL omitido para mascota con condición médica, datos médicos expuestos. → Rollback inmediato, notificar Sadid + Lady Carolina.
- **P1**: plan generation > 30s, auth failure rate > 1%, LLM principal caído. → Fix en < 4h.
- **P2**: OCR < 85%, LLM fallback activo. → Fix en < 24h.
- **P3**: UI degradada, notificaciones push con retraso. → Fix en < 72h.

Ver `RUNBOOK.md` para procedimientos detallados.

## Deploy — Checklist Pre-Release

1. Todos los Quality Gates G1-G8 en verde (`tests/quality-gates.md`).
2. `bandit -r app/` → 0 issues HIGH/MEDIUM.
3. `safety check` → 0 CVEs críticas.
4. Caso Sally pasa con ±0.5 kcal: `pytest tests/domain/test_nrc_calculator.py::test_sally_golden_case`.
5. Golden set 60 casos → 0 tóxicos en planes.
6. ≥ 18/20 planes aprobados por Lady Carolina.

**Sin estos gates en verde, no hay deploy.** Ver `SHIPPING-CHECKLIST.md`.

## agent_traces — Inmutabilidad

- Las trazas son append-only. **Sin UPDATE** sobre trazas existentes una vez insertadas.
- Solo INSERT. Las correcciones se registran como nueva traza con referencia a la original.
- Retención mínima: 90 días en caliente en PostgreSQL, archivado a Cloudflare R2 vía purge job mensual.

## Mantenimiento de Listas Médicas

- `TOXIC_DOGS` y `TOXIC_CATS`: revisión semestral con Lady Carolina.
- `RESTRICTIONS_BY_CONDITION`: revisión cuando se agrega nueva condición médica.
- Toda actualización → nuevo commit con mensaje: `security: update toxic_foods - [razón]`.

## Escalado y Costos

- Uvicorn workers: 2 workers en CPX31 (ajustar si p95 > 20s — incrementar workers o upgrade VPS).
- ARQ: `max_jobs=10` por worker — incrementar `max_jobs` o agregar réplica del contenedor worker si cola > 50 jobs pendientes.
- OpenRouter: monitorear costo por plan — alerta si > $0.10 USD/plan. 3+ condiciones siempre → claude-sonnet-4-5.
- Hetzner: CPX31 → CPX41 → CCX33 si CPU sostenido > 80% en ventana de 15 min. El upgrade es online (< 5 min downtime).
