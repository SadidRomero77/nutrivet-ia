---
name: story-to-bdd
description: Toma una User Story (US-XX) de NutriVet.IA y genera dos artefactos Python: escenarios Gherkin para appendar al .feature existente en behaviors/ y skeletons de tests (behave steps + pytest). Respeta la estructura de features ya existente y los Quality Gates G1-G8.
tools: Read, Write, Edit, Glob
---

# Skill: story-to-bdd
> Versión: 1.0 — NutriVet.IA (Python + behave + pytest)
> Puente entre User Stories y código de tests ejecutable

## Cuándo usar este skill

- Antes de implementar una story específica (TDD: tests primero)
- Para generar el contrato BDD ejecutable de una story ya especificada
- Para añadir cobertura a `behaviors/` sin duplicar escenarios existentes

**Input requerido**: ID de story (ej. `US-01`, `US-07`)
Si no se especifica, preguntar antes de continuar.

---

## Pre-requisitos

| Recurso | Verificar antes de empezar |
|---------|---------------------------|
| `aidlc-docs/inception/user-stories/stories.md` | Fuente de la story con sus ACs |
| `behaviors/` | Ya existe — NO crear features desde cero si el archivo referenciado existe |
| `specs/prd.md` | Referencia de reglas no negociables y Quality Gates |
| `.claude/rules/00-constitution.md` | Guardarraíles que todo scenario debe respetar |

---

## PASO 1 — Leer y extraer la story

Leer `aidlc-docs/inception/user-stories/stories.md` y localizar la story por `### US-XX:`.

Extraer:
- **Enunciado**: `Como / Quiero / Para`
- **ACs**: todos los ítems `- [ ] ...`
- **Gherkin asociado**: línea `**Gherkin asociado:** behaviors/{archivo}.feature`
- **Epic**: número y nombre
- **Prioridad**: CRÍTICA / ALTA / MEDIA

Si el ID no existe en el archivo → detener e informar al usuario.

---

## PASO 2 — Mapear archivos de output

### Feature file (Gherkin)

El archivo de destino viene del campo `**Gherkin asociado:**` de la story.

| Si el archivo `behaviors/{X}.feature` | Acción |
|---------------------------------------|--------|
| Ya existe | Leerlo completo, luego **appendar** solo scenarios nuevos que no existan |
| No existe | Crearlo con el header correcto y los scenarios |

**Archivos de behaviors existentes:**
```
behaviors/
  plan-generation.feature
  hitl-workflow.feature
  medical-restrictions.feature
  ocr-scanner.feature
  conversational-agent.feature
  golden-cases/sally.feature   ← NUNCA modificar sin validación Lady Carolina
```

Si el `.feature` referenciado en la story no existe, crearlo. Si existe, NO reescribirlo — solo appendar.

### Test files (Python)

Determinar la capa correcta según el dominio de la story:

| Story toca... | Archivo pytest skeleton |
|--------------|-------------------------|
| Cálculo RER/DER, toxicidad, restricciones médicas, value objects | `tests/domain/test_{módulo}.py` |
| Auth, casos de uso, HITL workflow, plan lifecycle | `tests/application/test_{módulo}.py` |
| Endpoints FastAPI, JWT, RBAC | `tests/presentation/test_{módulo}.py` |
| OCR, LLM clients, repositorios | `tests/infrastructure/test_{módulo}.py` |

Step implementations:
```
tests/steps/{feature-file}_steps.py
```

Si el archivo ya existe → appendar solo los steps de los nuevos scenarios. No reescribir.

---

## PASO 3 — Identificar guardarraíles aplicables

Antes de generar scenarios, verificar si la story involucra alguno de estos dominios.
Si aplica → el scenario de guardarraíl es **obligatorio**, no opcional.

| Si la story toca... | Guardarraíl obligatorio |
|--------------------|------------------------|
| Generación de plan / ingredientes | **Toxicity**: alimento tóxico → siempre bloqueado (G1) |
| Mascota con condición médica | **Medical restriction**: restricción hard-coded gana al LLM (G2) |
| Generación de plan + condición médica | **HITL**: plan debe quedar en `PENDING_VET`, nunca en `ACTIVE` (Regla 4) |
| Plan generado para owner | **Disclaimer**: mensaje "NutriVet.IA es asesoría nutricional digital" presente (Regla 8) |
| Consulta conversacional | **Boundary**: consulta médica → remite al vet, no responde (Regla 9) |

---

## PASO 4 — Generar scenarios Gherkin

### Reglas de generación

**Escenarios mínimos por story:**
1. **Happy path** — el flujo exitoso principal (obligatorio)
2. **Edge case** — entrada inválida, estado límite o caso alternativo (obligatorio)
3. **Guardarraíl** — uno por cada guardarraíl aplicable (ver Paso 3)

Escenarios adicionales solo si un AC lo requiere explícitamente.

