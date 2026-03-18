# Logical Components — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Domain Core

### NRCCalculator
**Responsabilidad**: Calcular RER y DER de forma determinista.
**Entradas**: `PetProfile` completo
**Salidas**: `NRCResult`
**Dependencias**: ninguna (solo math stdlib)
**Criticidad**: ALTA — Golden case Sally debe pasar con ±0.5 kcal

```
NRCCalculator
  ├── calculate_rer(peso_kg: Decimal) → Decimal
  ├── calculate_der(rer: Decimal, profile: PetProfile) → Decimal
  ├── get_age_factor(age: AgeVO, especie: str) → Decimal
  ├── get_reproductive_factor(estado: str) → Decimal
  ├── get_activity_factor(nivel: ActivityLevelVO, especie: str) → Decimal
  ├── get_bcs_factor(bcs: int) → Decimal
  └── estimate_ideal_weight(raza: str, talla: str) → Decimal
```

### FoodSafetyChecker
**Responsabilidad**: Verificar si un ingrediente es tóxico para la especie.
**Entradas**: `ingredient_name: str`, `especie: str`
**Salidas**: `SafetyResult` | raise `ToxicIngredientError`
**Dependencias**: `TOXIC_DOGS`, `TOXIC_CATS` (constantes)
**Criticidad**: MÁXIMA — 0% tolerancia a falsos negativos

```
FoodSafetyChecker
  ├── check(ingredient: str, especie: str) → SafetyResult
  ├── normalize_ingredient(name: str) → str
  └── _load_aliases() → dict[str, str]
```

### MedicalRestrictionEngine
**Responsabilidad**: Verificar restricciones de ingredientes por condición médica.
**Entradas**: `ingredients: list[str]`, `conditions: list[MedicalConditionVO]`
**Salidas**: `RestrictionResult`
**Dependencias**: `RESTRICTIONS_BY_CONDITION` (constante)
**Criticidad**: MÁXIMA — 100% aplicación requerida (Quality Gate G2)

```
MedicalRestrictionEngine
  ├── check_all(ingredients, conditions) → RestrictionResult
  ├── check_condition(ingredient, condition) → bool
  └── get_restrictions_for_condition(condition) → set[str]
```

### LLMRouter
**Responsabilidad**: Determinar modelo LLM según tier y complejidad clínica.
**Entradas**: `condiciones_medicas: list`, `tier: str`
**Salidas**: `model_id: str`
**Dependencias**: ninguna
**Criticidad**: ALTA — 3+ condiciones SIEMPRE → claude-sonnet-4-5

```
LLMRouter
  ├── resolve_model(pet_profile: PetProfile) → str
  ├── resolve_ocr_model() → str  (siempre gpt-4o)
  └── _is_clinical_override(n_conditions: int) → bool
```

### QueryClassifier
**Responsabilidad**: Clasificar intención de consulta conversacional.
**Entradas**: `query: str`
**Salidas**: `IntentClassification`
**Dependencias**: listas de palabras clave hard-coded
**Criticidad**: ALTA — ≥95% accuracy (Quality Gate G3)

```
QueryClassifier
  ├── classify(query: str) → IntentClassification
  ├── detect_emergency(query: str) → bool
  └── detect_medical_intent(query: str) → bool
```

## Diagrama de Dependencias entre Componentes

```
NRCCalculator ──────────────────┐
FoodSafetyChecker ──────────────┤→ PlanGenerationSubgraph (application)
MedicalRestrictionEngine ───────┤
LLMRouter ──────────────────────┘

QueryClassifier ─────────────────→ ConsultationSubgraph (application)

Entities / VOs ─────────────────→ todos los componentes de application
Ports (interfaces) ──────────────→ implementados en infrastructure
```
