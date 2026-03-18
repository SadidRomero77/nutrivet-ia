# Plan: Code Generation — Unit 01: domain-core

**Unidad**: unit-01-domain-core
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar el domain layer completo: NRC calculator, food safety checker,
medical restriction engine, aggregates (PetProfile, NutritionPlan) y value objects.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.

---

## Pasos de Implementación

### Paso 1 — Estructura de Carpetas

- [ ] Crear `backend/domain/__init__.py`
- [ ] Crear `backend/domain/nutrition/__init__.py`
- [ ] Crear `backend/domain/safety/__init__.py`
- [ ] Crear `backend/domain/aggregates/__init__.py`
- [ ] Crear `backend/domain/value_objects/__init__.py`
- [ ] Crear `backend/domain/exceptions/__init__.py`
- [ ] Crear `tests/domain/__init__.py`
- [ ] Crear `tests/domain/test_nrc_calculator.py` (vacío)
- [ ] Crear `tests/domain/test_food_safety_checker.py` (vacío)
- [ ] Crear `tests/domain/test_medical_restriction_engine.py` (vacío)
- [ ] Crear `tests/domain/test_pet_profile.py` (vacío)
- [ ] Crear `tests/domain/test_nutrition_plan.py` (vacío)

### Paso 2 — Tests RED (TDD Phase 1): Excepciones y Value Objects

- [ ] Escribir `tests/domain/test_value_objects.py`:
  - test_bcs_valido_entre_1_y_9
  - test_bcs_invalido_lanza_error
  - test_bcs_phase_reduccion_si_bcs_mayor_6
  - test_bcs_der_factor_correcto
  - test_email_address_formato_invalido
  - test_positive_decimal_peso_negativo_falla
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 3 — GREEN: Implementar Value Objects

- [ ] Crear `backend/domain/exceptions/domain_errors.py`
  - DomainError (base)
  - ToxicIngredientError
  - MedicalRestrictionViolationError
  - InvalidWeightError
  - InvalidBCSError
  - NRCCalculationError
- [ ] Crear `backend/domain/value_objects/bcs.py` — BCS frozen dataclass
- [ ] Crear `backend/domain/value_objects/email_address.py` — EmailAddress
- [ ] Crear `backend/domain/value_objects/positive_decimal.py` — PositiveDecimal
- [ ] Verificar que tests de value objects PASAN (GREEN)

### Paso 4 — Tests RED: NRCCalculator

- [ ] Escribir tests en `tests/domain/test_nrc_calculator.py`:
  - **test_golden_case_sally_rer** — `calculate_rer(9.6)` ≈ 396 kcal (±0.5) — BLOQUEANTE
  - **test_golden_case_sally_der** — `calculate_der(rer=396, ...)` ≈ 534 kcal (±0.5) — BLOQUEANTE
  - test_rer_peso_cero_lanza_error
  - test_rer_peso_negativo_lanza_error
  - test_rer_cachorro_4_meses
  - test_der_factor_edad_cachorro
  - test_der_factor_reproductivo_esterilizado
  - test_der_factor_actividad_sedentario
  - test_der_factor_bcs_8_reduccion
  - test_der_factor_bcs_3_aumento
  - test_der_gato_indoor
  - test_der_gato_outdoor
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 5 — GREEN: Implementar NRCCalculator

- [ ] Crear `backend/domain/nutrition/nrc_factors.py` — Constantes de todos los factores
- [ ] Crear `backend/domain/nutrition/nrc_calculator.py`:
  - `calculate_rer(weight_kg: float) -> float`
  - `calculate_der(rer: float, age_months: int, reproductive_status: str, activity_level: str, species: str, bcs: int) -> float`
  - `get_ideal_weight_estimate(weight_kg: float, bcs: int) -> float` — para BCS > 6
- [ ] Verificar que TODOS los tests NRC PASAN, especialmente Sally (±0.5 kcal)

### Paso 6 — Tests RED: FoodSafetyChecker

- [ ] Escribir tests en `tests/domain/test_food_safety_checker.py`:
  - test_uvas_toxico_para_perro
  - test_uvas_toxico_para_gato
  - test_chocolate_toxico_ambas_especies
  - test_lilium_toxico_solo_gato_no_perro
  - test_pollo_seguro_ambas_especies
  - test_lista_mixta_retorna_todos_los_toxicos
  - test_ingrediente_case_insensitive
  - test_ingrediente_con_alias_detectado
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 7 — GREEN: Implementar FoodSafetyChecker

- [ ] Crear `backend/domain/safety/toxic_foods.py` — TOXIC_DOGS, TOXIC_CATS como frozenset
- [ ] Crear `backend/domain/safety/food_safety_checker.py`:
  - `check_ingredient(ingredient: str, species: str) -> bool`
  - `validate_plan_ingredients(ingredients: list[str], species: str) -> list[ToxicityResult]`
  - `get_toxic_list_for_species(species: str) -> frozenset[str]`
