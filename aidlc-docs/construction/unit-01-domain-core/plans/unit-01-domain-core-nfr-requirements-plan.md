# Plan: NFR Requirements — Unit 01: domain-core

**Unidad**: unit-01-domain-core
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ✅ Definido
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del Domain Core

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| NRCCalculator.calculate_rer() | < 1ms | Cálculo matemático puro — Python stdlib |
| NRCCalculator.calculate_der() | < 1ms | Cálculo matemático puro — Python stdlib |
| FoodSafetyChecker.check() | < 5ms | Lookup en set Python en memoria |
| MedicalRestrictionEngine.get_restrictions() | < 5ms | Dict lookup en memoria |

**Regla crítica**: domain/ CERO llamadas de red, CERO I/O — solo Python stdlib.

### Seguridad

- `TOXIC_DOGS`, `TOXIC_CATS`, `RESTRICTIONS_BY_CONDITION`: constantes inmutables en código.
- No se pueden modificar en runtime ni via config externa.
- Cambios requieren commit + validación de Lady Carolina (ver Constitution REGLA 1 y 2).

### Confiabilidad

- Los cálculos NRC son determinísticos: mismo input → mismo output siempre.
- No hay estado mutable en domain layer.
- Tests deben pasar en CI con 100% reproducibilidad.

### Mantenibilidad

- Cobertura mínima: **80% en domain/** — obligatorio para CI.
- Todas las funciones: type hints obligatorios.
- Docstrings en español en todo módulo, clase y función pública.
- Ruff como linter: 0 warnings en domain/.

### Dependencias Externas

**CERO**. El domain layer no puede importar librerías externas.
Solo `Python stdlib` está permitido.

```python
# PROHIBIDO en domain/:
import fastapi    # ❌
import sqlalchemy # ❌
import httpx      # ❌
import pydantic   # ❌ (solo en presentation/)

# PERMITIDO en domain/:
from __future__ import annotations  # ✅
from typing import TypedDict        # ✅
from decimal import Decimal         # ✅
from enum import Enum               # ✅
```

## Checklist NFR domain-core

- [ ] `pytest --cov=backend/domain tests/domain/ --cov-fail-under=80` pasa
- [ ] `ruff check backend/domain/` → 0 errores
- [ ] `bandit -r backend/domain/` → 0 HIGH/MEDIUM
- [ ] Golden case Sally: CI no permite merge si falla
- [ ] Ningún import externo en domain/

## Referencias

- Global: `_shared/nfr-requirements.md`
- Constitution: `.claude/rules/00-constitution.md`
- Unit spec: `inception/units/unit-01-domain-core.md`
