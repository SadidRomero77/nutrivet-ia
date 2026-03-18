# ADR-013 — LLM Routing por Número de Condiciones Médicas

**Estado**: ~~Aceptado~~ **SUPERSEEDED**
**Reemplazado por**: [ADR-019 — OpenRouter LLM Routing](./ADR-019-openrouter-llm-routing.md) — 2026-03-10
**Fecha original**: 2026-01
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

> **ADVERTENCIA**: Esta decisión fue reemplazada por ADR-019 que migra a OpenRouter como proveedor unificado
> con routing por tier de suscripción + override clínico para 3+ condiciones. No usar este ADR como referencia
> para implementación — ver ADR-019.

---

## Contexto

NutriVet.IA usa LLMs para generar los planes nutricionales. Los casos clínicos varían enormemente en complejidad — un perro sano sin condiciones médicas no requiere el mismo poder de razonamiento que Sally (5 condiciones médicas simultáneas). Usar GPT-4o para todos los casos es costoso. Usar Ollama para casos complejos puede resultar en planes de menor calidad.

## Decisión

Implementar routing determinista basado en el número de condiciones médicas:

```
0 condiciones → Ollama Qwen2.5-7B  (local, $0)
1-2 condiciones → Groq Llama-70B  (free tier, $0)
3+ condiciones → GPT-4o           (OpenAI, ~$0.05-0.10/plan)
OCR siempre → Qwen2.5-VL-7B       (local, $0, privacidad)
```

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| GPT-4o siempre | Máxima calidad | Costo prohibitivo en escala |
| Ollama siempre | $0 siempre | Insuficiente para casos complejos |
| Routing por condiciones (elegida) | Balance calidad/costo | Más complejo de implementar |
| Routing por BCS | Usa otro factor | BCS no refleja complejidad clínica |

## Consecuencias

**Positivas**:
- Costo controlado: mascotas sanas (mayoría del mercado) → $0.
- Calidad garantizada: casos complejos → modelo de mayor capacidad.
- Privacy-first: OCR siempre local, imágenes nunca van a cloud.

**Negativas**:
- Groq free tier tiene límites diarios — monitorear.
- Ollama requiere infraestructura local en el servidor.

**Restricciones**:
- El routing es determinista — no es decisión del agente.
- Si Ollama no está disponible y la mascota tiene 0 condiciones → error, NO fallback a cloud.
- Si Groq rate limit agotado para 1-2 condiciones → error, NO fallback a GPT-4o.
