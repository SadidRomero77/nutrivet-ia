# Business Rules — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Conversation Service

### BR-CONV-01: SSE Streaming
- Las respuestas del agente conversacional se envían via Server-Sent Events (SSE).
- El cliente recibe tokens en tiempo real a medida que el LLM genera.
- Content-Type: `text/event-stream`.
- TTFT (Time To First Token) objetivo: < 1 segundo.

### BR-CONV-02: Quota Free Tier
- Free: 3 preguntas/día × máximo 3 días → 9 preguntas total → upgrade obligatorio.
- El conteo de "días" es: días en los que se usó al menos 1 pregunta.
- Al completar 3 días con uso → el agente se bloquea permanentemente para el tier free.
- Las preguntas restantes de un día NO se acumulan al día siguiente.

### BR-CONV-03: Emergencias Bypasan Quota
- Mensajes que contienen EMERGENCY_KEYWORDS → siempre se responden, sin consumir quota.
- La respuesta es el mensaje de referral de emergencia (template, sin LLM).

### BR-CONV-04: Consultas Médicas → Referral (sin quota)
- Mensajes clasificados como MEDICAL_QUERY → ReferralNode.
- Las consultas médicas NO consumen quota del free tier.
- Solo consultas nutricionales respondidas por el LLM consumen quota.

### BR-CONV-05: Historial por pet_id
- El historial de conversación está asociado al `pet_id`, no al `session_id`.
- Si el owner hace login en otro dispositivo → mismo historial para la misma mascota.
- El contexto del LLM incluye las últimas 10 conversaciones del pet.

### BR-CONV-06: System Prompt Contextual
- El system prompt incluye el perfil nutricional del pet (sin PII):
  - DER/RER calculados
  - Nombres de condiciones médicas (no los datos encriptados)
  - Status del plan activo
  - Historial reciente
- El system prompt NO incluye: nombre de la mascota, nombre del dueño, peso exacto.

### BR-CONV-07: Límite del Agente para Basico
- Básico: agente ilimitado (preguntas y días).
- Premium: agente ilimitado.
- Vet: agente ilimitado + modo guía veterinario (respuestas más técnicas).

### BR-CONV-08: Modo Guía Vet (Solo Tier Vet)
- Para tier "vet" el system prompt incluye instrucciones de modo técnico.
- El agente puede responder consultas más detalladas sobre nutrición clínica.
- SIGUE sin responder consultas médicas (síntomas, medicamentos, diagnósticos).
- Solo diferencia: nivel de tecnicidad de las respuestas nutricionales.

### BR-CONV-09: Persistencia de Mensajes
- Cada mensaje (user + assistant) se persiste en PostgreSQL.
- La persistencia ocurre DESPUÉS de completar el stream (no durante).
- Si el stream se interrumpe → el mensaje parcial NO se persiste.

### BR-CONV-10: Disclaimer en Respuestas de Plan
- Si la respuesta del agente hace referencia a un plan nutricional → agregar disclaimer al final.
- Disclaimer: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
