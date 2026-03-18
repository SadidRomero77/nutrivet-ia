# Plan: NFR Design — Unit 01: domain-core

**Unidad**: unit-01-domain-core
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ✅ Definido
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a domain-core

### Patrón: Determinismo Total

**Contexto**: Los cálculos NRC y las verificaciones de seguridad deben ser 100% reproducibles.

**Diseño**:
- Todas las funciones son puras (sin efectos secundarios, sin estado mutable).
- Los factores NRC están en constantes inmutables (`NRC_FACTORS` dict).
- No hay randomización ni dependencia de fecha/hora.

```python
# Ejemplo de función pura en domain:
def calculate_rer(weight_kg: float) -> float:
    """Calcula RER según estándar NRC. Función pura — sin efectos secundarios."""
    if weight_kg <= 0:
        raise InvalidWeightError(f"weight_kg debe ser > 0, recibido: {weight_kg}")
    return 70 * (weight_kg ** 0.75)
```

### Patrón: Fail-Fast con Errores de Dominio

**Contexto**: Errores en domain deben ser detectados lo antes posible con mensajes claros.

**Diseño**:
- Validaciones en constructores de aggregates y value objects.
- Excepciones de dominio explícitas (no generic Exception).
- No se permite `None` retornado cuando un error ocurre — siempre excepción.

```python
# Jerarquía de excepciones de dominio:
class DomainError(Exception): pass
class ToxicIngredientError(DomainError): pass
class MedicalRestrictionViolationError(DomainError): pass
class InvalidWeightError(DomainError): pass
class InvalidBCSError(DomainError): pass
class NRCCalculationError(DomainError): pass
```

### Patrón: Inmutabilidad de Reglas de Seguridad

**Contexto**: `TOXIC_DOGS`, `TOXIC_CATS` y `RESTRICTIONS_BY_CONDITION` no pueden cambiar
en runtime.

**Diseño**:
```python
# Constantes inmutables — frozenset para O(1) lookup
TOXIC_DOGS: frozenset[str] = frozenset({
    "uvas", "pasas", "cebolla", "ajo", "cebollín",
    "xilitol", "chocolate", "macadamia", "nuez moscada",
    "alcohol", "cafeína", "té", "café", "aguacate",
    "tomate verde", "rábano", "levadura cruda"
})

TOXIC_CATS: frozenset[str] = frozenset({
    "cebolla", "ajo", "cebollín", "uvas", "pasas",
    "lilium", "chocolate", "cafeína", "café", "té",
    "alcohol", "xilitol", "paracetamol", "ibuprofeno",
    "eucalipto", "aceite de árbol de té"
})
```

### Patrón: Value Objects con Validación

**Contexto**: Los campos críticos del dominio necesitan validación en construcción.

```python
@dataclass(frozen=True)  # frozen=True → inmutable
class BCS:
    value: int

    def __post_init__(self):
        if not (1 <= self.value <= 9):
            raise InvalidBCSError(f"BCS debe estar entre 1 y 9, recibido: {self.value}")

    @property
    def phase(self) -> str:
        if self.value <= 3:
            return "aumento"
        elif self.value <= 6:
            return "mantenimiento"
        else:
            return "reduccion"

    @property
    def der_factor(self) -> float:
        return {
            "aumento": 1.2,
            "mantenimiento": 1.0,
            "reduccion": 0.8
        }[self.phase]
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `nrc_calculator.py` | 100% | Unit tests — todos los factores |
| `food_safety_checker.py` | 100% | Unit tests — todas las especies |
| `medical_restriction_engine.py` | 90% | Unit tests — 13 condiciones |
| `aggregates/pet_profile.py` | 80% | Unit tests — invariantes |
| `aggregates/nutrition_plan.py` | 80% | Unit tests — ciclo de vida |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- Constitution: REGLA 1, REGLA 2, REGLA 3
- ADR-002: toxicidad hard-coded
