# ADR-019 — OpenRouter como Proveedor Unificado de LLMs

**Estado**: Aceptado — Reemplaza ADR-013
**Fecha**: 2026-03-10
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Contexto

ADR-013 definía un routing de LLMs basado en número de condiciones médicas usando tres proveedores distintos:
- 0 condiciones → Ollama Qwen2.5-7B (local)
- 1-2 condiciones → Groq Llama-70B (free tier)
- 3+ condiciones → GPT-4o

Este enfoque presentaba tres problemas críticos identificados en la revisión arquitectural:

1. **Modelos locales 7B no son adecuados para nutrición clínica**: La tasa de alucinaciones de modelos 7B es inaceptable para planes que afectan la salud de mascotas con condiciones médicas. Los guardarraíles hard-coded protegen contra los errores más graves, pero la calidad nutricional del plan depende directamente de la capacidad del LLM.

2. **Ollama en Hetzner requiere infraestructura dedicada**: Un proceso Ollama con 8GB+ de RAM requeriría un servidor separado con costo operativo continuo. OpenRouter elimina ese problema al proveer los modelos como servicio.

3. **Tres proveedores = tres integraciones, tres SDKs, tres puntos de fallo**: La mantenibilidad es baja para un equipo pequeño.

## Decisión

Adoptar **OpenRouter** como proveedor unificado de LLMs con routing por tier de suscripción + override por complejidad clínica.

### Nuevo routing

```python
def route_llm(tier: SubscriptionTier, conditions_count: int) -> str:
    """
    Routing de LLM por tier de suscripción con override clínico.

    Override de seguridad: 3+ condiciones médicas → siempre modelo máximo,
    independientemente del tier. Principio: la complejidad clínica no puede
    ser limitada por el tier de suscripción.
    """
    # Override clínico — no negociable
    if conditions_count >= 3:
        return "anthropic/claude-sonnet-4-5"

    routing = {
        SubscriptionTier.FREE:    "meta-llama/llama-3.3-70b",
        SubscriptionTier.BASICO:  "openai/gpt-4o-mini",
        SubscriptionTier.PREMIUM: "anthropic/claude-sonnet-4-5",
        SubscriptionTier.VET:     "anthropic/claude-sonnet-4-5",
    }
    return routing[tier]
```

### OCR — también vía OpenRouter

```python
OCR_MODEL = "openai/gpt-4o"  # Con capacidad de visión
```

Elimina la dependencia de Qwen2.5-VL-7B local. Misma API, mismo SDK, mejor precisión en tablas nutricionales.

### Modelo por tier y costo estimado

| Tier | Modelo | Costo estimado/plan |
|------|--------|---------------------|
| Free (mascota sana) | `meta-llama/llama-3.3-70b` | ~$0.002 |
| Básico (≤2 condiciones) | `openai/gpt-4o-mini` | ~$0.005 |
| Premium / Vet | `anthropic/claude-sonnet-4-5` | ~$0.04 |
| Cualquier tier con 3+ condiciones | `anthropic/claude-sonnet-4-5` | ~$0.04 |
| OCR (todos los tiers) | `openai/gpt-4o` (vision) | ~$0.01/imagen |

**Costo total estimado con 1.000 planes/mes**: ~$22/mes — completamente manejable.

### Privacidad de datos

Los prompts a OpenRouter (y por extensión a los proveedores finales) siguen la Regla 6 de la Constitución:
- Solo IDs anónimos (`pet_id`, `plan_id`) — nunca nombres, especie o condiciones médicas en texto plano
- OpenRouter actúa como proxy; el riesgo de exposición de datos se mitiga con IDs anónimos

## Opciones Consideradas

| Opción | Descartada porque |
|--------|------------------|
| ADR-013 (Ollama + Groq + GPT-4o) | Ollama requiere hardware dedicado; 3 integraciones; modelos 7B inadecuados para clínica |
| Solo OpenAI (GPT-4o para todo) | Costo elevado para tier Free; sin flexibilidad de modelos |
| Solo Anthropic (Claude para todo) | Mismo problema de costo en Free |
| OpenRouter con routing por condiciones (igual que ADR-013) | El routing por tier es más coherente con el modelo de negocio freemium |

## Consecuencias

**Positivas**:
- Una sola integración (OpenRouter SDK) — cero overhead de mantenimiento multi-proveedor
- Flexibilidad total: cambiar de modelo es un cambio de string en config, sin tocar código
- Fallback automático de OpenRouter si un proveedor cae
- Elimina infraestructura dedicada para Ollama
- Modelo mejora con el tier — refuerza el valor percibido de cada plan de pago
- OCR simplificado: mismo cliente, sin servidor local

**Negativas**:
- Costo variable por plan (vs. $0 con Ollama) — aceptable dado el modelo freemium
- Dependencia de OpenRouter como intermediario — mitigada con contrato de datos y uso de IDs anónimos
- Latencia adicional de ~50-100ms por el hop extra — dentro del límite de 60s

**Impacto en código**:
- Eliminar `OllamaClient`, `GroqClient`, `OpenAIClient` como clientes separados
- Crear `OpenRouterClient` único en `infrastructure/llm/`
- `LLMRouter` actualizado: routing por `(tier, conditions_count)` en lugar de solo `conditions_count`
- Eliminar dependencia de Ollama runtime de la infraestructura de deploy

**Impacto en CLAUDE.md**: Actualizar sección "LLM Texto" y "OCR/Visión".

## Variables de Entorno Requeridas

```bash
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```
