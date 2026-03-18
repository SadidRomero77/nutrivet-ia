# Plan: NFR Requirements — Unit 05: agent-core

**Unidad**: unit-05-agent-core
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del agent-core

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| Emergency keyword detection | < 1ms | Frozenset lookup en memoria — determinístico |
| Intent classification (LLM) | < 500ms p95 | LLM call con modelo pequeño |
| Plan generation subgraph (RER/DER) | < 5ms | Python puro — NRCCalculator |
| Plan generation subgraph (end-to-end) | p95 < 25s | LLM es el cuello de botella |
| POST /v1/agent/process | < 200ms para encolar | Async — job_id retornado inmediatamente |
| NutriVetState load_context | < 50ms | DB lookup + desencriptación Fernet |

**Regla crítica**: Los nodos deterministas (1, 2, 3, 4, 5, 7, 8, 9, 10) NUNCA deben
llamar a ningún LLM — solo el nodo 6 (`generate_with_llm`) hace llamada LLM.

### Seguridad

**Trazabilidad sin PII**:
- `agent_traces` acumuladas en `NutriVetState` durante el request.
- Al persistir: solo `pet_id` UUID — nunca nombre, especie, condiciones en texto plano.
- Nodos deben loggear con `trace_id`, no con datos de mascota.

**Integridad del estado**:
- `NutriVetState` es un TypedDict — todos los campos deben tener type hints.
- Los nodos no pueden agregar campos dinámicos al estado (disciplina LangGraph).
- El estado se considera confiable solo después de que `load_context_node` lo popula.

**Emergency bypass**:
- La detección de emergencias es anterior al clasificador LLM — no puede ser
  "inyectada" vía prompt injection en el clasificador.
- `EMERGENCY_KEYWORDS` es un frozenset en código — no configurable en runtime.

### Confiabilidad

- Si `intent_classifier` falla → default a `consultation` (comportamiento seguro).
- Si `plan_generation_subgraph` falla en nodo determinista → error controlado, no se llama LLM.
- Si LLM retorna ingrediente tóxico → nodo `validate_output` rechaza, job FAILED.
- Stubs de consultation/scanner: deben retornar respuesta válida (no None) para evitar romper el grafo.

### Mantenibilidad

- `NutriVetState` como TypedDict — cobertura 100% de campos con type hints.
- Cada nodo es una función pura (o async) con firma clara: `node(state: NutriVetState) -> NutriVetState`.
- Cobertura mínima: **80%** en agent-core.
- Tests de cada nodo de forma aislada — no solo tests del grafo completo.

## Checklist NFR agent-core

- [ ] Emergency detection < 1ms (pytest-benchmark)
- [ ] Intent classification no involucra código de emergencia (test de aislamiento)
- [ ] NutriVetState: todos los campos con type hints (verificar con mypy)
- [ ] RER/DER en plan subgraph: Sally pasa ±0.5 kcal
- [ ] Validación post-LLM: test con ingrediente tóxico en output → nodo 7 rechaza
- [ ] 0 datos PII en agent_traces (test de sanitización de prompts)
- [ ] Stubs retornan respuestas válidas (no None)
- [ ] Cobertura ≥ 80% en todos los módulos de agent-core
- [ ] `bandit -r backend/infrastructure/agent/` → 0 HIGH/MEDIUM

## Referencias

- Global: `_shared/nfr-requirements.md`
- Unit spec: `inception/units/unit-05-agent-core.md`
- Constitution: REGLA 1, 2, 3 (determinismo), REGLA 6 (sin PII en traces)
- Operations rules: `03-operations.md` (métricas P0)
