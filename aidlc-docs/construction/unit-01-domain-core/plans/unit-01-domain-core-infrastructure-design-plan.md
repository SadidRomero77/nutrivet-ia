# Plan: Infrastructure Design — Unit 01: domain-core

**Unidad**: unit-01-domain-core
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ✅ Definido
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

El domain core es **agnóstico de infraestructura por diseño**. No tiene componentes de
infraestructura propios. Reside como código Python puro ejecutado en el mismo contenedor
FastAPI del backend.

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| NRCCalculator | Módulo Python en `backend/domain/nutrition/nrc_calculator.py` |
| FoodSafetyChecker | Módulo Python en `backend/domain/safety/food_safety_checker.py` |
| MedicalRestrictionEngine | Módulo Python en `backend/domain/safety/medical_restriction_engine.py` |
| PetProfile (Aggregate) | Módulo Python en `backend/domain/aggregates/pet_profile.py` |
| NutritionPlan (Aggregate) | Módulo Python en `backend/domain/aggregates/nutrition_plan.py` |

**Servidor**: Hetzner CPX31 (Ashburn VA) — FastAPI + Uvicorn en Docker (ver `_shared/hetzner-infrastructure.md`)

### Storage

Domain core NO persiste datos. No tiene repositorios propios — eso es responsabilidad de
`infrastructure/db/` que implementa las interfaces definidas en `application/interfaces/`.

### LLM

Domain core NO llama LLMs. Las constantes de toxicidad y restricciones son **Python dicts/sets**.

### Contenedor Docker

```dockerfile
# El domain core no requiere dependencias adicionales en el Dockerfile
# Forma parte del contenedor backend estándar
FROM python:3.11-slim
COPY backend/ /app/backend/
# domain/ = Python puro, sin pip install extra
```

### Variables de Entorno Requeridas

**NINGUNA**. Domain core es stateless y libre de configuración externa.

## Notas Arquitecturales

1. Las listas `TOXIC_DOGS`, `TOXIC_CATS` y `RESTRICTIONS_BY_CONDITION` están en código fuente,
   no en base de datos. Esto es una decisión arquitectural deliberada (ADR-002): la seguridad
   clínica no puede depender de conectividad de red ni de una DB que podría estar caída.

2. Si en el futuro se requiere administrar estas listas via UI, se implementará un mecanismo
   de "pending changes" que requiera deploy para activarse — nunca modificación en runtime.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- ADR-002: toxicidad hard-coded en domain layer
