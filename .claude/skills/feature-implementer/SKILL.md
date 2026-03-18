# Skill: Feature Implementer

## Propósito
Implementar features de NutriVet.IA siguiendo TDD, Clean Architecture Hexagonal y las convenciones del proyecto.

## Cuándo activar
Cuando el usuario vaya a implementar una nueva funcionalidad ya definida en el PRD.

## Proceso obligatorio

### Paso 1 — Leer contexto
- Lee CLAUDE.md
- Lee docs/PRD.md de la feature a implementar
- Identifica la capa donde pertenece: Domain / Application / Infrastructure / Presentation

### Paso 2 — Diseño en Domain
Identifica y documenta en ASCII antes de escribir código:
- Entidades y Value Objects involucrados
- Reglas de negocio puras
- Interfaces de repositorio necesarias

### Paso 3 — Ciclo TDD (Red → Green → Refactor)
Para cada componente:
1. **RED**: Escribe el test primero — debe fallar
2. **GREEN**: Implementa el mínimo código para que pase
3. **REFACTOR**: Mejora sin romper tests

### Paso 4 — Orden de implementación
```
Domain (entidades + value objects)
  → Tests de dominio
Application (casos de uso + interfaces)
  → Tests de casos de uso
Infrastructure (repositorios + clientes externos)
  → Tests de integración
Presentation (FastAPI routers + Pydantic schemas)
  → Tests de endpoints
```

### Paso 5 — Checklist de salida
Antes de declarar la feature completa verificar:
- [ ] Todos los tests pasan (`pytest --cov=app tests/`)
- [ ] Cobertura mínima 80%
- [ ] Type hints en todas las funciones
- [ ] Docstrings en español en clases y métodos públicos
- [ ] Sin secrets en código
- [ ] Input validation con Pydantic en endpoints
- [ ] RBAC validado en endpoints que lo requieren
- [ ] Lint sin errores (`ruff check .`)

## Reglas críticas
- NUNCA implementar antes de tener el test
- Las restricciones nutricionales y de toxicidad son no negociables
- Si la feature toca datos médicos → agregar encriptación en reposo
- Un PR por feature, nunca mezclar features
