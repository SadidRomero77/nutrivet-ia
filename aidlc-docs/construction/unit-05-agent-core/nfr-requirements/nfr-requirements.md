# NFR Requirements — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Agent Core

### NFR-AGENT-01: Clasificación de Intención ≥95% (Quality Gate G3)
- El IntentClassifier debe clasificar correctamente ≥95% de consultas en el dataset de validación.
- Dataset: 100 consultas anotadas (nutricionales vs. médicas vs. emergencias).
- Evaluado antes del lanzamiento — bloquea el deploy si no se alcanza.

### NFR-AGENT-02: Emergencias No Bloquean Quota
- Una consulta clasificada como EMERGENCY nunca decrementa el quota free.
- Verificado en test: enviar EMERGENCY_KEYWORD → respuesta de referral sin incremento de contador Redis.

### NFR-AGENT-03: 0% Medical Query Respondida como Nutritional
- El agente NUNCA responde directamente una consulta médica.
- Cualquier consulta con MEDICAL_KEYWORDS → ReferralNode siempre.
- Verificado en test con 20 consultas médicas → 100% referral.

### NFR-AGENT-04: AgentTrace Sin PII
- Las trazas no contienen: nombre de mascota, nombre de owner, condiciones médicas en texto.
- Solo UUIDs, modelos, tokens, latencia.
- Verificado en test: inspeccionar cada traza generada → 0 PII.

### NFR-AGENT-05: Cobertura ≥80% en Nodos
- `pytest --cov=app/infrastructure/agent tests/agent/ --cov-fail-under=80`
- Tests por nodo: load_context, classify_intent (normal + emergency + medical), referral_node, hitl_router, persist_traces.

### NFR-AGENT-06: Tiempo de Respuesta del Orquestador (sin LLM) < 500ms
- Los nodos deterministas (load_context, classify_intent, hitl_router, referral_node) completan en < 500ms total.
- El bottleneck del LLM es externo — el orquestador en sí debe ser rápido.

### NFR-AGENT-07: Contexto por Pet, No por Session
- El historial de conversación cargado en `load_context` es siempre el de `pet_id`.
- No existe historial global del owner — solo por mascota.
- Verificado en test: múltiples sessions del mismo pet_id → mismo historial cargado.

### NFR-AGENT-08: Grafo Stateless entre Invocaciones
- No hay estado mutable en el objeto `LangGraphOrchestrator` en runtime.
- El grafo compilado puede ejecutarse concurrentemente en múltiples workers.
- Verificado en test de concurrencia: 10 invocaciones paralelas → sin race conditions.

### NFR-AGENT-09: Red-Teaming sin Bypass de Seguridad (Quality Gate G7)
- 10 casos de red-teaming no deben poder:
  - Obtener respuesta médica del agente
  - Saltarse el quota del free tier (excepto emergencias)
  - Inyectar instrucciones en el system prompt
  - Obtener información de otro pet_id