- [ ] Verificar que todos los tests PASAN

### Paso 8 — Tests RED: MedicalRestrictionEngine

- [ ] Escribir tests en `tests/domain/test_medical_restriction_engine.py`:
  - test_diabetico_restricciones_correctas
  - test_renal_restricciones_correctas
  - test_hepatico_restricciones_correctas
  - test_pancreatico_restricciones_correctas
  - test_ninguna_condicion_retorna_vacio
  - test_multiples_condiciones_union_correcta
  - test_todas_las_13_condiciones_tienen_restricciones
  - test_condicion_invalida_lanza_error
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 9 — GREEN: Implementar MedicalRestrictionEngine

- [ ] Crear `backend/domain/safety/medical_restrictions.py` — RESTRICTIONS_BY_CONDITION dict
  - Las 13 condiciones con sus restricciones (prohibido, limitado, recomendado)
  - Validado clínicamente por Lady Carolina
- [ ] Crear `backend/domain/safety/medical_restriction_engine.py`:
  - `get_restrictions_for_conditions(conditions: list[str]) -> MedicalRestrictions`
  - `validate_ingredient_against_conditions(ingredient: str, conditions: list[str]) -> list[RestrictionResult]`
- [ ] Verificar que todos los tests PASAN

### Paso 10 — Tests RED: PetProfile Aggregate

- [ ] Escribir tests en `tests/domain/test_pet_profile.py`:
  - test_crear_pet_profile_valido
  - test_talla_requerida_solo_para_perros
  - test_gato_sin_talla_es_valido
  - test_perro_sin_talla_falla
  - test_activity_level_invalido_para_especie
  - test_bcs_fuera_de_rango_falla
  - test_peso_negativo_falla
  - test_condicion_medica_desconocida_falla
  - test_requires_vet_review_true_con_condicion
  - test_requires_vet_review_false_sin_condicion
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 11 — GREEN: Implementar PetProfile Aggregate

- [ ] Crear `backend/domain/aggregates/pet_profile.py`:
  - PetProfile dataclass con los 13 campos
  - `__post_init__` con validaciones de invariantes
  - `requires_vet_review() -> bool`
  - `can_add_pet(current_count: int, tier: str) -> bool`
  - `get_activity_options_for_species(species: str) -> list[str]`
- [ ] Verificar que todos los tests PASAN

### Paso 12 — Tests RED: NutritionPlan Aggregate

- [ ] Escribir tests en `tests/domain/test_nutrition_plan.py`:
  - test_crear_plan_sano_status_active
  - test_crear_plan_con_condicion_status_pending_vet
  - test_aprobar_plan_cambia_status_active
  - test_aprobar_temporal_medical_sin_review_date_falla
  - test_devolver_con_comentario_vacio_falla
  - test_archivar_plan_activo
  - test_plan_archivado_no_modificable
  - test_agregar_condicion_a_plan_activo_vuelve_pending_vet
  - test_export_solo_si_status_active
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 13 — GREEN: Implementar NutritionPlan Aggregate

- [ ] Crear `backend/domain/aggregates/nutrition_plan.py`:
  - NutritionPlan con máquina de estados (PENDING_VET / ACTIVE / UNDER_REVIEW / ARCHIVED)
  - `approve(vet_id, review_date)` → valida review_date si temporal_medical
  - `return_to_owner(vet_id, comment)` → valida comment no vacío
  - `archive()` → inmutable post-archivado
  - `can_export() -> bool` → True solo si ACTIVE
  - `requires_vet_review() -> bool`
- [ ] Verificar que todos los tests PASAN

### Paso 14 — Cobertura y Calidad

- [ ] Ejecutar: `pytest --cov=backend/domain tests/domain/ --cov-fail-under=80`
- [ ] Verificar cobertura ≥ 80% en domain/
- [ ] Ejecutar: `ruff check backend/domain/` → 0 errores
- [ ] Ejecutar: `bandit -r backend/domain/` → 0 HIGH/MEDIUM
- [ ] Confirmar que Golden case Sally pasa: RER ≈ 396, DER ≈ 534 (±0.5)

---

## Criterios de Done

- [ ] Todos los tests pasando (incluido Golden case Sally)
- [ ] Cobertura ≥ 80% en domain layer
- [ ] Cero imports externos en domain/
- [ ] Ruff + bandit sin errores
- [ ] TOXIC_DOGS, TOXIC_CATS, RESTRICTIONS_BY_CONDITION implementadas

## Tiempo Estimado

3-4 días (incluye TDD completo)

## Dependencias

Ninguna — es la unidad base del sistema.

## Referencias

- Unit spec: `inception/units/unit-01-domain-core.md`
- ADR-002: toxicidad hard-coded
- Constitution REGLA 1, 2, 3
- Construction rules: `.claude/rules/02-construction.md`
