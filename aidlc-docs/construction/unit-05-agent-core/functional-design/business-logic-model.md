# Business Logic Model — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos del Agent Core (LangGraph)

### Flujo Principal: Orquestador

```
Input: NutriVetState (session_id, pet_id, user_message, tier)
  ↓
Nodo 1: load_context
  - Cargar PetProfile desde DB (usando pet_id)
  - Cargar plan activo si existe
  - Cargar últimas 10 conversaciones del pet
  - Poblar state: pet_profile, active_plan, n_conditions
  ↓
Nodo 2: classify_intent (IntentClassifier)
  - Detectar emergencia: check EMERGENCY_KEYWORDS → is_emergency=True
  - Si emergencia → STOP, enrutar a referral_node
  - Detectar consulta médica: check MEDICAL_KEYWORDS → intent=MEDICAL_QUERY
  - Si no → intent=NUTRITIONAL_QUERY o PLAN_GENERATION
  - Poblar state: intent, is_emergency
  ↓
Nodo 3: route (condicional)
  - EMERGENCY         → referral_node (inmediato)
  - MEDICAL_QUERY     → referral_node
  - PLAN_GENERATION   → plan_generation_subgraph
  - NUTRITIONAL_QUERY → consultation_subgraph
  ↓
Nodo 4: persist_traces
  - INSERT AgentTrace para cada LLM call del recorrido
  ↓
Output: NutriVetState con agent_response populated
```

### Subgrafo: PlanGenerationSubgraph

```
Input: NutriVetState (con pet_profile, tier, modalidad)
  ↓
Nodo 1: validate_plan_request
  - Verificar límites de tier para planes
  - Verificar no hay plan ACTIVE/PENDING_VET existente
  ↓
Nodo 2: enqueue_plan_job
  - Llamar PlanGenerationUseCase.request_plan()
  - Obtener job_id
  ↓
Nodo 3: hitl_router
  - Si n_conditions > 0 → informar al usuario que plan irá a revisión vet
  - Si n_conditions == 0 → informar que el plan se generará directamente
  ↓
Output: state.plan_job_id, state.agent_response con instrucciones de polling
```

### Nodo: ReferralNode

```
Input: NutriVetState (con intent, is_emergency)
  ↓
1. Si is_emergency:
   mensaje = "URGENCIA MÉDICA: Lleva inmediatamente a tu mascota al veterinario."
             + "Contacto BAMPYSVET: [número]"
             + "No administres medicamentos sin indicación veterinaria."
2. Si MEDICAL_QUERY:
   mensaje = "Esta consulta requiere evaluación veterinaria."
             + "Tu veterinario de confianza puede orientarte."
             + "NutriVet.IA no reemplaza el diagnóstico médico."
3. state.agent_response = AgentResponse(
       response_type="emergency_referral" o "referral",
       content=mensaje,
       emergency=is_emergency
   )
Output: NutriVetState con referral response
```

### ConsultationSubgraph (Stub para Fase 1, completo en Fase 2)

```
Input: NutriVetState
  ↓
Nodo 1: freemium_gate
  - Verificar quota del tier (free: 3/día)
  - Si excedido → respuesta de upgrade, no llamar LLM
  ↓
Nodo 2: build_context_prompt
  - Construir system prompt con perfil nutricional del pet (sin PII)
  - Agregar historial de conversación
  ↓
Nodo 3: llm_respond
  - Llamar OpenRouter con streaming
  - Registrar AgentTrace
  ↓
Nodo 4: increment_quota
  - Incrementar contador Redis para el pet_id del día
Output: state.agent_response con texto de respuesta nutricional
```
