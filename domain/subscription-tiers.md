# Modelo de Suscripción — Fuente Canónica

**Fuente de verdad**: Este archivo define los tiers, precios y límites del modelo freemium.
Todos los demás documentos deben referenciar este archivo.

---

## Tiers

| Tier | Precio | Mascotas | Planes | Agente Conversacional |
|------|--------|----------|--------|-----------------------|
| `free` | $0 | 1 | 1 plan total | 3 preguntas/día × 3 días → upgrade obligatorio |
| `basico` | $29.900 COP/mes | 1 | 1 nuevo/mes | Ilimitado |
| `premium` | $59.900 COP/mes | Hasta 3 | Ilimitados | Ilimitado |
| `vet` | $89.000 COP/mes | Ilimitadas (pacientes) | Ilimitados + dashboard clínico | Ilimitado + modo guía vet |

## Límites por Tier (para implementar en código)

```python
TIER_LIMITS = {
    "free": {
        "max_pets": 1,
        "max_plans_total": 1,           # Total histórico, no mensual
        "agent_questions_per_day": 3,
        "agent_days_limit": 3,          # Solo 3 días de acceso al agente
    },
    "basico": {
        "max_pets": 1,
        "max_plans_per_month": 1,
        "agent_questions_per_day": None,  # Ilimitado
        "agent_days_limit": None,
    },
    "premium": {
        "max_pets": 3,
        "max_plans_per_month": None,
        "agent_questions_per_day": None,
        "agent_days_limit": None,
    },
    "vet": {
        "max_pets": None,               # Ilimitado (pacientes de la clínica)
        "max_plans_per_month": None,
        "agent_questions_per_day": None,
        "agent_days_limit": None,
    },
}
```

## LLM Routing por Tier (ver ADR-019)

| Tier | Modelo (0-2 condiciones) | Override (3+ condiciones) |
|------|--------------------------|--------------------------|
| `free` | `meta-llama/llama-3.3-70b` | `anthropic/claude-sonnet-4-5` |
| `basico` | `openai/gpt-4o-mini` | `anthropic/claude-sonnet-4-5` |
| `premium` | `anthropic/claude-sonnet-4-5` | `anthropic/claude-sonnet-4-5` |
| `vet` | `anthropic/claude-sonnet-4-5` | `anthropic/claude-sonnet-4-5` |
| OCR (todos) | `openai/gpt-4o` | — |

## Gates de Conversión

| Gate | Trigger | Conversión esperada |
|------|---------|---------------------|
| Gate 1 | Segunda mascota en Free | Free → Básico/Premium |
| Gate 2 | Segundo plan en Free | Free → Básico |
| **Gate 3** | Mascota con condición médica en Free | **Free → cualquier tier (≥ 35%)** |
| Gate 4 | Agota 9 preguntas al agente (3×3 días) | Free → Básico |

> Gate 3 es el de mayor conversión esperada: urgencia clínica real (mascota enferma).
