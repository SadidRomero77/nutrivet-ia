# Outputs de Construction

Registro de artefactos de código producidos durante la fase Construction.

---

## Estructura de Código Esperada al Final de Construction

```
backend/
├── domain/
│   ├── entities/
│   │   ├── pet.py               # PetProfile aggregate root
│   │   ├── nutrition_plan.py    # NutritionPlan aggregate root
│   │   └── user.py              # UserAccount aggregate root
│   ├── value_objects/
│   │   ├── bcs.py               # BCS (1-9)
│   │   ├── species.py           # Enum: perro/gato
│   │   ├── plan_status.py       # Enum: PENDING_VET/ACTIVE/UNDER_REVIEW/ARCHIVED
│   │   └── kcal.py              # Kilocalorías con validación
│   ├── safety/
│   │   ├── toxic_foods.py       # TOXIC_DOGS, TOXIC_CATS (hard-coded)
│   │   └── medical_restrictions.py  # RESTRICTIONS_BY_CONDITION (hard-coded)
│   ├── nutrition/
│   │   └── nrc_calculator.py    # RER/DER — Python puro, sin LLM
│   └── events/
│       └── domain_events.py     # PlanGenerated, PlanApproved, etc.
├── application/
│   ├── use_cases/
│   │   ├── generate_plan.py
│   │   ├── approve_plan_vet.py
│   │   ├── scan_label.py
│   │   └── process_query.py
│   └── ports/
│       ├── plan_repository.py   # Interface (ABC)
│       ├── llm_port.py          # Interface (ABC)
│       └── ocr_port.py          # Interface (ABC)
├── infrastructure/
│   ├── db/
│   │   ├── repositories/        # Implementaciones PostgreSQL
│   │   └── migrations/          # Alembic migrations
│   ├── llm/
│   │   ├── ollama_client.py     # Qwen2.5-7B y Qwen2.5-VL-7B
│   │   ├── groq_client.py       # Llama-70B
│   │   └── openai_client.py     # GPT-4o
│   └── agent/
│       ├── graph.py             # LangGraph orquestador
│       ├── subgraphs/
│       │   ├── plan_generation.py
│       │   ├── consultation.py
│       │   ├── scanner.py
│       │   └── referral.py
│       └── state.py             # NutriVetState TypedDict
└── presentation/
    ├── routers/
    │   ├── auth.py
    │   ├── pets.py
    │   ├── plans.py
    │   ├── agent.py
    │   └── scanner.py
    └── middleware/
        ├── jwt_middleware.py
        └── rbac_middleware.py

mobile/
└── lib/
    ├── features/
    │   ├── auth/
    │   ├── pet_wizard/
    │   ├── plan_view/
    │   ├── agent_chat/
    │   └── ocr_scanner/
    └── core/
        ├── router/              # GoRouter
        ├── offline/             # Hive strategy
        └── interceptors/        # JWT refresh

tests/
├── domain/                      # TDD — cobertura ≥ 80%
├── integration/                 # Tests de integración por capa
└── bdd/                         # Gherkin → pytest-bdd
```

## Registro de Progreso

| Módulo | Estado | Cobertura | Notas |
|--------|--------|-----------|-------|
| domain/safety/ | ⬜ Pendiente | — | Prioridad 1 |
| domain/nutrition/ | ⬜ Pendiente | — | Prioridad 1 — caso Sally |
| domain/entities/ | ⬜ Pendiente | — | Prioridad 1 |
| application/use_cases/ | ⬜ Pendiente | — | Prioridad 2 |
| infrastructure/llm/ | ⬜ Pendiente | — | Prioridad 2 |
| infrastructure/agent/ | ⬜ Pendiente | — | Prioridad 2 |
| presentation/routers/ | ⬜ Pendiente | — | Prioridad 3 |
| mobile/ | ⬜ Pendiente | — | Paralelo a backend |
