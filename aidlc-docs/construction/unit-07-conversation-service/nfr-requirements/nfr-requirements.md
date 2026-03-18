# NFR Requirements — unit-07-conversation-service
**Unidad**: unit-07-conversation-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Conversation Service

### NFR-CONV-01: TTFT < 1 Segundo
- Time To First Token (tiempo desde request hasta primer chunk SSE) < 1 segundo.
- El bottleneck es: autenticación + gate check + context load + LLM TTFT.
- LLM TTFT de OpenRouter: típicamente 200-500ms.
- El overhead del sistema debe ser < 500ms para cumplir el target total.

### NFR-CONV-02: Quota Free Tier Aplicada Siempre
- Free: 3 preguntas/día × 3 días → 9 total → bloqueo.
- Verificado en test: enviar 10 preguntas con free tier → la 10ma es bloqueada.
- El bloqueo persiste entre reinicios (PostgreSQL guarda días usados).

### NFR-CONV-03: Emergencias Siempre Responden
- Un mensaje con EMERGENCY_KEYWORDS se responde SIEMPRE, sin verificar quota.
- Verificado en test: free tier con quota=9 (máximo) + mensaje de emergencia → respuesta de referral.

### NFR-CONV-04: 0% Respuestas Médicas del LLM
- El LLM NUNCA responde consultas médicas directamente.
- Verificado con 20 consultas médicas → 100% ReferralNode.
- Test de regresión en CI: `test_medical_queries_always_refer`.

### NFR-CONV-05: Historial por pet_id (No por Sesión)
- `GET /pets/{pet_id}/conversations` devuelve historial del pet independientemente de la sesión.
- Verificado en test: mismo pet_id desde dos sesiones distintas → mismo historial.

### NFR-CONV-06: Sin PII en System Prompt
- El system prompt no contiene: nombre de mascota, nombre de owner, peso en texto libre.
- Verificado en test: inspeccionar el prompt generado para un pet conocido → 0 PII.

### NFR-CONV-07: X-Accel-Buffering: no
- El header `X-Accel-Buffering: no` debe estar en todas las respuestas SSE.
- Sin este header, Traefik/Nginx bufferiza el stream y el usuario no recibe chunks en tiempo real.

### NFR-CONV-08: Cobertura de Tests ≥80%
- `pytest --cov=app/application/conversation tests/conversation/ --cov-fail-under=80`
- Tests obligatorios: gate free (dentro del límite), gate free (bloqueado), emergencia bypassa gate, médica bypassa gate, streaming nutritional, persistencia post-stream.

### NFR-CONV-09: Reconexión SSE
- Si el cliente se desconecta y reconecta, no se duplican mensajes en el historial.
- La persistencia ocurre una sola vez al finalizar el stream completo.

### NFR-CONV-10: Redis Fault Tolerance
- Si Redis no está disponible → degradar gracefully: no bloquear al usuario, loggear warning.
- La quota se re-sincroniza con PostgreSQL en el siguiente request exitoso.
