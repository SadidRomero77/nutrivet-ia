# Business Rules — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Agent Core

### BR-AGENT-01: Detección de Emergencias — Hard-Coded
- Las keywords de emergencia están hard-coded en domain (EMERGENCY_KEYWORDS).
- Si se detecta una emergencia → respuesta inmediata con ReferralNode, sin llamar al LLM.
- La respuesta de emergencia incluye: mensaje estructurado + contacto vet + instrucción de acción urgente.
- La detección de emergencias bypassa el quota del agente conversacional.
- NO se puede deshabilitar la detección de emergencias.

### BR-AGENT-02: Límite del Agente Conversacional (Free Tier)
- Free tier: 3 preguntas/día × 3 días = 9 preguntas total → upgrade obligatorio.
- El conteo es por `pet_id` + fecha (no por session).
- Las emergencias NO consumen quota.
- Consultas médicas (que generan referral) NO consumen quota.
- Solo consultas nutricionales respondidas consumen quota.

### BR-AGENT-03: Remisión Médica — Siempre
- Cualquier consulta clasificada como MEDICAL_QUERY → ReferralNode.
- El agente NUNCA responde consultas médicas (síntomas, medicamentos, diagnósticos).
- El ReferralNode genera un mensaje estructurado con contacto del vet.
- Quality Gate G3: ≥95% clasificación correcta nutricional vs. médica.

### BR-AGENT-04: HITL Routing en LangGraph
- El HITLRouter evalúa si la mascota tiene condiciones médicas.
- Si `n_conditions > 0` → plan status = PENDING_VET.
- Si `n_conditions == 0` → plan status = ACTIVE directo.
- Esta lógica es determinista — no usa LLM para decidir.

### BR-AGENT-05: AgentTrace — Append-Only
- Cada nodo del grafo que invoca al LLM registra un AgentTrace.
- Las trazas son inmutables post-inserción.
- Las trazas incluyen: nodo, modelo, tokens, latencia, pero NUNCA PII.

### BR-AGENT-06: Estado Contextual por Mascota
- El historial de conversación se recupera por `pet_id`, no por `session_id`.
- El contexto activo incluye: últimas 10 conversaciones + plan activo + condiciones médicas.
- El sistema prompt incluye el perfil nutricional resumido de la mascota.

### BR-AGENT-07: Cuatro Subgrafos — Responsabilidades Claras
- `PlanGenerationSubgraph`: SOLO para intenciones PLAN_GENERATION.
- `ConsultationSubgraph`: SOLO para intenciones NUTRITIONAL_QUERY.
- `ScannerSubgraph`: SOLO para escaneos de etiquetas (invocado separado).
- `ReferralNode`: Para MEDICAL_QUERY y EMERGENCY — no es un subgrafo, es un nodo terminal.

### BR-AGENT-08: Orquestador No Responde Directamente
- El orquestador solo clasifica y enruta. Nunca genera respuestas al usuario directamente.
- La respuesta siempre viene de un subgrafo o del ReferralNode.

### BR-AGENT-09: Timeout por Nodo
- Cada nodo del grafo tiene un timeout configurado.
- Si un nodo excede el timeout → error controlado, no excepción no manejada.
- El timeout del orquestador completo: 60 segundos.
