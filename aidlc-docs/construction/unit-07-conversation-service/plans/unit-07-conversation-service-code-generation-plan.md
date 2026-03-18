# Plan: Code Generation — Unit 07: conversation-service

**Unidad**: unit-07-conversation-service
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Reemplazar el stub del consultation subgraph con la implementación completa: QueryClassifier,
NutritionalResponder con SSE streaming, FreemiumGateChecker y historial persistente por pet_id.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.

---

## Pasos de Implementación

### Paso 1 — Estructura de Archivos

- [ ] `backend/infrastructure/agent/nodes/query_classifier.py` — NUTRITIONAL/MEDICAL/EMERGENCY
- [ ] `backend/infrastructure/agent/nodes/nutritional_responder.py` — SSE streaming
- [ ] `backend/infrastructure/agent/nodes/freemium_gate.py` — cuota Free tier
- [ ] `backend/infrastructure/agent/subgraphs/consultation.py` — REEMPLAZA stub de unit-05
- [ ] `backend/infrastructure/db/conversation_repository.py`
- [ ] `backend/infrastructure/db/agent_quota_repository.py`
- [ ] `backend/presentation/schemas/chat_schemas.py`
- [ ] `tests/conversation/test_query_classifier.py` (vacío)
- [ ] `tests/conversation/test_freemium_gate.py` (vacío)
- [ ] `tests/conversation/test_conversation_subgraph.py` (vacío)

### Paso 2 — Tests RED: QueryClassifier

- [ ] Escribir `tests/conversation/test_query_classifier.py`:
  - `test_consulta_nutricional_respondida` — "¿proteínas para mi perro?" → NUTRITIONAL
  - `test_consulta_medica_remite_vet` — "vomitó 3 veces" → MEDICAL
  - `test_consulta_medicamentos_medica` — "¿qué dosis le doy?" → MEDICAL
  - `test_consulta_diagnostico_medica` — "creo que tiene infección" → MEDICAL
  - `test_emergencia_detectada_antes_llm` — "convulsión" → EMERGENCY (sin LLM)
  - `test_aliases_regionales_respondidos` — "ahuyama" acepta y responde
  - `test_disclaimer_en_toda_respuesta` — NUTRITIONAL y MEDICAL incluyen disclaimer
  - `test_historial_como_contexto` — últimos 10 mensajes en system prompt
- [ ] Verificar que todos FALLAN (RED)

### Paso 3 — Tests RED: FreemiumGate

- [ ] Escribir `tests/conversation/test_freemium_gate.py`:
  - `test_emergencia_no_cuota` — emergency no decrementa ni verifica cuota
  - `test_free_bloquea_9_preguntas` — décima pregunta → upgrade gate (total)
  - `test_free_3_por_dia` — cuarta pregunta del día → upgrade gate (diario)
  - `test_reset_diario` — día siguiente → cuota diaria reseteada
  - `test_tier_basico_sin_limite` — Básico: sin gate
  - `test_cuota_atomica` — concurrent requests → no supera el límite
  - `test_emergencia_bypass_cuota_agotada` — Free con 9/9 puede hacer emergencia
- [ ] Verificar que todos FALLAN (RED)

### Paso 4 — Tests RED: Conversation Subgraph

- [ ] Escribir `tests/conversation/test_conversation_subgraph.py`:
  - `test_flujo_nutricional_completo` — consulta → SSE stream → disclaimer en último evento
  - `test_flujo_medico_remite` — consulta médica → mensaje de remisión sin LLM nutrition
  - `test_sse_primer_token_disponible` — primer token en stream (test de integration)
  - `test_historial_guardado_post_respuesta` — conversation guardado en DB
- [ ] Verificar que todos FALLAN (RED)

### Paso 5 — GREEN: QueryClassifier

- [ ] Implementar `query_classifier.py`:
  - Emergency detection: reutiliza `EMERGENCY_KEYWORDS` frozenset de unit-05 (determinístico)
  - Classification: LLM call para NUTRITIONAL vs MEDICAL (prompt de clasificación)
  - Default si LLM falla: `NUTRITIONAL` (comportamiento seguro)

