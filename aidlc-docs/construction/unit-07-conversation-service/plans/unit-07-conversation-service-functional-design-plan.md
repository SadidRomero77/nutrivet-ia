# Plan: Functional Design — Unit 07: conversation-service

**Unidad**: unit-07-conversation-service
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del agente conversacional: QueryClassifier (NUTRITIONAL/
MEDICAL/EMERGENCY), NutritionalResponder con SSE streaming, FreemiumGateChecker,
historial persistente por pet_id y aliases regionales.

## QueryClassifier — 3 Tipos de Consulta

| Tipo | Descripción | Acción |
|------|-------------|--------|
| `NUTRITIONAL` | Pregunta sobre nutrición, alimentos, porciones, ingredientes | Responde el agente |
| `MEDICAL` | Síntomas, medicamentos, diagnósticos, enfermedades | Remite al vet |
| `EMERGENCY` | Palabras clave de emergencia (frozenset) | Remite al vet + acción urgente |

**Regla crítica**: El agente NUNCA responde consultas MEDICAL (Quality Gate G3 ≥ 95%).
EMERGENCY detection es determinística (keyword frozenset — ya implementado en unit-05).

**Límite nutricional/médico** (ejemplos):
```
NUTRITIONAL: "¿Cuántas proteínas necesita mi perro con diabetes?"
NUTRITIONAL: "¿El pollo está bien para gatos con gastritis?"
MEDICAL:     "Mi perro vomitó 3 veces, ¿qué hago?"
MEDICAL:     "¿Qué dosis de metformina le doy?"
MEDICAL:     "Creo que tiene fiebre, ¿es grave?"
```

## NutritionalResponder — Respuesta con Contexto del Pet

**System prompt contextualizado**:
```
"Eres el asistente nutricional de {pet_name}, un {species} de {breed}.
Su plan nutricional activo incluye: [resumen del plan].
Sus condiciones médicas: [lista de condiciones — SOLO nutricionalmente relevantes].
Sus alergias conocidas: [lista].
Responde SOLO consultas nutricionales. Para cualquier consulta médica (síntomas,
medicamentos, diagnósticos), remite siempre al veterinario.
Usa términos en español LATAM. Incluye siempre el disclaimer al final."
```

**Aliases regionales**: la respuesta debe usar términos locales según el contexto:
- ahuyama (CO) / zapallo (AR/PE) / calabaza (MX) — todos son válidos
- El sistema no fuerza el dialecto — el LLM adapta según el contexto del usuario

## FreemiumGateChecker — Cuotas del Tier Free

```
Free tier: 3 preguntas/día × 3 días = 9 preguntas total (lifetime para Free)

Reglas:
  - Máx 3 preguntas por día calendario
  - Máx 9 preguntas total (acumuladas, no por período)
  - Al alcanzar el límite diario → response con upgrade gate
  - Al alcanzar el límite total → upgrade obligatorio, no más respuestas
  - EMERGENCIAS: siempre pasan — no consumen cuota ni se bloquean

Tier Básico/Premium/Vet: ilimitado (sin gate)
```

**Verificación de cuota**: atómica en DB (`agent_quotas` tabla) — no basada en sesión.
La cuota persiste entre sesiones y dispositivos.

## SSE Streaming (ADR-021)

```
POST /v1/agent/chat
  → QueryClassifier (determina tipo)
  → FreemiumGateChecker (verifica cuota)
  → NutritionalResponder (genera respuesta con SSE)

Response: Content-Type: text/event-stream
  data: {"token": "El", "done": false}
  data: {"token": " pollo", "done": false}
  ...
  data: {"token": ".", "done": true, "disclaimer": "NutriVet.IA es asesoría..."}
```

**El disclaimer se envía en el último evento SSE** (`done: true`).

## Historial de Conversación — Contexto LLM

- Persistido por `pet_id` (no por sesión ni dispositivo).
- Los últimos 10 mensajes se incluyen como contexto en el LLM call.
- El historial nunca contiene datos médicos en texto plano — solo IDs.
- Mobile recupera últimos 50 mensajes al abrir el chat.

## Consulta Médica — Mensaje de Remisión

```python
MEDICAL_REFERRAL_MESSAGE = """
Esta consulta está relacionada con la salud de {pet_name} y está fuera de mi área.
Te recomiendo consultar con tu veterinario de confianza para este tema.

{vet_contact_if_available}

Recuerda: NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico
médico veterinario.
"""
```

## Casos de Prueba Críticos

- [ ] Consulta nutricional → respondida por el agente con contexto del pet
- [ ] Consulta médica ("vomitó") → remite al vet con mensaje estructurado
- [ ] Emergencia → bypass de cuota + mensaje urgente
- [ ] Free tier: 3 preguntas en un día → cuarta bloqueada con upgrade gate
- [ ] Free tier: 9 preguntas total → décima bloqueada, upgrade obligatorio
- [ ] Aliases regionales en respuesta (no solo términos colombianos)
- [ ] Disclaimer presente en TODA respuesta (incluyendo remisiones)
- [ ] Historial de las últimas 10 conversaciones incluido en contexto LLM
- [ ] SSE streaming funcional (primer token < 1s)
- [ ] System prompt incluye pet_name, species, conditions, active_plan

## Referencias

- Spec: `aidlc-docs/inception/units/unit-07-conversation-service.md`
- ADR-021: SSE streaming
- Constitution: REGLA 8 (disclaimer), REGLA 9 (límite nutricional/médico)
- Quality Gates: G3 (≥ 95% clasificación nutricional vs médica)
