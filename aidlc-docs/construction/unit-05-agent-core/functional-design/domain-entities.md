# Domain Entities — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Agent Core

### NutriVetState (TypedDict — LangGraph State)
Estado compartido accesible por todos los nodos del grafo.
```python
class NutriVetState(TypedDict):
    # Contexto del request
    session_id: str           # UUID de la sesión
    pet_id: str               # UUID (anónimo, nunca nombre)
    owner_id: str             # UUID
    tier: str                 # free/basico/premium/vet
    user_message: str         # mensaje del usuario

    # Perfil de la mascota (cargado al inicio)
    pet_profile: dict         # PetProfile serializado (sin PII)
    active_plan: dict | None  # NutritionPlan activo (serializado)
    n_conditions: int         # número de condiciones médicas

    # Clasificación
    intent: str               # PLAN_GENERATION | NUTRITIONAL_QUERY | MEDICAL_QUERY | EMERGENCY
    is_emergency: bool        # True si se detectaron keywords de emergencia

    # Resultados de nodos
    agent_response: str | None     # respuesta final al usuario
    plan_job_id: str | None        # si se generó un plan
    scan_result: dict | None       # si se procesó un scan

    # Trazas y metadatos
    agent_traces: list[dict]  # acumulado de trazas del grafo
    error: str | None         # error si algún nodo falló
```

### AgentResponse
Respuesta estructurada del agente al cliente.
- `response_type: Literal["text", "plan_queued", "referral", "emergency_referral", "scan_result"]`
- `content: str` — texto de respuesta
- `plan_job_id: str | None` — si aplica
- `referral_contact: str | None` — contacto del vet si es referral
- `emergency: bool`
- `disclaimer: str | None`

### IntentClassification
Resultado de la clasificación de intención.
- `intent: Literal["PLAN_GENERATION", "NUTRITIONAL_QUERY", "MEDICAL_QUERY", "EMERGENCY"]`
- `is_emergency: bool`
- `confidence: float` — 0.0–1.0
- `keywords_matched: list[str]`

### HITLDecision
Decisión del router HITL sobre qué hacer con un plan.
- `requires_vet: bool` — True si la mascota tiene condiciones médicas
- `plan_status: Literal["PENDING_VET", "ACTIVE"]`
- `routing_reason: str`

## Constantes del Agent Core

### EMERGENCY_KEYWORDS (Hard-Coded)
```python
EMERGENCY_KEYWORDS: frozenset[str] = frozenset([
    "convulsión", "convulsiones", "convulsiona",
    "no respira", "sin respiración",
    "envenenamiento", "intoxicado", "intoxicación",
    "emergencia", "urgencia",
    "colapso", "colapsó",
    "sangrado abundante", "hemorragia",
    "fractura", "hueso roto",
    "desmayo", "inconsciente", "inconciencia",
    "no se mueve", "no reacciona",
])
```

### MEDICAL_KEYWORDS (Hard-Coded)
```python
MEDICAL_KEYWORDS: frozenset[str] = frozenset([
    "síntomas", "síntoma", "medicina", "medicamento",
    "diagnóstico", "tratamiento", "pastilla", "dosis",
    "enfermedad", "operación", "cirugía", "antibiótico",
    "veterinario urgente", "dolor", "vómito excesivo",
])
```
