# Tech Stack Decisions — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para el Domain Core

### Python 3.12 Stdlib Only
**Decisión**: El domain layer usa exclusivamente Python 3.12 stdlib.
**Razón**: Garantiza cero acoplamiento con infraestructura. Si se necesita migrar de FastAPI a otro framework, el dominio no cambia. El dominio es la parte más estable del sistema.
**Alternativas rechazadas**: Pydantic en dominio (crea dependencia), SQLAlchemy en dominio (viola Clean Architecture).

### dataclasses (frozen=True) para Value Objects
**Decisión**: Usar `@dataclass(frozen=True)` para todos los value objects.
**Razón**: Inmutabilidad nativa de Python, sin dependencias externas. Hashable por defecto (útil para sets y dicts).
**Alternativas rechazadas**: `NamedTuple` (menos expresivo), `attrs` (dependencia externa), Pydantic (dependencia externa + overhead).

### Decimal para Cálculos Calóricos
**Decisión**: `from decimal import Decimal` para RER/DER y todos los valores calóricos.
**Razón**: Precisión numérica exacta. El caso Sally requiere ±0.5 kcal. `float` tiene errores de representación que pueden acumular y violar este umbral.
**Alternativas rechazadas**: `float` (errores de punto flotante inaceptables para cálculos clínicos).

### pytest para Tests del Domain
**Decisión**: pytest como framework de testing.
**Razón**: Estándar de facto en Python. Compatible con `--cov` para cobertura. Fixtures simples para instanciar objetos de dominio.
**Librerías de test**: pytest, pytest-cov, pytest-asyncio (para ports async).

### frozenset para Listas de Tóxicos y Restricciones
**Decisión**: `TOXIC_DOGS: frozenset[str]`, `TOXIC_CATS: frozenset[str]`.
**Razón**: Búsqueda O(1) vs. O(n) en lista. Inmutabilidad garantizada en runtime. No es posible agregar un ingrediente accidentalmente.

### Enum para Estados y Tipos
**Decisión**: `class PlanStatus(str, Enum)` para todos los estados del dominio.
**Razón**: Type-safe. Serializable a string directamente (compatible con PostgreSQL y JSON). Previene typos en comparaciones.

### ABC para Ports (Repository Interfaces)
**Decisión**: `from abc import ABC, abstractmethod` para definir ports.
**Razón**: Contrato explícito que la infraestructura debe implementar. El `abstractmethod` garantiza que no se puede instanciar el port directamente. Compatible con type hints estrictos.

## Lo que NO se usa en Domain

| Tecnología | Razón de Exclusión |
|------------|-------------------|
| FastAPI | Capa de presentación — no pertenece al dominio |
| SQLAlchemy | Capa de infraestructura — no pertenece al dominio |
| Pydantic | Se usa en presentación para schemas HTTP, no en dominio para entidades |
| Redis | Capa de infraestructura — el dominio no tiene estado en caché |
| httpx / requests | El dominio no hace llamadas HTTP |
| LangChain / LangGraph | Capa de infraestructura del agente |
| cryptography (AES) | Encriptación en capa de infraestructura (PostgreSQL) |
| boto3 | Acceso a R2/S3 — infraestructura |
