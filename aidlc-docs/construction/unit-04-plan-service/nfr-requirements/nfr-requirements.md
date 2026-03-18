# NFR Requirements — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Plan Service

### NFR-PLAN-01: Plan Generation p95 < 30s (Alerta P1)
- El tiempo de generación end-to-end (enqueue → job completed) debe ser < 30s en p95.
- Medido desde `plan_job.enqueued_at` hasta `plan_job.completed_at`.
- Alerta P1 si p95 supera 30s → investigar LLM latency, ARQ queue depth.

### NFR-PLAN-02: 0% Tóxicos en Planes (Quality Gate G1)
- Zero tolerancia: ningún plan generado puede contener ingredientes de TOXIC_DOGS / TOXIC_CATS.
- Golden set de 60 casos → 0 tóxicos.
- Si un tóxico se detecta en un plan post-generación → P0 inmediato, rollback, auditoría.

### NFR-PLAN-03: 100% Restricciones Médicas (Quality Gate G2)
- Todas las restricciones de las 13 condiciones deben aplicarse.
- Test matrix: 13 condiciones × ingredientes prohibidos = 0 bypass.

### NFR-PLAN-04: AgentTrace Append-Only
- No existe ningún UPDATE en `agent_traces` table.
- Verificado por: trigger en PostgreSQL + ausencia de método `update()` en el repositorio.
- Test: intentar UPDATE → error de DB.

### NFR-PLAN-05: LLM Routing Correcto
- 3+ condiciones → claude-sonnet-4-5 SIEMPRE, independientemente del tier.
- Verificado en test: `LLMRouter.resolve_model()` con 3 condiciones + tier "free" → "anthropic/claude-sonnet-4-5".

### NFR-PLAN-06: Solo UUIDs en Prompts
- Los prompts al LLM no contienen nombre de mascota, nombre de owner, ni especie.
- Verificado en test: inspeccionar el prompt generado — no debe contener PII.

### NFR-PLAN-07: Cobertura de Tests ≥ 80%
- `pytest --cov=app/application/plans --cov=app/workers tests/plans/ --cov-fail-under=80`
- Tests obligatorios: generación happy path, tóxico detectado (stop), restricción violada (re-prompt), HITL routing, firma vet, devolución con comentario.

### NFR-PLAN-08: Disclaimer Obligatorio Inmutable
- El campo `disclaimer` no puede ser modificado post-creación.
- El disclaimer fijo: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
- Verificado en test: intentar modificar disclaimer → error de dominio.

### NFR-PLAN-09: Timeout del Worker
- El worker ARQ tiene `job_timeout=120` segundos.
- Si el job excede 120s → `status = "failed"` automáticamente por ARQ.
- Previene jobs zombies en Redis.

### NFR-PLAN-10: Notificación Push en Eventos de Plan
- Plan listo (completed) → push al owner.
- Plan aprobado por vet → push al owner.
- Plan devuelto por vet → push al owner con comentario.
- Implementado con FCM (Firebase Cloud Messaging) o fallback a APNS directo.
