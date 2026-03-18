# Deployment Architecture — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Deployment del Conversation Service

```
Hetzner CPX31 (Ashburn VA)
└── Coolify
    ├── nutrivet-backend (FastAPI + Uvicorn, puerto 8000)
    │   ├── presentation/agent/
    │   │   └── agent_router.py         ← POST /agent/chat (SSE)
    │   │                                  GET /pets/{id}/conversations
    │   │                                  GET /pets/{id}/agent-quota
    │   ├── application/conversation/
    │   │   ├── conversation_use_case.py
    │   │   └── freemium_gate_checker.py
    │   └── infrastructure/conversation/
    │       ├── openrouter_streaming_client.py  ← httpx streaming
    │       ├── redis_quota_client.py           ← INCR + TTL
    │       └── pg_conversation_repository.py
    │
    ├── Redis (contenedor)
    │   └── quota:{pet_id}:{YYYY-MM-DD}  → Hash { questions_used: N }
    │       TTL: 86400 segundos (1 día UTC)
    │
    └── PostgreSQL
        └── conversations, conversation_messages, agent_quotas tables
```

## PostgreSQL Schema

```sql
CREATE TABLE conversation_sessions (
    session_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    owner_id UUID NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversation_messages (
    message_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES conversation_sessions(session_id),
    pet_id UUID NOT NULL REFERENCES pets(pet_id),  -- denormalizado para query
    role VARCHAR(20) NOT NULL CHECK (role IN ('user','assistant')),
    content TEXT NOT NULL,
    intent VARCHAR(50) NULL,
    tokens_used INT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_quotas (
    quota_id UUID PRIMARY KEY,
    pet_id UUID NOT NULL REFERENCES pets(pet_id),
    owner_id UUID NOT NULL REFERENCES users(user_id),
    date DATE NOT NULL,
    questions_used INT NOT NULL DEFAULT 0,
    questions_limit INT NULL,   -- NULL = ilimitado
    UNIQUE (pet_id, date)
);

CREATE INDEX idx_messages_pet ON conversation_messages(pet_id, created_at DESC);
CREATE INDEX idx_sessions_pet ON conversation_sessions(pet_id);
```

## Redis Schema para Quota

```
HSET quota:{pet_id}:{YYYY-MM-DD} questions_used N
EXPIRE quota:{pet_id}:{YYYY-MM-DD} 86400  -- TTL 24h
```

Además, un hash diario para tracking de días totales:
```
SADD quota:days_used:{pet_id} {YYYY-MM-DD}
```

## Variables de Entorno

```env
REDIS_URL=redis://localhost:6379
OPENROUTER_API_KEY=               # compartida
OPENROUTER_STREAMING_TIMEOUT=60   # segundos timeout stream
FREE_TIER_QUESTIONS_PER_DAY=3
FREE_TIER_MAX_DAYS=3
```
