# Fase Inception

**Propósito**: Definir QUÉ construir y POR QUÉ, antes de escribir una sola línea de código de producción.

---

## Cuándo Estás en Inception

- Diseñando una nueva feature o módulo.
- Modelando el dominio (DDD).
- Escribiendo especificaciones técnicas.
- Tomando decisiones de arquitectura (ADRs).
- Escribiendo escenarios Gherkin (BDD) para validar comprensión.

## Qué Produce Inception

| Artefacto | Ubicación | Herramienta |
|-----------|-----------|-------------|
| Requisito funcional | `ai-dlc/phases/inception/requirements/` | `/specify` |
| Diseño técnico | `ai-dlc/phases/inception/designs/` | `/plan` |
| User stories | `ai-dlc/phases/inception/user-stories/` | Manual |
| ADR (si aplica) | `decisions/` | Manual |
| Escenarios Gherkin | `behaviors/` | De /plan |
| Actualización DDD | `domain/` | Manual |

## Flujo de Trabajo en Inception

```
Nueva Feature
     │
     ▼
/specify [feature]
  → Capturar QUÉ y POR QUÉ
  → Verificar contra domain/invariants.md
  → Verificar contra .claude/rules/00-constitution.md
     │
     ▼
Modelar en DDD (si nueva entidad)
  → Actualizar domain/ubiquitous-language.md
  → Actualizar domain/bounded-contexts.md si cruza contextos
  → Crear/actualizar domain/aggregates/[aggregate].md
     │
     ▼
/plan [feature]
  → Diseño técnico completo
  → Contrato API
  → Impacto en DB
  → Escenarios Gherkin base
     │
     ▼
Crear ADR (si decisión arquitectural significativa)
  → decisions/ADR-[N]-[nombre].md
     │
     ▼
Checklist de salida (inception/checklist.md)
```

## Reglas de Steering para Esta Fase

Ver `.claude/rules/01-inception.md`

## Participantes

- **Sadid Romero** — AI Engineer, decisiones técnicas
- **Lady Carolina Castañeda** — validación clínica de restricciones y reglas médicas
- **Agente IA** — asistencia en modelado DDD, escritura de specs, análisis de impacto
