# AI-DLC — AI-Driven Development Lifecycle

NutriVet.IA implementa el **AI-Driven Development Lifecycle (AI-DLC)** de AWS, integrado con **Spec-Driven Development (SDD)** de Microsoft y las metodologías **DDD + BDD + TDD**.

---

## Filosofía

> "El agente IA ejecuta tareas rutinarias. El humano decide estrategia y valida clínicamente."

El humano es responsable de:
- Decisiones clínicas (Lady Carolina Castañeda, MV)
- Decisiones arquitecturales (Sadid Romero, AI Engineer)
- Aprobación de planes para mascotas con condición médica (vet firmante)

El agente IA es responsable de:
- Generación de planes nutricionales (con guardarraíles deterministas)
- Búsqueda de información, análisis de impacto, generación de código
- Ejecución de tareas dentro de los límites de la Constitution

---

## Las 3 Fases

```
┌─────────────────────────────────────────────────────────────┐
│  INCEPTION          CONSTRUCTION          OPERATIONS        │
│                                                             │
│  /specify           /tasks (TDD)          Deploy + Monitor  │
│  DDD Modeling       BDD → Tests           Incident Mgmt     │
│  /plan              Code Implementation   Evals + Drift     │
│  ADRs               CI/CD                 Maintenance       │
│                                                             │
│  Output:            Output:               Output:           │
│  domain/            backend/ + mobile/    Metrics + Traces  │
│  specs/             tests/                RUNBOOK incidents  │
│  behaviors/         decisions/ (nuevos)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Cómo Navegar Este Repositorio

### Para una Nueva Feature

```
1. /specify [feature]   → ai-dlc/phases/inception/requirements/
2. /plan [feature]      → ai-dlc/phases/inception/designs/
3. /tasks [feature]     → ai-dlc/phases/construction/tasks/
4. Implementar TDD      → backend/ + tests/
5. BDD scenarios        → behaviors/
6. Deploy checklist     → ai-dlc/phases/operations/checklist.md
```

### Para Entender el Dominio

```
domain/ubiquitous-language.md     ← Glosario del dominio
domain/bounded-contexts.md        ← Mapa de contextos
domain/aggregates/                ← Aggregates: PetProfile, NutritionPlan, UserAccount
domain/invariants.md              ← Reglas de negocio no negociables
domain/domain-events.md           ← Eventos que cruzan bounded contexts
```

### Para Verificar Comportamientos

```
behaviors/                        ← Escenarios Gherkin por flujo
behaviors/golden-cases/sally.feature ← Golden case clínico de referencia
```

### Para Verificar Calidad

```
tests/strategy.md                 ← Qué testear y en qué orden
tests/quality-gates.md            ← G1-G8 con criterios de aceptación
tests/fixtures/sally.json         ← Fixture del golden case
```

### Para Tomar Decisiones

```
decisions/                        ← ADRs (Architecture Decision Records)
.claude/rules/00-constitution.md  ← Principios no negociables
```

---

## Steering Rules Para Agentes IA

| Archivo | Cuándo Aplica |
|---------|---------------|
| `.claude/rules/00-constitution.md` | Siempre — principios no negociables |
| `.claude/rules/01-inception.md` | Fase de diseño y especificación |
| `.claude/rules/02-construction.md` | Fase de implementación |
| `.claude/rules/03-operations.md` | Fase de deploy y operación |

---

## Integración de Metodologías

```
SDD (Spec-Driven)  →  Estructura el CUÁNDO escribir qué artefacto
AI-DLC (AWS)       →  Define las FASES y las reglas de steering
DDD                →  Define QUÉ existe en el dominio y cómo se llama
BDD                →  Define CÓMO se comporta el sistema externamente
TDD                →  Define CÓMO se verifica que cada pieza funciona
```
