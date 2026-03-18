# Reglas de Steering — Fase Inception

Estas reglas aplican cuando el agente está en la fase de planificación, diseño y especificación.

---

## Lenguaje del Dominio

- Usar siempre el vocabulario de `domain/ubiquitous-language.md`.
- Si un término no existe en el glosario, proponer su adición antes de usarlo.
- Código en inglés. Comentarios y documentación en español.

## Antes de Diseñar Cualquier Feature

1. Verificar que el requisito existe en `specs/prd.md` o crear un issue documentado.
2. Consultar `domain/bounded-contexts.md` para identificar qué contexto(s) están involucrados.
3. Verificar conflictos con `domain/invariants.md` — si hay conflicto, escalar antes de continuar.
4. Verificar `decisions/` — si hay un ADR que afecte la decisión, respetarlo.

## Al Escribir Especificaciones

- Toda feature nueva requiere al menos un escenario Gherkin en `behaviors/`.
- Los escenarios Gherkin deben cubrir: happy path + al menos un edge case clínico.
- El Caso Sally (`behaviors/golden-cases/sally.feature`) es el golden case — nunca modificarlo sin validación de Lady Carolina.
- Usar el formato: `Given [contexto] / When [acción] / Then [resultado esperado]`.

## Al Tomar Decisiones de Arquitectura

- Toda decisión arquitectural significativa → crear un ADR en `decisions/`.
- Formato: MADR (Markdown Architectural Decision Records).
- Consultar ADRs existentes antes de proponer una alternativa tecnológica.

## Al Definir Nuevas Entidades de Dominio

- Seguir el patrón de `domain/aggregates/` — cada aggregate en su propio archivo.
- Definir: entidad raíz, invariantes, value objects, domain events que emite.
- Toda entidad médica (condición, restricción, toxicidad) requiere validación de Lady Carolina antes de implementar.

## Checklist de Salida de Inception

Verificar `ai-dlc/phases/inception/checklist.md` antes de declarar Inception completa.
