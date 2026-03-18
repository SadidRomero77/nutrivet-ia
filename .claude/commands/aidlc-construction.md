# AI-DLC Construction Skill

Ejecuta la fase **Construction** del AI-DLC para NutriVet.IA.
Solo ejecutar después de que `/aidlc` haya completado la fase Inception con Gate 5 aprobado.

---

## Verificación Previa

1. Lee `aidlc-docs/aidlc-state.md` — confirma que Inception está en ✅.
2. Lee `aidlc-docs/inception/application-design/unit-of-work.md` — carga las unidades.
3. Si Inception no está completa → informa al usuario y detente.

---

## Por Cada Unidad de Trabajo (en orden de dependencias)

### PASO C1 — Functional Design

Crea: `aidlc-docs/construction/{unit-name}/functional-design/`

Archivos a generar:
- `business-logic-model.md` — lógica de negocio agnóstica de tecnología
- `business-rules.md` — reglas hard-coded, validaciones, guardarraíles
- `domain-entities.md` — entidades específicas de la unidad (referencia a `domain/`)
- `frontend-components.md` — si la unidad tiene UI (solo para `mobile-app`)

**GATE C1**: Presenta artefactos → espera A (cambios) o B (aprobar).

### PASO C2 — NFR Requirements

Evalúa para la unidad:
- Escalabilidad (usuarios concurrentes objetivo)
- Performance (SLAs: latencia p95, throughput)
- Disponibilidad (uptime target)
- Seguridad (OWASP Top 10, Ley 1581/2012)
- Stack tecnológico (confirmar o ajustar)
- Mantenibilidad (cobertura de tests, linting)

**GATE C2**: Presenta análisis NFR → espera aprobación.

### PASO C3 — Infrastructure Design

Mapea componentes lógicos a servicios reales:
- Compute: FastAPI + Uvicorn (Docker en Hetzner CPX31) + ARQ worker (ver ADR-022)
- Storage: PostgreSQL 16 (Docker) + Cloudflare R2 para PDFs/imágenes
- LLM: OpenRouter (proveedor unificado) — routing por tier + override clínico (ver ADR-019)
- Queue: ARQ (Redis) — async job queue para generación de planes
- Monitoring: Sentry + structlog JSON + Coolify logs

**GATE C3**: Presenta diseño infra → espera aprobación.

### PASO C4 — Code Generation Plan

Crea: `aidlc-docs/construction/plans/{unit-name}-code-generation-plan.md`

Plan numerado con checkboxes:
- [ ] Estructura de carpetas
- [ ] Tests del domain layer (RED phase — TDD)
- [ ] Implementación domain/ (GREEN phase)
- [ ] Casos de uso en application/
- [ ] Infraestructura (repositories, LLM clients)
- [ ] Endpoints presentation/
- [ ] Migraciones Alembic (si aplica)
- [ ] Flutter components (si aplica)
- [ ] BDD → tests automatizados

**GATE C4**: Presenta plan → espera aprobación antes de generar código.

### PASO C5 — Code Generation (Ejecución)

Ejecuta el plan aprobado paso a paso:
- Actualiza checkboxes al completar cada paso
- Código va en `backend/` o `mobile/` — NUNCA en `aidlc-docs/`
- Sigue reglas de `.claude/rules/02-construction.md`
- Usa `gitnexus_impact` antes de editar `domain/`

### PASO C6 — Build and Test

Crea: `aidlc-docs/construction/build-and-test/{unit-name}/`
- Instrucciones de build
- Guía de ejecución de tests (unitarios, integración, BDD)
- Reporte de cobertura
- Estado de Quality Gates G1-G8 relevantes

**GATE C6 (Final de unidad)**: Confirma que la unidad está lista → procede a la siguiente.

---

## REGLAS

- Orden de unidades: `domain-core` → `auth-service` → `pet-service` → `plan-service` → `agent-core` → `scanner-service` → `conversation-service` → `export-service` → `mobile-app`
- No avanzar a siguiente unidad sin Gate aprobado de la actual
- Actualizar `aidlc-docs/aidlc-state.md` al completar cada unidad
- Registrar en `aidlc-docs/audit.md` con timestamp ISO 8601
