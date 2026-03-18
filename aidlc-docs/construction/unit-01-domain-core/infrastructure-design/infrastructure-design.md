# Infrastructure Design — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Principio: Cero Dependencias Externas

El domain core sigue la regla de Clean Architecture: la capa de dominio no depende de ninguna infraestructura.

```
domain/  ←  NO importa:
  - FastAPI
  - SQLAlchemy
  - Redis
  - httpx / requests
  - boto3
  - LangChain / LangGraph
  - OpenRouter
  - cryptography (AES)
  Sólo Python 3.12 stdlib: dataclasses, decimal, datetime, enum, typing, uuid
```

## Estructura de Módulos del Domain Core

```
app/domain/
├── __init__.py
├── nutrition/
│   ├── __init__.py
│   ├── nrc_calculator.py        ← RER/DER determinista
│   └── factors.py               ← Tablas de factores DER
├── safety/
│   ├── __init__.py
│   ├── toxic_foods.py           ← TOXIC_DOGS, TOXIC_CATS (constantes)
│   ├── medical_restrictions.py  ← RESTRICTIONS_BY_CONDITION (constantes)
│   └── food_safety_checker.py   ← FoodSafetyChecker service
├── entities/
│   ├── __init__.py
│   ├── user_account.py
│   ├── pet_profile.py
│   ├── nutrition_plan.py
│   ├── conversation_session.py
│   └── label_scan.py
├── value_objects/
│   ├── __init__.py
│   ├── age_vo.py
│   ├── activity_level_vo.py
│   ├── medical_condition_vo.py
│   ├── plan_status.py
│   └── nrc_result.py
├── exceptions/
│   ├── __init__.py
│   ├── toxic_ingredient_error.py
│   ├── medical_restriction_error.py
│   └── invariant_error.py
├── routing/
│   ├── __init__.py
│   ├── llm_router.py            ← LLM routing logic (domain, no HTTP)
│   └── query_classifier.py      ← Intent + emergency detection
└── ports/
    ├── __init__.py
    ├── pet_repository.py        ← Interface (abstract)
    ├── plan_repository.py       ← Interface (abstract)
    └── user_repository.py       ← Interface (abstract)
```

## Interfaces (Ports)

Los ports son clases abstractas en `domain/ports/` que definen contratos para la infraestructura.
La implementación concreta vive en `infrastructure/`.

```python
# domain/ports/pet_repository.py
from abc import ABC, abstractmethod
from uuid import UUID
from app.domain.entities.pet_profile import PetProfile

class PetRepositoryPort(ABC):
    """Puerto de repositorio para PetProfile."""

    @abstractmethod
    async def get_by_id(self, pet_id: UUID) -> PetProfile | None:
        """Obtener perfil de mascota por ID."""
        ...

    @abstractmethod
    async def save(self, pet: PetProfile) -> None:
        """Persistir perfil de mascota."""
        ...
```

## Excepciones del Dominio

```python
# domain/exceptions/toxic_ingredient_error.py
class ToxicIngredientError(Exception):
    """Lanzada cuando un ingrediente está en la lista de tóxicos."""
    def __init__(self, ingredient: str, especie: str):
        self.ingredient = ingredient
        self.especie = especie
        super().__init__(f"Ingrediente tóxico para {especie}: {ingredient}")

class MedicalRestrictionViolationError(Exception):
    """Lanzada cuando un ingrediente viola una restricción médica."""
    ...

class DomainInvariantError(Exception):
    """Lanzada cuando se viola una invariante del dominio."""
    ...
```
