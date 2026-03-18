# Fase Construction

**Propósito**: Implementar lo diseñado en Inception, con TDD como práctica central y BDD como contrato de comportamiento.

---

## Cuándo Estás en Construction

- Escribiendo código de producción (backend Python, mobile Flutter).
- Escribiendo tests (unitarios, integración, BDD).
- Implementando migraciones de base de datos.
- Configurando CI/CD y pipelines.
- Revisando y haciendo merge de PRs.

## Principio Central de Construction

```
RED → GREEN → REFACTOR
(test falla) → (implementación mínima) → (limpieza)
```

**Orden de implementación obligatorio**:
```
1. domain/          (cero dependencias externas)
2. application/     (casos de uso)
3. infrastructure/  (PostgreSQL, LLMs, OCR)
4. presentation/    (FastAPI routers)
5. mobile/          (Flutter)
```

## Flujo de Trabajo en Construction

```
/tasks [feature]
  → Lista de tasks ordenadas con criterios de completitud
     │
     ▼
TASK-1: Escribir tests (RED phase)
  → tests/domain/test_[feature].py
     │
     ▼
TASK-2: Implementar domain/ (GREEN phase)
  → Mínimo código para pasar los tests
     │
     ▼
TASK-3+: Application, Infrastructure, Presentation
  → Tests de integración en cada capa
     │
     ▼
TASK-N: BDD → Tests automatizados
  → Escenarios de behaviors/ → tests/bdd/
     │
     ▼
Definition of Done (ver checklist.md)
     │
     ▼
PR → Code Review → Merge
```

## Herramientas

```bash
# Correr tests con cobertura
pytest --cov=app tests/ --cov-report=html

# Lint
ruff check .

# Seguridad estática
bandit -r app/

# Dependencias
safety check

# Análisis de impacto (GitNexus MCP)
# gitnexus_impact antes de editar domain/
```

## Reglas de Steering para Esta Fase

Ver `.claude/rules/02-construction.md`
