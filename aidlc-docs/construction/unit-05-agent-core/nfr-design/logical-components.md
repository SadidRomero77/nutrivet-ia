# Logical Components — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Agent Core

### LangGraphOrchestrator
**Responsabilidad**: Compilar y ejecutar el StateGraph principal de NutriVet.IA.
**Capa**: infrastructure/agent/
**Dependencias**: LangGraph, todos los nodos y subgrafos
**Método principal**: `async invoke(state: NutriVetState) → NutriVetState`

### NutriVetState
**Responsabilidad**: Contenedor de estado compartido entre nodos.
**Capa**: domain/entities/ (TypedDict — sin dependencias externas)
**Notas**: Serializable a JSON para persistencia en Redis checkpointer.

### IntentClassifier (Nodo)
**Responsabilidad**: Clasificar intención del mensaje con lógica determinista.
**Capa**: infrastructure/agent/nodes/
**Dependencias**: QueryClassifier (domain service — sin LLM)
**Salida**: `state["intent"]`, `state["is_emergency"]`

### PlanGenerationSubgraph
**Responsabilidad**: Manejar el flujo de solicitud de generación de plan.
**Capa**: infrastructure/agent/subgraphs/
**Dependencias**: PlanGenerationUseCase, HITLRouter
**Nodos internos**: validate_request → enqueue_job → hitl_router

### ConsultationSubgraph
**Responsabilidad**: Responder consultas nutricionales con LLM + quota control.
**Capa**: infrastructure/agent/subgraphs/
**Dependencias**: FreemiumGateChecker, OpenRouterClient, Redis (quota)
**Nodos internos**: freemium_gate → build_context → llm_respond → increment_quota

### ScannerSubgraph
**Responsabilidad**: Procesar escaneos de etiquetas nutricionales (delegado a unit-06).
**Capa**: infrastructure/agent/subgraphs/
**Dependencias**: ScannerService (unit-06)

### ReferralNode
**Responsabilidad**: Generar respuesta de remisión al vet (médica y emergencias).
**Capa**: infrastructure/agent/nodes/
**Dependencias**: ninguna LLM — respuesta basada en template hard-coded
**Regla crítica**: SIEMPRE se invoca para MEDICAL_QUERY y EMERGENCY.

### HITLRouter (Nodo)
**Responsabilidad**: Determinar el status del plan según condiciones médicas del pet.
**Capa**: infrastructure/agent/nodes/
**Dependencias**: ninguna (lógica determinista del domain)
**Salida**: `"PENDING_VET"` o `"ACTIVE"` según `state["n_conditions"]`

### AgentTraceRepository (Insert-Only)
**Responsabilidad**: Persistir trazas de todos los nodos que invocan LLM.
**Capa**: infrastructure/agent/
**Regla**: Solo método `insert()`.

## Diagrama de Nodos del Grafo

```
[START]
   ↓
[load_context] → carga pet_profile, active_plan, conversaciones
   ↓
[classify_intent] → determina intent, is_emergency
   ↓ (condicional)
┌──────────────┬──────────────────┬──────────────────┐
│  EMERGENCY   │  MEDICAL_QUERY   │ PLAN_GENERATION   │  NUTRITIONAL_QUERY
│      ↓       │       ↓          │       ↓           │        ↓
│ [referral]   │  [referral]      │  [plan_subgraph]  │  [consult_subgraph]
└──────┬───────┴────────┬─────────┴─────────┬─────────┴────────┬───────────┘
       └────────────────┴──────────────────────────────────────┘
                                    ↓
                          [persist_traces]
                                    ↓
                                  [END]
```
