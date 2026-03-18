# ADR-021 — Agente Conversacional Fluido (No Chatbot)

**Estado**: Aceptado
**Fecha**: 2026-03-11
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Contexto

El agente conversacional de NutriVet.IA es un diferenciador clave del producto. Sin embargo,
si el agente responde con listas numeradas genéricas, respuestas cortas sin contexto o mensajes
con tono de asistente corporativo, el owner lo percibirá como "otro chatbot más" y perderá confianza.

El agente debe sentirse como hablar con un **nutricionista veterinario de confianza**: respuestas
cálidas, contextualizadas a la mascota específica del usuario, con personalidad consistente y
capacidad de mantener el hilo de la conversación de forma natural.

## Decisión

### Principios de Conversación (no negociables)

1. **Siempre en contexto de la mascota**: el agente conoce el nombre, especie, condiciones y plan
   activo de la mascota — las respuestas deben referenciarlo explícitamente.
   - ❌ "Los perros con diabetes deben evitar el azúcar."
   - ✅ "Para Luna, con su diabetes, el azúcar es una restricción estricta. En su plan actual
     usamos boniato en pequeñas cantidades como fuente de carbohidrato complejo de bajo índice glucémico."

2. **Respuestas de longitud adecuada al contexto**: no siempre largas, no siempre cortas.
   - Preguntas simples ("¿puedo darle pollo?") → 2-3 oraciones directas
   - Preguntas complejas ("¿cómo ajusto el plan si bajó de peso?") → respuesta estructurada con contexto

3. **Sin listas numeradas como primer formato**: el agente responde en prosa natural. Si necesita
   enumerar, usa bullets solo cuando hay 3+ items sin jerarquía entre ellos.

4. **Continuidad conversacional**: recuerda lo que se discutió en la misma sesión y hace referencias
   cruzadas cuando es relevante.
   - "Como comentamos antes sobre la transición de Luna..."

5. **Tono cálido pero profesional**: no condescendiente, no corporativo. Como un colega veterinario
   de confianza que habla con el dueño de la mascota.

6. **Proactividad contextual**: cuando hay algo importante relacionado con la pregunta que el usuario
   no preguntó pero debería saber, el agente lo menciona brevemente.
   - Si preguntan por un ingrediente con contraindicación → "Ese ingrediente es seguro para la mayoría
     de perros, pero dado que Luna tiene gastritis, te recomiendo reducir la cantidad a..."

### Límites del Agente (hard-coded, no cambian con el tono)

- Consultas médicas (síntomas, diagnósticos, medicamentos) → derivar al vet con mensaje estructurado
- Diagnósticos o interpretación de exámenes → derivar siempre
- El tono amigable no modifica estos límites

### Estructura del Prompt del Sistema

El system prompt del agente conversacional debe incluir:

```
Eres el asistente nutricional de [nombre_mascota], [especie], [edad], con [condiciones_activas].
Su plan nutricional actual es [tipo_plan]: [resumen_del_plan].

Tu rol: responder preguntas sobre nutrición de [nombre_mascota] de forma precisa, cálida y contextualizada.
Hablas como un nutricionista veterinario de confianza — no como un chatbot corporativo.

Límites:
- Consultas médicas (síntomas, diagnósticos, medicamentos) → "Para eso necesitas hablar con un
  veterinario. Te conecto con uno ahora si quieres."
- Nunca especulas sobre diagnósticos ni interpreta exámenes.
```

### UX del Chat en Flutter

- **Burbujas de mensaje con avatar**: el agente tiene un avatar (icono NutriVet.IA), no un ícono genérico
- **Streaming de respuesta**: las respuestas se muestran letra por letra (streaming) — sensación de
  que el agente está "pensando" y escribiendo en tiempo real
- **Indicador de contexto activo**: burbuja pequeña en la parte superior que muestra la mascota activa
  ("Hablando sobre Luna 🐶")
- **Acciones rápidas contextuales**: chips de respuesta rápida sugeridos cuando aplica
  (ej: "Ver plan completo", "Ajustar porción", "Hablar con vet")
- **Historial persistente**: el historial del chat se guarda por mascota, no por sesión
- **Animaciones sutiles**: typing indicator mientras el agente procesa, fade-in de respuestas

### Streaming en Backend

El endpoint de chat debe soportar **Server-Sent Events (SSE)** para streaming de tokens:

```
POST /v1/agent/chat
Content-Type: text/event-stream

data: {"token": "Para "}
data: {"token": "Luna, "}
data: {"token": "con su diabetes..."}
data: {"done": true, "full_response": "..."}
```

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| **Agente fluido contextualizado (elegida)** | Diferenciador, retención, confianza | Más complejo de implementar (streaming, estado) |
| Chatbot Q&A estándar | Simple de implementar | No diferencia del producto, baja retención |
| Solo FAQs predefinidas | Sin riesgo de respuesta incorrecta | No es un agente, no es el diferenciador prometido |

## Consecuencias

**Positivas**:
- Retención mayor: usuarios que sienten conexión con el agente regresan más frecuentemente.
- Diferenciador real vs. apps genéricas de chat con mascotas.
- El streaming mejora la percepción de velocidad aunque el LLM tarde lo mismo.

**Negativas**:
- SSE es nativo en FastAPI + Uvicorn (proceso persistente) — sin restricciones de timeout ni configuración adicional de infraestructura.
- El system prompt contextualizado consume más tokens (incluye perfil de mascota + plan activo).
- Mayor cuidado en el diseño del prompt para mantener el tono consistente.

## Impacto en Unidades

- **U-05 agent-core**: `ConsultationSubgraph` debe incluir el contexto de la mascota en el system prompt
- **U-07 conversation-service**: endpoint SSE + historial persistente por mascota
- **U-09 mobile-app**: `ChatScreen` con streaming, avatar, chips contextuales, indicador de mascota activa
