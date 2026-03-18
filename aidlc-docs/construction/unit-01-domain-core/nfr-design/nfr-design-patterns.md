# NFR Design Patterns — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones Aplicados en el Domain Core

### Patrón 1: Value Object Inmutable
Todos los value objects del dominio son `@dataclass(frozen=True)`.
- Garantiza inmutabilidad post-creación.
- Permite comparación por valor, no por referencia.
- Previene mutación accidental de estado de dominio.

```python
@dataclass(frozen=True)
class NRCResult:
    """Resultado del cálculo NRC. Inmutable."""
    rer_kcal: Decimal
    der_kcal: Decimal
    factors_applied: frozenset  # inmutable también
```

### Patrón 2: Guard Clauses en Constructores
Invariantes validadas en `__post_init__` para prevenir objetos en estado inválido.

```python
def __post_init__(self):
    if self.peso_kg <= 0:
        raise DomainInvariantError("peso_kg debe ser > 0")
    if not 1 <= self.bcs <= 9:
        raise DomainInvariantError("BCS debe estar entre 1 y 9")
```

### Patrón 3: Repository Pattern (Port)
Los ports son interfaces abstractas en domain que la infraestructura implementa.
- El dominio define el contrato, no la implementación.
- Permite testing sin base de datos (in-memory implementations).
- Dependency inversion aplicado estrictamente.

### Patrón 4: Fail-Fast para Seguridad Alimentaria
`FoodSafetyChecker` lanza excepción (no retorna bool) para ingredientes tóxicos.
- Asegura que el caller no pueda ignorar el resultado.
- El sistema se detiene en cualquier ingrediente tóxico.
- No hay resultado "posiblemente tóxico" — solo tóxico o seguro.

### Patrón 5: Strategy para Factores DER
Los factores DER están en tablas separadas (`factors.py`), no en la calculadora.
- Permite actualización de factores sin modificar la lógica de cálculo.
- Cualquier cambio en factores requiere validación de Lady Carolina y nuevo test.

### Patrón 6: Constantes como Single Source of Truth
`TOXIC_DOGS`, `TOXIC_CATS`, `RESTRICTIONS_BY_CONDITION` son frozensets Python.
- No hay base de datos para estas listas en runtime.
- Cambiar una lista requiere un commit, revisión de código, y deploy.
- El test de regression corre en cada PR para verificar las listas.

## Correctitud Numérica

- Usar `Decimal` (no `float`) para todos los cálculos calóricos.
- Redondear en el último paso, no en intermedios.
- Precisión: 2 decimales para output al usuario, 6 decimales para cálculos intermedios.
- Tolerancia Golden Case Sally: ±0.5 kcal.

```python
from decimal import Decimal, ROUND_HALF_UP

def calculate_rer(peso_kg: Decimal) -> Decimal:
    """Calcula RER usando fórmula NRC. Usa Decimal para precisión."""
    rer = Decimal("70") * (peso_kg ** Decimal("0.75"))
    return rer.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

## Aislamiento del Domain en Tests

```python
# tests/domain/test_nrc_calculator.py
# Sin mocks de base de datos ni HTTP — el dominio es puro
def test_sally_golden_case():
    """Caso Sally debe producir RER≈396 y DER≈534 con ±0.5 kcal."""
    profile = PetProfile(
        peso_kg=Decimal("9.6"),
        edad=AgeVO(8, "años"),
        estado_reproductivo="esterilizado",
        nivel_actividad=ActivityLevelVO("sedentario"),
        bcs=6, especie="perro", ...
    )
    result = NRCCalculator().calculate(profile)
    assert abs(result.rer_kcal - Decimal("396")) <= Decimal("0.5")
    assert abs(result.der_kcal - Decimal("534")) <= Decimal("0.5")
```