**Verificar antes de appendar**: leer los scenarios existentes en el `.feature`. Si un scenario con el mismo comportamiento ya existe, no duplicar — solo mencionar en el reporte que ya está cubierto.

**Formato Gherkin:**
```gherkin
# ─── {NOMBRE DE LA STORY} (US-XX) ────────────────────────────────────────────

Scenario: {descripción clara en español del comportamiento}
  Given {estado del sistema antes de la acción}
  When {acción concreta del actor — un solo evento}
  Then {resultado observable y verificable}
  And {resultado adicional si aplica}
```

**Calidad de los pasos:**
- `Given` → estado inicial (setup del contexto)
- `When` → una sola acción del actor
- `Then` → resultado verificable externamente (sin mencionar implementación)
- Lenguaje de negocio en español — sin términos de código (`NRCCalculator`, `frozenset`, etc.)
- `And` solo como continuación — nunca como primer paso

**Ejemplo de guardarraíl de toxicidad:**
```gherkin
Scenario: Ingrediente tóxico para perros es rechazado en cualquier plan (G1)
  Given una mascota de especie "perro"
  And el plan incluye el ingrediente "uvas"
  When el sistema verifica seguridad alimentaria
  Then el ingrediente "uvas" es rechazado con error de toxicidad
  And el plan no puede pasar a estado "ACTIVE" con ese ingrediente
  And este rechazo ocurre independientemente del tier o del LLM utilizado
```

**Ejemplo de guardarraíl HITL:**
```gherkin
Scenario: Plan para mascota con condición médica nunca llega a ACTIVE sin revisión vet (Regla 4)
  Given una mascota registrada con condición "renal"
  When el owner solicita generación de plan
  Then el plan queda en estado "PENDING_VET"
  And el owner no puede ver ni exportar el plan hasta aprobación veterinaria
```

---

## PASO 5 — Generar skeleton de behave steps

Archivo: `tests/steps/{feature-file}_steps.py`

Si el archivo ya existe, appendar solo los `@step` de los nuevos scenarios.

```python
# -*- coding: utf-8 -*-
"""
Steps BDD — {Feature name} (US-XX: {nombre de la story})
Archivo feature: behaviors/{feature-file}.feature

Convención: código en inglés, comentarios de negocio en español.
Estado: skeleton — implementar durante Code Generation de unit-XX.
"""

from behave import given, when, then  # type: ignore
import pytest


# ─── STEPS: {NOMBRE DEL SCENARIO} ────────────────────────────────────────────

@given("{texto exacto del paso Given}")
def step_given_{nombre_descriptivo}(context):
    # TODO: {descripción del setup en español}
    raise NotImplementedError("Step pendiente de implementar")


@when("{texto exacto del paso When}")
def step_when_{nombre_descriptivo}(context):
    # TODO: {descripción de la acción en español}
    raise NotImplementedError("Step pendiente de implementar")


@then("{texto exacto del paso Then}")
def step_then_{nombre_descriptivo}(context):
    # TODO: {descripción de la verificación en español}
    raise NotImplementedError("Step pendiente de implementar")
```

**Reglas para el skeleton de steps:**
- Un `@given/@when/@then` por paso único del Gherkin
- `raise NotImplementedError` — hace fallar el step inmediatamente (red phase)
- Comentario `# TODO:` en español explicando qué debe hacer el step
- Si dos scenarios comparten un paso idéntico → un solo `@step` compartido

---

## PASO 6 — Generar skeleton de pytest

Archivo: `tests/{capa}/test_{módulo}.py`

Si el archivo ya existe, appendar solo las funciones de test nuevas.

```python
# -*- coding: utf-8 -*-
"""
Tests unitarios — {módulo} (US-XX: {nombre de la story})
Epic: {nombre de la épica}
BDD feature: behaviors/{feature-file}.feature

Quality Gates cubiertos: {lista de G1-G8 aplicables o "N/A"}
Convención: código en inglés, docstrings en español.
"""

import pytest


class Test{NombreClase}:
    """Tests para {descripción del módulo en español}."""

    # ─── Happy path ───────────────────────────────────────────────────────────

    def test_{descripción_técnica_happy_path}(self):
        """
        {AC cubierto — descripción en español}.
        Scenario BDD: '{nombre del scenario en el .feature}'
        """
        # Arrange — {descripción del estado inicial}
        # TODO: configurar datos de entrada

        # Act — {descripción de la acción}
        # TODO: ejecutar la función/método bajo prueba

        # Assert — {descripción del resultado esperado}
        # TODO: verificar resultado
        pytest.fail("not implemented")

    # ─── Edge cases ───────────────────────────────────────────────────────────

    def test_{descripción_técnica_edge_case}(self):
        """
        {Descripción del caso límite en español}.
        Scenario BDD: '{nombre del scenario en el .feature}'
        """
        # Arrange
        # TODO

        # Act
        # TODO

        # Assert
        pytest.fail("not implemented")

    # ─── Guardarraíles (incluir solo si aplica) ───────────────────────────────

    def test_toxic_ingredient_always_blocked(self):
        """
        Ingrediente tóxico debe ser rechazado siempre, sin excepción.
        Quality Gate G1 — 0 tóxicos en planes.
        Scenario BDD: 'Ingrediente tóxico para perros es rechazado en cualquier plan'
        """
        # Arrange
        # TODO: preparar caso con ingrediente tóxico

        # Act
        # TODO: llamar a food_toxicity_checker o equivalente

        # Assert — verificar rechazo
        pytest.fail("not implemented")
```

