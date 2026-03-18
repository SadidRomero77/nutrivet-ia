# Plan: Functional Design — Unit 01: domain-core

**Unidad**: unit-01-domain-core
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ✅ Completado (referencia a `_shared/`)
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del dominio core: cálculos NRC, seguridad de alimentos,
restricciones médicas, entidades y value objects.

## Artefactos Producidos

| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| Modelo de lógica de negocio (flujos E2E) | `_shared/business-logic-model.md` | ✅ |
| Reglas de negocio hard-coded | `_shared/business-rules.md` | ✅ |
| Entidades de dominio | `_shared/domain-entities.md` | ✅ |

## Lógica de Negocio Específica de domain-core

### NRCCalculator

```
RER = 70 × peso_kg ^ 0.75
DER = RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs

Factores de edad:
  < 4 meses  → 3.0
  4-12 meses → 2.0
  1-7 años   → 1.6 (perro) / 1.4 (gato)
  > 7 años   → 1.4 (perro) / 1.2 (gato)

Factores reproductivos:
  entero     → 1.8 (perro) / 1.6 (gato)
  esterilizado → 1.6 (perro) / 1.2 (gato)

Factores de actividad (perros):
  sedentario   → 1.2
  moderado     → 1.4
  activo       → 1.6
  muy_activo   → 1.8

Factores de actividad (gatos):
  indoor         → 1.2
  indoor_outdoor → 1.4
  outdoor        → 1.6

Factores BCS:
  BCS 1-3 (bajo peso)    → 1.2 (fase de aumento)
  BCS 4-6 (ideal)        → 1.0 (mantenimiento)
  BCS 7-9 (sobrepeso)    → 0.8 sobre peso ideal (fase de reducción)
```

### FoodSafetyChecker

```
TOXIC_DOGS = {uvas, cebolla, ajo, xilitol, chocolate, macadamia, ...}
TOXIC_CATS = {cebolla, ajo, uvas, lilium, chocolate, cafeína, ...}

Lógica: si ingredient.lower() in TOXIC_SPECIES → ToxicIngredientError
Acción: BLOQUEANTE — nunca llegar al LLM con ingrediente tóxico
```

### MedicalRestrictionEngine

```
RESTRICTIONS_BY_CONDITION = {
  "diabético": {"prohibido": [...], "limitado": [...], "recomendado": [...]},
  "renal": {...},
  ... (13 condiciones)
}

Lógica: get_restrictions(conditions) → unión de todas las restricciones
Acción: BLOQUEANTE — el LLM recibe las restricciones como contexto mandatory
```

## Casos de Prueba Críticos

- [ ] Golden case Sally: RER ≈ 396 kcal, DER ≈ 534 kcal (±0.5 kcal)
- [ ] Uvas en plan para perro → ToxicIngredientError
- [ ] Cebolla en plan para gato → ToxicIngredientError
- [ ] Diabético: restricciones correctas retornadas
- [ ] BCS 8 → factor 0.8 sobre peso ideal (no peso real)

## Referencias

- Spec: `aidlc-docs/inception/units/unit-01-domain-core.md`
- Global: `aidlc-docs/construction/_shared/business-rules.md`
- ADRs: ADR-002 (toxicidad hard-coded)
