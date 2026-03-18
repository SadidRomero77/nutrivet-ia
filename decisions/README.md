# Architecture Decision Records (ADRs)

Registro de todas las decisiones arquitecturales significativas de NutriVet.IA.
Formato: MADR (Markdown Architectural Decision Records).

---

## Índice

| ADR | Título | Estado |
|-----|--------|--------|
| [ADR-001](ADR-001-langgraph-orchestrator.md) | LangGraph como orquestador del agente | ✅ Aceptado |
| [ADR-002](ADR-002-toxicity-hardcoded.md) | Toxicidad y restricciones médicas hard-coded en domain layer | ✅ Aceptado |
| ~~[ADR-003](ADR-003-aws-lambda.md)~~ | ~~AWS Lambda + API Gateway para deployment~~ | ⚠️ Superseeded por ADR-022 |
| [ADR-004](ADR-004-jwt-auth.md) | JWT access 15min + refresh token rotativo | ✅ Aceptado |
| [ADR-005](ADR-005-flutter-mobile.md) | Flutter para aplicación mobile (iOS + Android) | ✅ Aceptado |
| [ADR-006](ADR-006-postgresql-alembic.md) | PostgreSQL + Alembic para base de datos | ✅ Aceptado |
| [ADR-007](ADR-007-bcs-scale.md) | BCS escala 1-9 con selector visual | ✅ Aceptado |
| [ADR-008](ADR-008-two-modalities.md) | Dos modalidades de plan (Natural/Concentrado) | ✅ Aceptado |
| [ADR-009](ADR-009-sponsors.md) | Sponsors con tag "Patrocinado" obligatorio — máximo 3 | ✅ Aceptado |
| [ADR-010](ADR-010-ocr-only-nutritional.md) | OCR solo acepta tabla nutricional o ingredientes | ✅ Aceptado |
| [ADR-011](ADR-011-freemium.md) | Modelo freemium (Free/Básico/Premium/Vet) | ✅ Aceptado |
| [ADR-012](ADR-012-latam-food-database.md) | Base de datos de alimentos LATAM-wide en español | ✅ Aceptado |
| ~~[ADR-013](ADR-013-llm-routing.md)~~ | ~~LLM routing por número de condiciones médicas~~ | ⚠️ Superseeded por ADR-019 |
| [ADR-014](ADR-014-size-5-categories.md) | 5 categorías de talla para perros con rangos de peso | ✅ Aceptado |
| [ADR-015](ADR-015-cat-activity-indoor-outdoor.md) | Actividad de gatos: indoor/indoor_outdoor/outdoor | ✅ Aceptado |
| [ADR-016](ADR-016-no-rejected-state.md) | Sin estado RECHAZADO en el ciclo de vida del plan | ✅ Aceptado |
| [ADR-017](ADR-017-pdf-export.md) | Exportación PDF y compartición social de planes | ✅ Aceptado |
| [ADR-018](ADR-018-vet-as-plan-creator.md) | Vet crea plan directamente desde dashboard clínico | ✅ Aceptado |
| [ADR-019](ADR-019-openrouter-llm-routing.md) | OpenRouter como proveedor unificado — routing por tier + override clínico | ✅ Aceptado |
| [ADR-020](ADR-020-interactive-plan-presentation.md) | Plan nutricional visual interactivo por secciones | ✅ Aceptado |
| [ADR-021](ADR-021-fluid-conversational-agent.md) | Agente conversacional fluido (no chatbot) | ✅ Aceptado |
| [ADR-022](ADR-022-hetzner-coolify-infrastructure.md) | Hetzner + Coolify como infraestructura de despliegue (reemplaza AWS) | ✅ Aceptado |

---

## Cómo crear un nuevo ADR

1. Copiar la plantilla de cualquier ADR existente.
2. Asignar número secuencial: `ADR-018`.
3. Completar todos los campos: contexto, opciones consideradas, decisión, consecuencias.
4. Cambiar estado a `Propuesto` hasta ser aprobado.
5. Agregar al índice de este README.

**Cuándo crear un ADR**: Toda decisión que sea difícil de revertir, que afecte múltiples capas, o que implique trade-offs tecnológicos significativos.
