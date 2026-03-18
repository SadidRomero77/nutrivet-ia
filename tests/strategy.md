# Estrategia de Tests — NutriVet.IA

**Filosofía**: Test first en domain layer. El código de producción solo existe para hacer pasar un test.

---

## Pirámide de Tests

```
                    ┌──────────────┐
                    │  E2E Tests   │  ← Pocos, lentos, solo flujos críticos
                    │  (Flutter)   │
                  ┌─┴──────────────┴─┐
                  │ Integration Tests │  ← API endpoints, DB, LLM mocks
                  │   (pytest)        │
                ┌─┴───────────────────┴─┐
                │    BDD Tests          │  ← Gherkin → pytest-bdd (behaviors/)
                │    (pytest-bdd)       │
              ┌─┴───────────────────────┴─┐
              │      Unit Tests           │  ← La base. TDD primero.
              │   (pytest — domain/)      │  ← Cobertura ≥ 80% OBLIGATORIO
              └───────────────────────────┘
```

---

## Orden de Implementación (No Negociable)

```
1. domain/safety/          → toxic_foods, medical_restrictions (cobertura 100%)
2. domain/nutrition/       → nrc_calculator (cobertura 100% — Caso Sally es bloqueante)
3. domain/entities/        → pet_profile, nutrition_plan, user_account (cobertura ≥ 90%)
4. domain/value_objects/   → BCS, Species, PlanStatus, enums (cobertura 100%)
5. application/use_cases/  → generate_plan, approve_plan, scan_label (cobertura ≥ 80%)
6. infrastructure/         → tests de integración con mocks (cobertura ≥ 70%)
7. presentation/           → tests de API con TestClient (cobertura ≥ 70%)
8. behaviors/              → pytest-bdd conecta .feature con steps
```

---

## Tests Bloqueantes de Release (Quality Gates)

Estos tests deben pasar en CI antes de cualquier merge a `main`:

### G1 — Zero Tóxicos
```python
# tests/domain/test_golden_set.py
@pytest.mark.parametrize("case", load_golden_set_60_cases())
def test_no_toxic_ingredients_in_plan(case):
    """Ningún plan del golden set de 60 casos contiene tóxicos."""
    plan = generate_plan(case["pet_profile"])
    for ingredient in plan.ingredients:
        assert ingredient not in TOXIC_DOGS if case["species"] == "perro" else TOXIC_CATS
```

### G2 — Restricciones Médicas 100%
```python
# tests/domain/test_medical_restrictions.py
@pytest.mark.parametrize("condition", MedicalCondition)
def test_all_restrictions_applied(condition):
    """Todas las restricciones de cada condición se aplican en el plan."""
    restrictions = RESTRICTIONS_BY_CONDITION[condition]
    plan = generate_plan_with_condition(condition)
    for restricted_item in restrictions:
        assert restricted_item not in plan.allowed_ingredients
```

### G8 — Caso Sally (Bloqueante más crítico)
```python
# tests/domain/test_nrc_calculator.py
def test_sally_golden_case():
    """
    El golden case de Sally debe reproducir exactamente los valores validados
    por Lady Carolina Castañeda (MV, BAMPYSVET).
    Tolerancia: ±0.5 kcal
    """
    sally = PetProfile(
        species=Species.PERRO,
        weight_kg=Decimal("9.6"),
        age_months=96,
        reproductive_status=ReproductiveStatus.ESTERILIZADO,
        activity_level=DogActivityLevel.SEDENTARIO,
        bcs=BCS(6),
        medical_conditions=[
            MedicalCondition.DIABETICO,
            MedicalCondition.HEPATICO_HIPERLIPIDEMIA,
            MedicalCondition.GASTRITIS,
            MedicalCondition.CISTITIS_URINARIA,
            MedicalCondition.HIPOTIROIDEO,
        ]
    )
    calc = NRCCalculator()
    result = calc.calculate(sally)

    assert abs(result.rer_kcal - 396.0) <= 0.5, f"RER esperado ≈396, obtenido {result.rer_kcal}"
    assert abs(result.der_kcal - 534.0) <= 0.5, f"DER esperado ≈534, obtenido {result.der_kcal}"
    assert result.weight_phase == WeightPhase.MANTENIMIENTO
    assert result.llm_model == "gpt-4o"  # 5 condiciones → GPT-4o
    assert result.requires_vet_review == True
```

