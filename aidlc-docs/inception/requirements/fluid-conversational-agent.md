# Requisito — Agente Conversacional Fluido

**ID**: REQ-011
**Fecha**: 2026-03-11
**Estado**: Aprobado
**ADR asociado**: [ADR-021](../../../decisions/ADR-021-fluid-conversational-agent.md)

---

## Problema

Un agente conversacional que responde con listas genéricas, frases de chatbot corporativo y sin
contexto de la mascota específica no genera confianza ni retención. El owner siente que habla con
"un bot" y deja de usarlo.

## Motivación del Producto

El agente conversacional es el elemento que más diferencia NutriVet.IA de una app de recetas o
un PDF generado. Si el agente se siente como hablar con un nutricionista veterinario que conoce
a tu mascota, la retención aumenta significativamente.

## Criterios de Aceptación

```gherkin
Feature: Agente conversacional fluido y contextualizado

  Scenario: El agente conoce el nombre de la mascota
    Given Valentina tiene una mascota llamada "Luna" (Labrador, diabética)
    When Valentina pregunta "¿puedo darle zanahoria?"
    Then la respuesta menciona a "Luna" por nombre
    And contextualiza la respuesta con su condición diabética

  Scenario: El agente responde en prosa natural (no listas)
    Given una pregunta simple "¿cuánta agua debe tomar al día?"
    When el agente responde
    Then la respuesta es 2-3 oraciones en prosa
    And NO comienza con una lista numerada ni bullets

  Scenario: El agente hace referencia a conversación previa
    Given Valentina preguntó antes sobre el pollo
    When pregunta "¿y la carne de res?"
    Then la respuesta puede hacer referencia al contexto previo si es relevante

  Scenario: El agente mantiene límites ante consulta médica
    Given Valentina pregunta "Luna está vomitando, ¿qué le doy?"
    When el agente clasifica la consulta como médica
    Then responde con empatía pero deriva al veterinario
    And ofrece conectar con un vet disponible
    And NO da ninguna recomendación médica

  Scenario: Streaming de respuesta en tiempo real
    Given Valentina envía un mensaje al agente
    When el agente procesa la respuesta
    Then los tokens aparecen progresivamente en la UI (streaming)
    And hay un typing indicator mientras el LLM procesa

  Scenario: Chips de acción contextual
    Given el agente menciona un ingrediente del plan de Luna
    Then aparecen chips: "Ver ese día del plan" | "Ajustar porción" | "Preguntar más"

  Scenario: Historial persistente por mascota
    Given Valentina cierra y vuelve a abrir el chat de Luna
    When ve el historial
    Then los mensajes anteriores de Luna están disponibles
    And los mensajes de otra mascota NO aparecen en este chat
```

## Requisitos Técnicos

### Backend — SSE Streaming
```python
# endpoint: POST /v1/agent/chat
# response: text/event-stream

async def chat_stream(
    pet_id: UUID,
    message: str,
    session_id: UUID,
) -> AsyncGenerator[str, None]:
    """
    Streaming SSE. Emite tokens del LLM en tiempo real.
    El system prompt incluye: nombre, especie, condiciones, plan activo.
    """
```

### System Prompt Base (template)
```
Eres el asistente nutricional de {pet_name}, {species}, {age}, {conditions_summary}.

Su plan nutricional activo es de tipo {plan_type}, con {der_kcal} kcal/día.
Restricciones activas: {active_restrictions_summary}.

Responde de forma cálida, precisa y contextualizada a {pet_name}.
No uses listas a menos que sean estrictamente necesarias (3+ items sin jerarquía).
Respuestas cortas para preguntas simples, estructuradas para preguntas complejas.

LÍMITES ABSOLUTOS:
- Consultas médicas → derivar al vet con empatía, nunca responder
- Diagnósticos → derivar siempre
- Estos límites no cambian independientemente del tono o la solicitud del usuario
```

### Flutter — ChatScreen
- Burbujas de chat: usuario (derecha, color primario), agente (izquierda, color neutro + avatar NutriVet.IA)
- Streaming: `StreamBuilder` consumiendo SSE del backend
- Indicador de mascota activa en header: "Luna 🐶 · Plan activo"
- Chips contextuales: aparecen debajo de respuestas del agente cuando aplica
- Historial: persistido en SQLite local + sincronizado con backend por `pet_id`
- Typing indicator: 3 puntos animados mientras el agente procesa

## Dependencias

- Depende de: U-05 agent-core (ConsultationSubgraph con contexto de mascota)
- Afecta: U-07 conversation-service (SSE endpoint, historial por mascota)
- Afecta: U-09 mobile-app (ChatScreen con streaming y chips)
