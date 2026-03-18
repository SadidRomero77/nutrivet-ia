# Logical Components — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Conversation Service

### ConversationUseCase
**Responsabilidad**: Orquestar el flujo de chat SSE: gate → classify → stream → persist.
**Capa**: application/conversation/
**Dependencias**: FreemiumGateChecker, QueryClassifier, OpenRouterStreamingClient, RedisQuotaClient, ConversationRepositoryPort
**Método principal**:
```
async stream_response(pet_id, owner_id, message, tier) → AsyncIterator[str]
```

### FreemiumGateChecker
**Responsabilidad**: Verificar si el usuario puede hacer una pregunta según su tier y quota.
**Capa**: application/conversation/
**Dependencias**: RedisQuotaClient, AgentQuotaRepositoryPort
**Método**:
```
check_gate(pet_id, owner_id, tier) → FreemiumGate
```
**Regla**: Emergencias siempre pasan. Referrals médicos siempre pasan.

### ConsultationSubgraph (LangGraph)
**Responsabilidad**: Subgrafo que construye el contexto y hace el streaming SSE.
**Capa**: infrastructure/conversation/
**Dependencias**: OpenRouterStreamingClient, NRCCalculator, ConversationRepository

### OpenRouterStreamingClient
**Responsabilidad**: Streaming HTTP de OpenRouter con `httpx` async.
**Capa**: infrastructure/conversation/
**Implementa**: LLMStreamingClientPort

### RedisQuotaClient
**Responsabilidad**: INCR atómico de quota con TTL 24h en Redis.
**Capa**: infrastructure/conversation/
**Operaciones**: increment_quota, get_quota, check_upgrade_required

### PostgreSQLConversationRepository
**Responsabilidad**: Persistencia de messages y sessions en PostgreSQL.
**Capa**: infrastructure/conversation/
**Métodos**:
```
save_message(message: ConversationMessage) → None
get_recent_by_pet(pet_id, limit) → list[ConversationMessage]
save_quota(quota: AgentQuota) → None
get_quota_status(pet_id, date) → AgentQuota | None
```

### AgentRouter (SSE Endpoint)
**Responsabilidad**: FastAPI endpoint que envuelve el stream del use case en SSE.
**Capa**: presentation/agent/
**Endpoints**:
```
POST /agent/chat                       → SSE stream
GET  /pets/{pet_id}/conversations      → list[ConversationMessage]
GET  /pets/{pet_id}/agent-quota        → QuotaStatus
```

## Diagrama de Flujo

```
POST /agent/chat
    ↓
ConversationUseCase.stream_response()
    ↓
FreemiumGateChecker.check_gate()
    ├── gate.allowed=False → yield upgrade_message, STOP
    └── gate.allowed=True → continuar
    ↓
QueryClassifier.classify()
    ├── EMERGENCY → yield referral_emergency, STOP
    ├── MEDICAL   → yield referral_medical, STOP
    └── NUTRITIONAL → continuar
    ↓
ConsultationSubgraph
    ├── build_context_prompt (NRC + historial)
    └── OpenRouterStreamingClient.stream_complete()
              ↓ chunks
         SSE: data: {"chunk": "..."}
    ↓ (post-stream)
RedisQuotaClient.increment_quota()
PostgreSQLConversationRepository.save_message()
PostgreSQLAgentTraceRepository.insert()
```
