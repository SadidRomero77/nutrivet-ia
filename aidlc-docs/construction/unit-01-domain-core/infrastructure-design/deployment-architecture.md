# Deployment Architecture — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Ubicación en el Deployment

El domain core NO es un servicio independiente. Es una capa de código Python que reside dentro del contenedor `nutrivet-backend`.

```
Hetzner CPX31 (Ashburn VA)
└── Coolify (orquestador Docker)
    └── nutrivet-backend (Docker container)
        ├── presentation/   ← FastAPI + Uvicorn (expuesto)
        ├── application/    ← Casos de uso
        ├── infrastructure/ ← PostgreSQL, Redis, OpenRouter clients
        └── domain/         ← unit-01-domain-core (este módulo)
            ├── nutrition/
            │   └── nrc_calculator.py
            ├── safety/
            │   ├── toxic_foods.py
            │   └── medical_restrictions.py
            ├── entities/
            │   ├── pet_profile.py
            │   ├── nutrition_plan.py
            │   └── ...
            └── value_objects/
```

## Dependencias del Contenedor

El domain layer tiene CERO dependencias externas. Solo Python 3.12 stdlib.
- No requiere acceso a PostgreSQL.
- No requiere acceso a Redis.
- No realiza llamadas HTTP.
- No importa FastAPI, SQLAlchemy, ni ninguna librería de terceros.

## Build y CI

```dockerfile
# El domain core se valida en CI antes de build
FROM python:3.12-slim AS test
WORKDIR /app
COPY requirements-test.txt .
RUN pip install -r requirements-test.txt
COPY app/domain ./app/domain
COPY tests/domain ./tests/domain
RUN pytest --cov=app/domain tests/domain/ --cov-fail-under=80
```

## Pruebas en CI (GitHub Actions)

```yaml
# .github/workflows/test-domain.yml
- name: Test domain layer
  run: pytest --cov=app/domain tests/domain/ --cov-fail-under=80
- name: Golden case Sally
  run: pytest tests/domain/test_nrc_calculator.py::test_sally_golden_case -v
- name: Toxicity safety tests
  run: pytest tests/domain/test_toxic_foods.py -v
```

## Consideraciones de Deploy

- El domain layer nunca se despliega de forma independiente.
- Cambios en domain/ requieren re-build del contenedor `nutrivet-backend`.
- No hay estado en runtime en el domain layer (stateless puro).
- Las constantes `TOXIC_DOGS`, `TOXIC_CATS`, `RESTRICTIONS_BY_CONDITION` son parte del código, no configuración externa.
- Actualizar estas listas requiere un nuevo deploy con commit documentado: `security: update toxic_foods - [razón]`.
