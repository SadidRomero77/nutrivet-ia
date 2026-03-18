# Checklist de Salida — Fase Inception

Todos los items deben estar marcados antes de pasar a Construction.

---

## Requisitos

- [ ] Existe `requirements/[feature].md` con problema, motivación clínica y criterios de aceptación.
- [ ] El requisito está referenciado en `specs/prd.md` o tiene justificación de por qué no.
- [ ] No contradice `domain/invariants.md`.
- [ ] No contradice `.claude/rules/00-constitution.md`.

## Domain Model

- [ ] Todos los términos nuevos están en `domain/ubiquitous-language.md`.
- [ ] Si hay nueva entidad: documentada en `domain/aggregates/` con invariantes y domain events.
- [ ] Si cruza bounded contexts: `domain/bounded-contexts.md` actualizado.
- [ ] Si hay nueva regla médica o de toxicidad: validada por Lady Carolina Castañeda (MV).

## Diseño Técnico

- [ ] Existe `designs/[feature].md` con contrato API, capas afectadas, cambios de DB.
- [ ] Si hay cambio en DB: scope de migración Alembic definido.
- [ ] Si hay cambio en agent/LLM: tool spec actualizada en `specs/tool-specs/`.
- [ ] Si hay decisión arquitectural significativa: ADR creado en `decisions/`.

## Comportamientos (BDD)

- [ ] Al menos un escenario Gherkin (happy path) en `behaviors/`.
- [ ] Al menos un escenario edge case clínico.
- [ ] Si afecta el Caso Sally: verificar que `behaviors/golden-cases/sally.feature` sigue siendo válido.

## User Stories

- [ ] User stories en `ai-dlc/phases/inception/user-stories/` con criterios de aceptación.
- [ ] Formato: `Como [rol], quiero [acción], para [beneficio]`.

## Aprobaciones

- [ ] Sadid Romero aprueba el diseño técnico.
- [ ] Lady Carolina Castañeda aprueba si hay cambios en reglas clínicas o nutricionales.
