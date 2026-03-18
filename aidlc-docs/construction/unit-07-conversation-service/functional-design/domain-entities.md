# Domain Entities — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Conversation Service

### ConversationSession
- `session_id: UUID`
- `pet_id: UUID` — historial por mascota, no por sesión
- `owner_id: UUID`
- `messages: list[ConversationMessage]` — historial en orden cronológico
- `created_at: datetime`
- `last_message_at: datetime`

### ConversationMessage
- `message_id: UUID`
- `session_id: UUID`
- `pet_id: UUID` — denormalizado para queries por mascota
- `role: Literal["user", "assistant"]`
- `content: str`
- `intent: str | None` — clasificación del mensaje (NUTRITIONAL_QUERY, REFERRAL, etc.)
- `tokens_used: int | None` — solo para mensajes del assistant
- `created_at: datetime`

### AgentQuota
Control de uso del agente conversacional por tier.
- `quota_id: UUID`
- `pet_id: UUID`
- `owner_id: UUID`
- `tier: str`
- `date: date` — por día UTC
- `questions_used: int`
- `questions_limit: int | None` — None = ilimitado (tiers pagos)
- `days_used: int` — días con al menos 1 pregunta (solo relevante para free)

### FreemiumGate
Resultado de la verificación de quota antes de responder.
- `gate_id: str`
- `allowed: bool`
- `remaining_questions: int | None`
- `remaining_days: int | None`
- `upgrade_reason: str | None` — mensaje de upgrade si no allowed

## Value Objects

### ConversationContext
Contexto construido para el system prompt del LLM. Sin PII.
```python
@dataclass(frozen=True)
class ConversationContext:
    pet_id: str          # UUID como string
    der_kcal: float      # calculado desde PetProfile
    rer_kcal: float
    n_conditions: int    # número de condiciones activas
    condition_names: list[str]  # nombres de condiciones (sin PII)
    current_plan_status: str | None
    recent_history: list[dict]  # últimas N conversaciones
```

### QuotaStatus
```python
@dataclass(frozen=True)
class QuotaStatus:
    tier: str
    allowed: bool
    questions_used_today: int
    questions_limit_today: int | None
    total_questions_used: int
    upgrade_required: bool
    upgrade_message: str | None
```
