# Business Logic Model — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos del Conversation Service

### Flujo Principal: Chat SSE

```
POST /agent/chat { pet_id, message }
Headers: Accept: text/event-stream
  ↓
1. Verificar ownership: pet.owner_id == current_user.user_id
2. Cargar PetProfile + plan activo desde DB
3. Calcular NRC para contexto: NRCCalculator().calculate(pet_profile)

  ↓ FreemiumGateChecker
4. Si tier == "free":
   a. Obtener quota de Redis: HGET quota:{pet_id}:{date} questions_used
   b. Si questions_used >= 3 → verificar días_usados en PostgreSQL
   c. Si días_usados >= 3 → retornar upgrade_required (no iniciar stream)
   d. Si questions_used >= 3 pero días < 3 → esperar próximo día

  ↓ IntentClassifier (determinista)
5. Detectar emergencia (EMERGENCY_KEYWORDS) → si True: stream referral_emergency, STOP
6. Detectar consulta médica (MEDICAL_KEYWORDS) → si True: stream referral_medical, STOP

  ↓ ConsultationSubgraph (solo si NUTRITIONAL_QUERY)
7. Construir ConversationContext (sin PII)
8. Cargar últimas 10 conversaciones del pet
9. Construir system prompt con contexto nutricional
10. Construir messages list (historial + mensaje actual)
11. Iniciar stream a OpenRouter:
    response = await openrouter_client.stream_complete(model, messages)

  ↓ SSE Stream
12. Para cada chunk del LLM:
    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
13. Al completar: yield f"data: {json.dumps({'done': True, 'full_text': full_response})}\n\n"

  ↓ Post-Stream (fuera del stream)
14. Si NUTRITIONAL_QUERY respondida: INCR Redis quota + actualizar AgentQuota en DB
15. Persistir ConversationMessage (user + assistant) en PostgreSQL
16. Persistir AgentTrace (modelo, tokens, latencia)
```

### Flujo: Obtener Historial de Conversaciones

```
GET /pets/{pet_id}/conversations?limit=20&offset=0
  ↓
1. Verificar ownership
2. SELECT messages WHERE pet_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?
3. Retornar list[ConversationMessage] + HTTP 200
```

### Flujo: Quota Status

```
GET /pets/{pet_id}/agent-quota
  ↓
1. Verificar ownership
2. Si tier != "free" → retornar { unlimited: true }
3. Obtener quota Redis: questions_used hoy
4. Obtener días usados de PostgreSQL
5. Retornar QuotaStatus { questions_used, questions_remaining, days_used, days_remaining }
```

### Flujo: Stream de Referral (sin LLM)

```
yield referral_message (texto fijo de template)
yield done event
→ NO incrementar quota (referral no consume quota)
→ Persistir el mensaje de referral en historial
```
