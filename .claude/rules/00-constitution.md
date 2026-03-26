# Constitution — Principios No Negociables de NutriVet.IA

Este documento define los principios que el agente IA NUNCA puede sobrescribir, ignorar ni reinterpretar.
Cualquier cambio requiere confirmación explícita de Sadid Romero o Lady Carolina Castañeda (MV).

---

## REGLA 1 — Toxicidad Hard-Coded (BLOQUEANTE)

`TOXIC_DOGS` y `TOXIC_CATS` son listas definidas en `domain/safety/` como constantes Python.
El LLM **NUNCA** decide si un alimento es tóxico. Estas listas son la única fuente de verdad.

```python
# domain/safety/toxic_foods.py — nunca modificar sin validación veterinaria
TOXIC_DOGS = {"uvas", "cebolla", "ajo", "xilitol", "chocolate", "macadamia", ...}
TOXIC_CATS = {"cebolla", "ajo", "uvas", "lilium", "chocolate", "cafeína", ...}
```

**Acción del agente**: Si un ingrediente aparece en estas listas → rechazar siempre, sin excepción.

---

## REGLA 2 — Restricciones Médicas Hard-Coded (BLOQUEANTE)

`RESTRICTIONS_BY_CONDITION` cubre las 13 condiciones soportadas. El LLM **no puede sobrescribir** estas restricciones.

Las 13 condiciones: `diabético · hipotiroideo · cancerígeno · articular · renal · hepático/hiperlipidemia · pancreático · neurodegenerativo · bucal/periodontal · piel/dermatitis · gastritis · cistitis/enfermedad_urinaria · sobrepeso/obesidad`

**Acción del agente**: Si hay conflicto entre lo que el LLM sugiere y una restricción hard-coded → la restricción gana siempre.

---

## REGLA 3 — RER/DER Siempre Determinista (BLOQUEANTE)

```
RER = 70 × peso_kg^0.75
DER = RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs
```

El cálculo calórico **NUNCA** lo hace el LLM. Es Python puro en `domain/nutrition/nrc_calculator.py`.

**Golden case Sally**: RER ≈ 396 kcal · DER ≈ 534 kcal/día (tolerancia ±0.5 kcal). Si el output difiere, hay un bug.

---

## REGLA 4 — HITL Solo Para Mascotas Con Condición Médica

- Mascota sana → Plan `ACTIVE` directo. Sin revisión de vet.
- Mascota con condición médica → Plan `PENDING_VET` → firma vet → `ACTIVE`.
- Si owner agrega condición a plan `ACTIVE` → vuelve a `PENDING_VET`.

**Nunca** implementar HITL para mascotas sanas. **Nunca** saltarse HITL para mascotas con condición médica.

---

## REGLA 5 — LLM Routing Por Tier + Override Clínico (BLOQUEANTE)

Proveedor unificado: **OpenRouter**. Sin endpoints `:free` — sin SLA, rate limits compartidos.
Routing por tier de suscripción con override por complejidad clínica.

```
Free tier                → openai/gpt-4o-mini
Básico tier              → openai/gpt-4o-mini
Premium / Vet tier       → anthropic/claude-sonnet-4-5
2+ condiciones (any tier)→ anthropic/claude-sonnet-4-5  ← override no negociable
OCR (todos los tiers)    → openai/gpt-4o (vision)
Query classifier         → openai/gpt-4o-mini  (clasificación de seguridad crítica)
```

**Umbral 2 (no 3)**: 2 condiciones simultáneas (ej: diabetes+renal) implican restricciones
contradictorias que requieren el modelo de mayor capacidad de razonamiento clínico.

**Nunca** usar un modelo inferior para casos con 2+ condiciones médicas, independientemente del tier.
**Nunca** usar modelos locales (Ollama) ni endpoints `:free` para generación de planes o OCR.

---

## REGLA 6 — Seguridad de Datos (BLOQUEANTE)

- Datos médicos: AES-256 en reposo en PostgreSQL.
- Prompts a LLMs externos: solo IDs anónimos — **nunca** nombres, especie, condición médica en texto plano.
- Logs: JSON estructurado — **nunca** PII en logs.
- `agent_traces`: inmutables post-generación — **sin UPDATE** sobre trazas existentes.
- JWT: access 15min + refresh rotativo. **Nunca** JWT sin expiración.
- CORS: explícito. **Nunca** wildcard en producción.

---

## REGLA 7 — OCR Solo Tabla Nutricional o Ingredientes

El scanner solo acepta imagen de tabla nutricional o lista de ingredientes.
**NUNCA** imagen de marca, logo, o empaque frontal. Principio de imparcialidad.

---

## REGLA 8 — Disclaimer Obligatorio en Cada Vista de Plan

> "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."

Este texto debe aparecer en **cada vista** del plan, sin excepción. No puede omitirse ni minimizarse.

---

## REGLA 9 — Agente Conversacional: Límite Nutricional/Médico

- Consultas nutricionales → el agente responde.
- Consultas médicas (síntomas, medicamentos, diagnósticos) → el agente remite al vet con mensaje estructurado. **Nunca** responde consultas médicas.

---

## REGLA 10 — Ayuno Máximo 12 Horas

Los planes **nunca** deben incluir ayunos mayores a 12 horas. Riesgo hepático/biliar/pancreático.

---

## Acciones que Requieren Confirmación Explícita

Antes de implementar cualquiera de estas acciones, detener y confirmar con Sadid Romero:

- Merge a `main`/`master`
- Cambios en esquema de base de datos
- Modificar lógica de restricciones nutricionales
- Modificar `TOXIC_DOGS`, `TOXIC_CATS`, `RESTRICTIONS_BY_CONDITION`
- Cambiar LLM routing o umbrales de condiciones
- Deploy a producción
- Agregar sponsor a lista de concentrados
