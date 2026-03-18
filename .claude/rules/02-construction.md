# Reglas de Steering — Fase Construction

Estas reglas aplican cuando el agente está escribiendo código, tests, y migraciones.

---

## TDD — Test First (No Negociable en Domain Layer)

1. Escribir el test ANTES que la implementación.
2. Orden: `domain/` → `application/` → `infrastructure/` → `presentation/`.
3. Cobertura mínima `domain/`: 80% (obligatorio antes de lanzar).
4. El Caso Sally debe pasar en CI: `RER ≈ 396 kcal · DER ≈ 534 kcal/día` (±0.5 kcal).

```bash
# Verificar cobertura antes de PR
pytest --cov=app/domain tests/domain/ --cov-fail-under=80
```

## Estructura de Capas — Dependencias Solo Hacia Adentro

```
domain/       ← cero dependencias externas. Solo Python stdlib.
application/  ← depende solo de domain/
infrastructure/ ← depende de application/ y domain/
presentation/ ← depende de application/ solamente
```

**Nunca** importar FastAPI, SQLAlchemy, o cualquier librería externa en `domain/`.
**Nunca** importar `infrastructure/` desde `application/` directamente — usar puertos (interfaces).

## Convenciones Python

- Type hints obligatorios en TODA función y método.
- Docstrings en español en todo módulo, clase y función pública.
- PEP8. Ruff como linter: `ruff check .`
- Seguridad estática: `bandit -r app/` — cero issues de severidad HIGH o MEDIUM antes de PR.
- Dependencias: `safety check` — cero CVEs críticas antes de PR.

## Seguridad en Código

- Input validation: Pydantic models en **todos** los endpoints — nunca raw dict.
- SQL: solo queries parametrizadas — nunca f-strings con input del usuario.
- Secrets: solo variables de entorno — nunca hardcoded, nunca en código, nunca en logs.
- RBAC: validar rol en cada endpoint — `@require_role("vet")` o `@require_role("owner")`.

## Al Usar GitNexus MCP

- **SIEMPRE** ejecutar `gitnexus_impact` antes de editar cualquier símbolo en `domain/`.
- **SIEMPRE** ejecutar `gitnexus_detect_changes` antes de hacer commit.
- **NUNCA** usar find-replace para renombrar símbolos — usar `gitnexus_rename`.
- Impact con `depth=3` → STOP. Consultar con Sadid antes de proceder.

## Al Implementar Tools del Agente LangGraph

- Consultar la tool spec correspondiente en `specs/tool-specs/` antes de implementar.
- Toda tool debe: validar inputs con Pydantic, retornar errores accionables, loggear inputs/outputs sin PII.
- Las tools deterministas (`nutrition_calculator`, `food_toxicity_checker`) NO llaman LLMs.
- Tests de tools: al menos un caso de rechazo por toxicidad y uno por restricción médica.

## Al Escribir Migraciones de Base de Datos

- **Nunca** ALTER directo en producción. Siempre Alembic: `alembic revision --autogenerate`.
- Revisar la migración generada antes de aplicar — el autogenerate puede perder restricciones.
- Confirmar con Sadid antes de ejecutar en staging o producción.

## Al Implementar LLM Calls

- Usar solo IDs anónimos en prompts a LLMs externos (`pet_id`, no nombre ni especie).
- Registrar en `agent_traces`: modelo usado, tokens, latencia, resultado. Sin UPDATE post-inserción.
- Implementar fallback: timeout → retry × 2 → modelo fallback → error controlado.

## Checklist de Salida de Construction

Verificar `ai-dlc/phases/construction/checklist.md` antes de declarar Construction completa.