### Paso 6 — GREEN: FreemiumGateChecker

- [ ] Implementar `AgentQuotaRepository`:
  - `get_or_create(user_id)` — crea si no existe
  - `increment(user_id)` — atómico (UPDATE con check)
  - `reset_daily(user_id)` — reset daily_count si nuevo día
- [ ] Implementar `freemium_gate.py`:
  - Emergencias: bypass incondicional
  - Tier pagado: bypass
  - Free: check daily + total → gate si excede
  - Decremento ANTES del LLM call

### Paso 7 — GREEN: NutritionalResponder con SSE

- [ ] Implementar `nutritional_responder.py`:
  - `build_system_prompt(pet_profile)` — contexto del pet
  - `build_conversation_context(pet_id, limit=10)` — historial desde DB
  - `stream_response(messages, model)` — async generator via OpenRouter streaming
  - Disclaimer en último evento SSE
- [ ] Implementar streaming en `OpenRouterClient`:
  - `stream(messages, model)` — async generator de chunks

### Paso 8 — GREEN: ConsultationSubgraph (reemplaza stub)

- [ ] Implementar `consultation.py`:
  - Nodo 1: `emergency_check` (determinístico)
  - Nodo 2: `freemium_gate` (cuota)
  - Nodo 3: `query_classifier` (LLM — NUTRITIONAL/MEDICAL)
  - Nodo 4a: `nutritional_responder` (SSE stream — si NUTRITIONAL)
  - Nodo 4b: `referral_node` (mensaje estructurado — si MEDICAL/EMERGENCY)
  - Nodo 5: `persist_conversation` (guarda mensaje + respuesta en DB)

### Paso 9 — Alembic Migrations

- [ ] `alembic revision -m "014_conversations"` → tabla conversations + índice
- [ ] `alembic revision -m "015_agent_quotas"` → tabla agent_quotas + UNIQUE index
- [ ] Revisar migraciones generadas
- [ ] Confirmar con Sadid antes de `alembic upgrade head` en staging

### Paso 10 — FastAPI Endpoint

- [ ] Implementar `POST /v1/agent/chat` → SSE StreamingResponse:
  ```python
  return StreamingResponse(
      generate_sse(request, current_user),
      media_type="text/event-stream",
      headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
  )
  ```
- [ ] System prompt contextualizado con `pet_name + conditions + plan` (ADR-021)
- [ ] Verificar headers de SSE correctos para pasar por Caddy reverse proxy

### Paso 11 — Cobertura y Calidad

- [ ] `pytest --cov=backend/infrastructure/agent/subgraphs/consultation tests/conversation/ --cov-fail-under=80`
- [ ] G3 test set: `pytest tests/conversation/test_g3_classification.py` — 95% mínimo
- [ ] `ruff check backend/` → 0 errores
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM
- [ ] Test de disclaimer: ninguna respuesta sin disclaimer

---

## Criterios de Done

- [ ] Stub de unit-05 reemplazado por implementación completa
- [ ] SSE streaming funcional (primer token < 1s)
- [ ] Free tier quota: 3/día × 3 días, atómica, no bypasseable
- [ ] Emergencias bypass cuota siempre
- [ ] Nunca responde consultas médicas (G3 ≥ 95%)
- [ ] Disclaimer en TODA respuesta
- [ ] Historial últimos 10 mensajes incluido en contexto LLM
- [ ] Cobertura ≥ 80%, ruff + bandit sin errores

## Tiempo Estimado

4-5 días (TDD + SSE implementation + cuota atómica + G3 test set)

## Dependencias

- Unit 01: domain value objects
- Unit 02: JWT middleware, RBAC
- Unit 03: PetProfile (para system prompt contextualizado)
- Unit 04: LLMRouter, OpenRouterClient
- Unit 05: NutriVetState, EMERGENCY_KEYWORDS, ReferralNode, consultation stub (a reemplazar)

## Referencias

- Unit spec: `inception/units/unit-07-conversation-service.md`
- ADR-021: SSE streaming
- Constitution: REGLA 8 (disclaimer), REGLA 9 (límite nutricional/médico)
- Quality Gates: G3