**Reglas para el skeleton pytest:**
- `pytest.fail("not implemented")` — falla inmediatamente (red phase TDD)
- Cada `def test_*` cubre exactamente un scenario del `.feature`
- El docstring referencia el AC cubierto y el nombre del scenario BDD
- Anotar `# Quality Gate GX` cuando aplique
- Nombre del método en inglés técnico, docstring en español

---

## PASO 7 — Verificar coherencia entre artefactos

Antes de presentar resultados:

- [ ] Cada AC tiene al menos un scenario en el `.feature`
- [ ] Cada scenario tiene al menos un `@step` en el steps skeleton
- [ ] Cada scenario tiene al menos un `def test_*` en el pytest skeleton
- [ ] Los guardarraíles aplicables tienen su scenario obligatorio
- [ ] No se duplicó ningún scenario ya existente en el `.feature`
- [ ] `behaviors/golden-cases/sally.feature` no fue modificado
- [ ] Los archivos de `behaviors/` con `# ═══` en el header no fueron reescritos

---

## PASO 8 — Reportar al usuario

```
✅ BDD generado para US-XX — {Nombre de la story}

Artefactos:
  behaviors/{feature-file}.feature        → {N} scenarios appendados / {N} ya existían
  tests/steps/{feature-file}_steps.py     → {N} steps skeleton (red phase)
  tests/{capa}/test_{módulo}.py           → {N} tests skeleton (red phase)

Cobertura de ACs:
  AC 1: ✅ → Scenario "{nombre}"
  AC 2: ✅ → Scenario "{nombre}"
  AC 3: ✅ → Scenario "{nombre}"

Guardarraíles incluidos:
  {G1 — Toxicidad: sí/no aplicable}
  {G2 — Restricciones médicas: sí/no aplicable}
  {Regla 4 — HITL: sí/no aplicable}
  {Regla 8 — Disclaimer: sí/no aplicable}

Quality Gates cubiertos: {lista de G1-G8 o "ninguno directo"}

Siguiente paso: implementar los steps y hacer pasar los tests (green phase).
  → Unit: /aidlc-construction
  → Sync Linear: /aidlc-to-linear
```

---

## Restricciones

| ❌ Prohibido | ✅ Permitido |
|-------------|-------------|
| Reescribir `.feature` existentes | Solo appendar scenarios nuevos |
| Modificar `behaviors/golden-cases/sally.feature` | Solo leerlo como referencia |
| Usar términos técnicos en pasos Gherkin | Lenguaje de negocio en español |
| Inventar ACs fuera de los definidos en la story | Derivar solo de ACs y constitución |
| Generar `.js` o cualquier archivo no-Python | Solo `.py` y `.feature` |
| Usar `assert False` en lugar de `pytest.fail()` | `pytest.fail("not implemented")` |
| Omitir guardarraíles cuando la story los requiere | Siempre incluirlos si aplican |
| Crear archivo en capa incorrecta | Determinar capa según dominio de la story |

---

## Vocabulario DDD del dominio

Usar estos nombres en el código de los skeletons (no en los pasos Gherkin):

| Concepto | Nombre en código | Módulo esperado |
|---------|-----------------|-----------------|
| Perfil de mascota | `PetProfile` | `domain/aggregates/pet_profile.py` |
| Plan nutricional | `NutritionPlan` | `domain/aggregates/nutrition_plan.py` |
| Calculador NRC | `NRCCalculator` | `domain/nutrition/nrc_calculator.py` |
| Verificador toxicidad | `FoodToxicityChecker` | `domain/safety/food_toxicity_checker.py` |
| Motor restricciones | `MedicalRestrictionEngine` | `domain/safety/medical_restrictions.py` |
| Alimentos tóxicos | `TOXIC_DOGS`, `TOXIC_CATS` | `domain/safety/toxic_foods.py` |
| Restricciones médicas | `RESTRICTIONS_BY_CONDITION` | `domain/safety/medical_restrictions.py` |
| Enrutador LLM | `LLMRouter` | `infrastructure/llm/llm_router.py` |
| Trazas del agente | `AgentTrace` | `domain/aggregates/agent_trace.py` |
| Cuenta de usuario | `UserAccount` | `domain/aggregates/user_account.py` |
