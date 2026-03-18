# /plan — Capturar CÓMO

**Propósito**: Diseño técnico de una feature. Solo ejecutar después de `/specify`.

## Instrucciones al Agente

Cuando el desarrollador ejecuta `/plan [nombre-feature]`:

1. Verificar que existe `ai-dlc/phases/inception/requirements/[nombre-feature].md`.
2. Crear `ai-dlc/phases/inception/designs/[nombre-feature].md` con la siguiente plantilla:

```markdown
# Diseño Técnico: [nombre-feature]

## Bounded Context(s) Involucrados
[Referencias a domain/bounded-contexts.md]

## Capa(s) Afectadas
- [ ] domain/
- [ ] application/
- [ ] infrastructure/
- [ ] presentation/

## Nuevas Entidades / Cambios a Entidades Existentes
[Aggregates, entities, value objects afectados]

## Nuevos Domain Events
[Eventos que esta feature emite]

## Contrato de API
### Endpoint
`METHOD /api/v1/[path]`

### Request (Pydantic)
```python
class [FeatureRequest](BaseModel):
    ...
```

### Response (Pydantic)
```python
class [FeatureResponse](BaseModel):
    ...
```

## Cambios de Base de Datos
[Nuevas tablas, columnas, índices — requieren migración Alembic]

## Impacto en Agent/LLM
[Si afecta tools del agente, LLM routing, prompts]

## Escenarios Gherkin (completar en behaviors/)
[Copiar y completar desde /specify]

## Decisiones de Diseño
[Alternativas consideradas y por qué se eligió esta]

## ADR requerido
- [ ] Sí → crear en decisions/
- [ ] No (cambio interno, sin impacto arquitectural)

## Riesgos
[Posibles problemas técnicos o clínicos]
```

3. Si hay cambios en `domain/`, usar `gitnexus_impact` para verificar blast radius.
4. Si impact depth ≥ 3 → reportar al desarrollador y detener.
