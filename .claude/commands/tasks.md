# /tasks — Descomponer en Chunks Implementables

**Propósito**: Convertir el diseño técnico en tareas ordenadas y ejecutables por el agente.

## Instrucciones al Agente

Cuando el desarrollador ejecuta `/tasks [nombre-feature]`:

1. Verificar que existe `ai-dlc/phases/inception/designs/[nombre-feature].md`.
2. Crear `ai-dlc/phases/construction/tasks/[nombre-feature]-tasks.md`:

```markdown
# Tasks: [nombre-feature]

## Orden de Implementación

### TASK-1: Tests del domain layer
**Tipo**: TDD — escribir PRIMERO
**Archivo**: `tests/domain/test_[feature].py`
**Criterio de completitud**: Tests corren en rojo (red phase de TDD)

### TASK-2: Implementación domain/
**Tipo**: Implementation
**Archivo(s)**: `backend/domain/[...]`
**Criterio de completitud**: Tests de TASK-1 pasan (green phase)

### TASK-3: Caso(s) de uso en application/
**Tipo**: Implementation
**Archivo(s)**: `backend/application/use_cases/[...]`
**Criterio de completitud**: Integración domain-application funciona

### TASK-4: Infraestructura (si aplica)
**Tipo**: Implementation
**Archivo(s)**: `backend/infrastructure/[...]`
**Criterio de completitud**: [criterio específico]

### TASK-5: Endpoint en presentation/
**Tipo**: Implementation
**Archivo(s)**: `backend/presentation/routers/[...]`
**Criterio de completitud**: Contrato API del /plan pasa tests de integración

### TASK-6: Migración DB (si aplica)
**Tipo**: Migration
**Comando**: `alembic revision --autogenerate -m "[nombre]"`
**Criterio de completitud**: Migración aplicada en dev, revisada, sin data loss

### TASK-7: Feature flag Flutter (si aplica)
**Tipo**: Mobile
**Archivo(s)**: `mobile/lib/features/[...]`
**Criterio de completitud**: Feature funciona en modo offline-first

### TASK-8: Gherkin → tests automatizados
**Tipo**: BDD
**Archivo(s)**: `tests/bdd/[feature]/`
**Criterio de completitud**: Todos los escenarios de behaviors/ pasan

## Definition of Done

- [ ] Cobertura domain/ ≥ 80%
- [ ] `ruff check .` → 0 errores
- [ ] `bandit -r app/` → 0 HIGH/MEDIUM
- [ ] Caso Sally sigue pasando (±0.5 kcal)
- [ ] `gitnexus_detect_changes` ejecutado — impacto documentado
- [ ] PR description incluye link al /specify y /plan
```
