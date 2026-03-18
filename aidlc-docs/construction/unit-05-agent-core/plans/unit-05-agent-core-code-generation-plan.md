# Plan: Code Generation — Unit 05: agent-core

**Unidad**: unit-05-agent-core
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar el orquestador LangGraph: NutriVetState TypedDict, IntentClassifier,
ReferralNode, HITLRouter, Plan Generation Subgraph completo (10 nodos), y stubs
para consultation/scanner.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.

---

## Pasos de Implementación

### Paso 1 — Estructura de Carpetas

- [ ] `backend/infrastructure/agent/__init__.py`
- [ ] `backend/infrastructure/agent/orchestrator.py` — wiring del grafo LangGraph
- [ ] `backend/infrastructure/agent/state.py` — NutriVetState TypedDict
- [ ] `backend/infrastructure/agent/nodes/__init__.py`
- [ ] `backend/infrastructure/agent/nodes/emergency_detector.py`
- [ ] `backend/infrastructure/agent/nodes/intent_classifier.py`
- [ ] `backend/infrastructure/agent/nodes/referral_node.py`
- [ ] `backend/infrastructure/agent/nodes/hitl_router.py`
- [ ] `backend/infrastructure/agent/subgraphs/__init__.py`
- [ ] `backend/infrastructure/agent/subgraphs/plan_generation.py` — 10 nodos completos
- [ ] `backend/infrastructure/agent/subgraphs/consultation.py` — stub
- [ ] `backend/infrastructure/agent/subgraphs/scanner.py` — stub
- [ ] `tests/agent/test_orchestrator.py` (vacío)
- [ ] `tests/agent/test_nodes.py` (vacío)
- [ ] `tests/agent/test_plan_subgraph.py` (vacío)

### Paso 2 — Tests RED: Nodos del Orquestador

- [ ] Escribir `tests/agent/test_nodes.py`:
  - `test_intent_consultation` — mensaje nutricional → intent "consultation"
  - `test_intent_emergencia_keyword` — "convulsión" → "emergency" (sin LLM, mock verifica no llamado)
  - `test_intent_plan_generation` — "quiero un plan" → "plan_generation"
  - `test_referral_medica` — intent "referral" → mensaje estructurado con contacto vet
  - `test_emergencia_no_cuota` — emergency no decrementa cuota de preguntas
  - `test_referral_incluye_accion_urgente_si_emergencia`
  - `test_referral_no_incluye_accion_si_no_emergencia`
- [ ] Verificar que todos FALLAN (RED)

### Paso 3 — Tests RED: Plan Generation Subgraph

- [ ] Escribir `tests/agent/test_plan_subgraph.py`:
  - `test_plan_subgraph_nrc_no_llm` — nodos 1-5 no hacen llamadas LLM (mock verifica)
  - `test_plan_valida_output_post_llm` — nodo 7 rechaza plan con ingrediente tóxico
  - `test_plan_sano_active_directo` — sin condición → ACTIVE (nodo 9)
  - `test_plan_condicion_pending_vet` — con condición → PENDING_VET (nodo 9)
  - `test_plan_acumula_traces` — state["agent_traces"] tiene trazas al final

### Paso 4 — Tests RED: Orquestador Completo

- [ ] Escribir `tests/agent/test_orchestrator.py`:
  - `test_orquestador_carga_contexto` — pet_profile y active_plan en state tras load_context
  - `test_routing_4_intents` — cada intent enruta al subgrafo correcto
  - `test_emergency_bypass_llm` — emergency no llama intent_classifier (mock verifica)
  - `test_stub_consultation_retorna_respuesta` — stub no retorna None
  - `test_stub_scanner_retorna_respuesta` — stub no retorna None
- [ ] Verificar que todos FALLAN (RED)

### Paso 5 — GREEN: NutriVetState y Nodos Base

- [ ] Implementar `NutriVetState` TypedDict con todos los campos tipados
- [ ] Implementar `EMERGENCY_KEYWORDS` frozenset (emergency_detector.py)
- [ ] Implementar `emergency_detector` node (determinístico, < 1ms)
- [ ] Implementar `intent_classifier` node (usa LLM via OpenRouterClient)
- [ ] Implementar `referral_node` (determinístico, sin LLM)
- [ ] Implementar `hitl_router` node (evalúa requires_vet_review())
- [ ] Implementar stubs: `consultation_subgraph`, `scanner_subgraph`
- [ ] Verificar que tests de nodos PASAN

