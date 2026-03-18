# /specify — Capturar QUÉ y POR QUÉ

**Propósito**: Documentar requisitos funcionales y motivación de una feature ANTES de diseñar la solución técnica.

## Instrucciones al Agente

Cuando el desarrollador ejecuta `/specify [nombre-feature]`:

1. Crear archivo en `ai-dlc/phases/inception/requirements/[nombre-feature].md`.
2. Usar la siguiente plantilla:

```markdown
# Requisito: [nombre-feature]

## Problema que resuelve
[Descripción del problema desde la perspectiva del usuario/veterinario]

## Usuarios afectados
- [ ] Owner (dueño de mascota)
- [ ] Vet (veterinario)
- [ ] Admin

## Motivación clínica
[Por qué esto es relevante desde el punto de vista veterinario — validar con Lady Carolina si aplica]

## Comportamientos esperados (Gherkin)
[Al menos un escenario — completar en /plan]

## Criterios de aceptación
- [ ] [criterio 1]
- [ ] [criterio 2]

## Lo que NO incluye
[Explicit exclusions — qué queda fuera del scope]

## Referencia PRD
Sección: [referencia a specs/prd.md]
```

3. Verificar que el requisito no contradice `domain/invariants.md` ni `.claude/rules/00-constitution.md`.
4. Si hay contradicción → reportar al desarrollador antes de continuar.
