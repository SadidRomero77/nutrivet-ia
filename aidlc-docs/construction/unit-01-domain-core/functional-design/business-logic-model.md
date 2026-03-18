# Business Logic Model — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos de Lógica de Negocio del Domain Core

### Flujo 1: NRCCalculator

```
Input: PetProfile (peso_kg, especie, edad, estado_reproductivo, nivel_actividad, bcs)
  ↓
1. Validar peso_kg > 0
2. RER = 70 × peso_kg^0.75  (siempre Python, nunca LLM)
3. Seleccionar factor_edad según especie + edad
4. Seleccionar factor_reproductivo
5. Seleccionar factor_actividad según especie + nivel
6. Aplicar factor_bcs
7. DER = RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs
8. Si bcs ≥ 7 → peso_objetivo = estimar_peso_ideal(raza, talla)
              → RER_reduccion = 70 × peso_objetivo^0.75 × factores × 0.8
9. Retornar NRCResult(rer_kcal, der_kcal, factores aplicados)
Output: NRCResult
```

### Flujo 2: FoodSafetyChecker

```
Input: ingredient_name: str, especie: Literal["perro", "gato"]
  ↓
1. Normalizar nombre → minúsculas, strip, remover tildes
2. Buscar en alias_map (ej: "aguacate" → "avocado")
3. Si especie == "perro" → check TOXIC_DOGS (constante hard-coded)
4. Si especie == "gato" → check TOXIC_CATS (constante hard-coded)
5. Si encontrado → raise ToxicIngredientError(ingredient, especie)
6. Si no → retornar SafetyResult(is_safe=True)
Output: SafetyResult | raise ToxicIngredientError (BLOQUEANTE)
```

### Flujo 3: MedicalRestrictionEngine

```
Input: ingredients: list[str], conditions: list[MedicalConditionVO]
  ↓
1. Si conditions == [] → retornar vacío (sin restricciones)
2. Para cada condition en conditions:
   a. Obtener restricted_ingredients = RESTRICTIONS_BY_CONDITION[condition]
   b. Para cada ingredient en ingredients:
      - Si ingredient ∈ restricted_ingredients → agregar a violations
3. Retornar RestrictionResult(violations: list[Violation], passed: bool)
Output: RestrictionResult
Nota: Si violations → el plan no puede generarse hasta que el LLM remueva los ingredientes violados
```

### Flujo 4: LLMRouter (Pure Domain Logic)

```
Input: pet_profile (condiciones_medicas, tier)
  ↓
1. Contar condiciones médicas activas: n = len(condiciones_medicas)
2. Si n >= 3 → return "anthropic/claude-sonnet-4-5"  (override clínico, siempre)
3. Si tier == "premium" o tier == "vet" → return "anthropic/claude-sonnet-4-5"
4. Si tier == "basico" → return "openai/gpt-4o-mini"
5. Si tier == "free" → return "meta-llama/llama-3.3-70b"
Output: model_id: str
```

### Flujo 5: QueryClassifier (Domain Logic)

```
Input: query: str
  ↓
1. Detectar palabras clave de emergencia (lista hard-coded):
   "convulsión", "convulsiones", "no respira", "envenenamiento", "emergencia"
   "colapso", "sangrado", "fracturas", "desmayo" → emergency=True
2. Detectar palabras clave médicas:
   "síntomas", "medicamento", "diagnóstico", "medicina", "tratamiento",
   "pastilla", "dosis", "veterinario" → intent=MEDICAL_QUERY
3. Si no → intent=NUTRITIONAL_QUERY
Output: IntentClassification(intent, emergency, confidence)
```

### Invariantes del Dominio

- `PetProfile.peso_kg` SIEMPRE > 0
- `PetProfile.bcs` SIEMPRE en rango 1–9
- `PetProfile.talla` SOLO para especie == "perro"
- `NutritionPlan.sections` SIEMPRE len == 5
- `NutritionPlan.rer_kcal` y `der_kcal` NUNCA calculados por LLM
- `AgentTrace` NUNCA modificado post-inserción (append-only)
- `TOXIC_DOGS`, `TOXIC_CATS`: nunca derivados de LLM
