# Workflow — LLM Routing

**Propósito**: Seleccionar el modelo LLM correcto según complejidad clínica de la mascota.

---

## Lógica de Routing (Determinista)

```python
def route_llm(medical_conditions: list[str]) -> LLMModel:
    n = len(medical_conditions)
    if n == 0:
        return LLMModel.OLLAMA_QWEN_7B      # Local, $0
    elif n <= 2:
        return LLMModel.GROQ_LLAMA_70B      # Free tier, $0
    else:
        return LLMModel.GPT_4O              # Máxima capacidad

def route_ocr() -> LLMModel:
    return LLMModel.OLLAMA_QWEN_VL_7B      # Siempre local, $0
```

---

## Tabla de Routing

| Condiciones | Modelo | Proveedor | Costo | Razón |
|-------------|--------|-----------|-------|-------|
| 0 | Qwen2.5-7B | Ollama (local) | $0 | Caso simple → no requiere capacidad premium |
| 1-2 | Llama-70B | Groq (free tier) | $0 | Complejidad media → capacidad superior sin costo |
| 3+ | GPT-4o | OpenAI | ~$0.05-0.10/plan | Caso Sally (5 condiciones) → máxima capacidad |
| OCR | Qwen2.5-VL-7B | Ollama (local) | $0 | Siempre local — visión multimodal, sin datos a cloud |

---

## Reglas del Routing

1. **El routing es determinista** — el agente no decide el modelo, es función del número de condiciones.
2. **Ollama no disponible** → si 0 condiciones: error al owner, NO fallback a cloud. Privacidad first.
3. **Groq rate limit agotado** → error al owner, NO fallback a GPT-4o para 1-2 condiciones. Evitar costos imprevistos.
4. **GPT-4o**: solo para 3+ condiciones. Si falla → retry × 2 → error controlado.
5. **OCR siempre local**: Qwen2.5-VL nunca falla a un modelo cloud. Privacidad de imagen de producto.

---

## Caso Sally — Verificación de Routing

```
Sally: Diabetes + Hepatopatía + Hiperlipidemia + Gastritis + Cistitis = 5 condiciones
→ 5 > 2 → GPT-4o ✓
→ DER calculado por NRC Calculator (Python puro) ✓
→ LLM recibe: pet_id anonimizado, DER target, ingredientes permitidos
→ LLM NO recibe: nombre "Sally", peso exacto, nombre del owner
```

---

## Monitoreo del Routing

Métricas a registrar en `agent_traces`:

```json
{
  "routing_decision": "gpt-4o",
  "conditions_count": 5,
  "model_latency_ms": 4200,
  "tokens_input": 650,
  "tokens_output": 900,
  "estimated_cost_usd": 0.047,
  "fallback_triggered": false
}
```

Alertas:
- `llm_fallback_rate > 10%` → P2 — investigar disponibilidad de Ollama/Groq.
- `estimated_cost_usd > 0.10` por plan → P3 — revisar prompt efficiency.