---

## Estructura de Directorios de Tests

```
tests/
├── domain/
│   ├── test_nrc_calculator.py        # RER/DER, Sally, todos los factores
│   ├── test_toxic_foods.py           # TOXIC_DOGS, TOXIC_CATS, todas las especies
│   ├── test_medical_restrictions.py  # 13 condiciones × restricciones
│   ├── test_pet_profile.py           # Invariantes del aggregate PetProfile
│   ├── test_nutrition_plan.py        # Máquina de estados, invariantes
│   ├── test_user_account.py          # Límites de subscripción, roles
│   └── test_golden_set.py            # 60 casos del golden set
│
├── application/
│   ├── test_generate_plan_use_case.py
│   ├── test_approve_plan_use_case.py
│   └── test_scan_label_use_case.py
│
├── integration/
│   ├── test_api_auth.py              # JWT, refresh, RBAC
│   ├── test_api_pets.py              # CRUD mascotas
│   ├── test_api_plans.py             # Generación, HITL, exportación
│   └── test_api_scanner.py           # OCR pipeline
│
├── bdd/
│   ├── conftest.py                   # Step definitions compartidos
│   ├── test_plan_generation.py       # → behaviors/plan-generation.feature
│   ├── test_hitl_workflow.py         # → behaviors/hitl-workflow.feature
│   ├── test_medical_restrictions.py  # → behaviors/medical-restrictions.feature
│   ├── test_ocr_scanner.py           # → behaviors/ocr-scanner.feature
│   ├── test_conversational_agent.py  # → behaviors/conversational-agent.feature
│   └── test_sally_golden_case.py     # → behaviors/golden-cases/sally.feature
│
├── fixtures/
│   ├── sally.json                    # Golden case Sally completo
│   ├── golden_set_60.json            # 60 casos para G1
│   └── pet_profiles/                 # Perfiles de prueba variados
│
└── quality-gates.md                  # G1-G8 con criterios de aceptación
```

---

## Herramientas

```toml
# pyproject.toml — sección [tool.pytest]
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "golden: golden cases — siempre corren en CI",
    "slow: tests lentos — solo en pipeline completo",
    "security: tests de seguridad y red-teaming",
]

[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

```bash
# Comandos de uso frecuente

# Solo domain layer (más rápido — correr durante desarrollo)
pytest tests/domain/ --cov=app/domain --cov-fail-under=80 -v

# Golden case Sally (bloqueante)
pytest tests/domain/test_nrc_calculator.py::test_sally_golden_case -v

# BDD completo
pytest tests/bdd/ -v --gherkin-terminal-reporter

# Suite completa con cobertura
pytest --cov=app tests/ --cov-report=html --cov-fail-under=80

# Solo golden set G1 (60 casos)
pytest tests/domain/test_golden_set.py -m golden -v

# Red-teaming (G7)
pytest tests/domain/ -m security -v
```

---

## Fixtures Clave

Los fixtures en `tests/fixtures/` son la fuente de verdad para los tests. No se generan dinámicamente — son JSON predefinidos y revisados por Lady Carolina Castañeda.

| Fixture | Descripción | Validado por |
|---------|-------------|-------------|
| `sally.json` | Golden case completo — RER 396, DER 534 | Lady Carolina ✅ |
| `golden_set_60.json` | 60 casos variados: 0 deben tener tóxicos | Lady Carolina (en progreso) |
| `cat_indoor_senior.json` | Gato indoor senior — prueba factores NRC felinos | Pendiente |
| `puppy_life_stage.json` | Cachorro con milestones — prueba life_stage plan | Pendiente |