### Paso 6 — GREEN: Plan Generation Subgraph (10 Nodos)

- [ ] Nodo 1: `load_context` — carga PetProfile + active_plan desde DB
- [ ] Nodo 2: `calculate_nutrition` — invoca NRCCalculator (sin LLM)
- [ ] Nodo 3: `apply_restrictions` — invoca MedicalRestrictionEngine (sin LLM)
- [ ] Nodo 4: `check_safety_pre` — FoodSafetyChecker pre-LLM (valida alergias)
- [ ] Nodo 5: `select_llm` — LLMRouter.select_model() (determinístico)
- [ ] Nodo 6: `generate_with_llm` — OpenRouterClient.generate()
- [ ] Nodo 7: `validate_output` — FoodSafetyChecker post-LLM (valida output)
- [ ] Nodo 8: `generate_substitutes` — genera substitute_set aprobado
- [ ] Nodo 9: `determine_hitl` — requires_vet_review() → PENDING_VET o ACTIVE
- [ ] Nodo 10: `persist_and_notify` — persiste plan + secciones + traces + notifica
- [ ] Verificar que tests del plan subgraph PASAN

### Paso 7 — LangGraph Graph Wiring

- [ ] Implementar `build_orchestrator()` en `orchestrator.py`:
  ```
  START → load_context → emergency_detector
    → conditional: emergency → referral_node → END
    → intent_classifier
    → conditional_edges: 4 intents → 4 subgrafos/nodos
    → cada subgrafo → END
  ```
- [ ] Compilar grafo con `graph.compile()`
- [ ] Crear singleton `ORCHESTRATOR` para reutilizar entre requests

### Paso 8 — FastAPI Endpoint

- [ ] Implementar `POST /v1/agent/process` en `presentation/routers/agent_router.py`:
  ```python
  @router.post("/v1/agent/process")
  async def process(request: AgentRequest, current_user: User = Depends(...)):
      initial_state = build_initial_state(request, current_user)
      result = await ORCHESTRATOR.ainvoke(initial_state)
      return AgentResponse.from_state(result)
  ```
- [ ] Definir `AgentRequest` y `AgentResponse` schemas (Pydantic)

### Paso 9 — Cobertura y Calidad

- [ ] `pytest --cov=backend/infrastructure/agent tests/agent/ --cov-fail-under=80`
- [ ] `ruff check backend/infrastructure/agent/` → 0 errores
- [ ] `bandit -r backend/infrastructure/agent/` → 0 HIGH/MEDIUM
- [ ] Verificar que NutriVetState tiene type hints en todos los campos (mypy o manualmente)
- [ ] Confirmar que emergency detection < 1ms (pytest-benchmark en test de nodo)

---

## Criterios de Done

- [ ] Orquestador enruta correctamente los 4 intents + emergency
- [ ] Emergency detection < 1ms, sin LLM
- [ ] Plan generation subgraph produce RER/DER determinístico (Sally ±0.5 kcal)
- [ ] Validación post-LLM rechaza ingredientes tóxicos (nodo 7)
- [ ] Stubs de consultation y scanner retornan respuestas válidas (no None)
- [ ] FastAPI endpoint `POST /v1/agent/process` funcional
- [ ] Cobertura ≥ 80%, ruff + bandit sin errores

## Tiempo Estimado

5-6 días (LangGraph wiring + 10 nodos del plan subgraph + TDD)

## Dependencias

- Unit 01: NRCCalculator, FoodSafetyChecker, MedicalRestrictionEngine
- Unit 02: JWT middleware, RBAC
- Unit 03: PetProfile aggregate (para load_context)
- Unit 04: LLMRouter, OpenRouterClient, IPlanRepository, IAgentTraceRepository

## Referencias

- Unit spec: `inception/units/unit-05-agent-core.md`
- ADR-019: LLM routing
- Constitution: REGLA 1, 2, 3, 4, 9
- Construction rules: `.claude/rules/02-construction.md`
