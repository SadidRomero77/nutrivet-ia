# Behaviors — BDD (Behavior-Driven Development)

Escenarios Gherkin que documentan el comportamiento esperado del sistema desde la perspectiva del usuario/veterinario.

---

## Filosofía

> "El código debe hacer lo que los escenarios dicen. Los escenarios son el contrato."

Los escenarios Gherkin sirven como:
1. **Documentación viva** — siempre sincronizada con el código real.
2. **Criterios de aceptación** — qué debe pasar para que una feature esté lista.
3. **Tests automatizados** — cada `.feature` tiene un test `pytest-bdd` correspondiente en `tests/bdd/`.

---

## Flujos Documentados

| Archivo | Flujo | Prioridad |
|---------|-------|-----------|
| `plan-generation.feature` | Generación de plan nutricional (Tipo A y B) | CRÍTICA |
| `hitl-workflow.feature` | Revisión veterinaria de planes con condición médica | CRÍTICA |
| `medical-restrictions.feature` | Aplicación de restricciones por condición médica | CRÍTICA |
| `ocr-scanner.feature` | Escaneo de etiquetas nutricionales | ALTA |
| `conversational-agent.feature` | Consultas al agente conversacional | ALTA |
| `golden-cases/sally.feature` | Caso Sally — golden case clínico de referencia | CRÍTICA |

---

## Convención de Escritura

```gherkin
# language: es

Feature: [Nombre del flujo]
  Como [rol: owner/vet/sistema]
  Quiero [acción]
  Para [beneficio]

  Background:
    Given [precondiciones comunes a todos los escenarios]

  Scenario: [Nombre del escenario — happy path]
    Given [contexto]
    When  [acción del actor]
    Then  [resultado esperado]

  Scenario: [Nombre del escenario — edge case]
    Given [contexto específico]
    When  [acción]
    Then  [resultado]
    And   [condición adicional]
```

---

## Conexión con Tests

Cada `.feature` tiene un archivo `tests/bdd/test_[nombre].py` con los step definitions.

```bash
# Correr todos los escenarios BDD
pytest tests/bdd/ -v

# Correr el golden case Sally
pytest tests/bdd/test_sally_golden_case.py -v
```
