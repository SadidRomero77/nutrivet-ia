# NFR Design Patterns — unit-05-agent-core
**Unidad**: unit-05-agent-core
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Agent Core

### Patrón 1: Determinismo Antes de LLM
Toda la lógica crítica (emergencias, HITL, routing) se resuelve con código determinista ANTES de invocar cualquier LLM.
- Emergencias: detectadas por EMERGENCY_KEYWORDS frozenset → nunca LLM.
- HITL: decisión por `n_conditions > 0` → nunca LLM.
- LLM Routing: decisión por tier + n_conditions → nunca LLM.
El LLM solo se invoca para generar contenido conversacional o del plan.

### Patrón 2: Fail-Fast para Emergencias
Las emergencias se detectan en el primer nodo y cortocircuitan el grafo.
```python
def route_by_intent(state: NutriVetState) -> str:
    if state["is_emergency"]:
        return "referral"  # inmediato, sin más nodos
    ...
```
Garantiza que una emergencia nunca espera detrás de una cola de LLM.

### Patrón 3: Stateless por Invocación
Cada invocación del grafo recibe un `NutriVetState` limpio con el contexto cargado.
- No hay estado global mutable en el orquestador.
- Múltiples workers de Uvicorn pueden ejecutar el grafo concurrentemente sin conflicto.
- El contexto histórico se carga desde PostgreSQL en el nodo `load_context`.

### Patrón 4: Template-Based Referral (Sin LLM)
El ReferralNode usa templates pre-definidos, no LLM.
- Las respuestas de remisión son predecibles, revisables y validadas.
- El LLM nunca intenta "ayudar" en una consulta médica.
- Los templates están versionados en código — un cambio requiere PR y revisión.

### Patrón 5: Contextual System Prompt (Privacidad)
El system prompt del agente conversacional incluye el perfil nutricional pero sin PII:
```
System: Eres un asistente de nutrición veterinaria.
Pet ID: {pet_id}. DER: {der_kcal} kcal. Condiciones: {condition_names}.
Responde solo consultas nutricionales. Ante consultas médicas, remite al vet.
```
Nunca incluye: nombre de la mascota, nombre del dueño, peso exacto en texto libre.

### Patrón 6: Tracing Centralizado en persist_traces
Todos los nodos acumulan trazas en `state["agent_traces"]` durante el recorrido.
El nodo `persist_traces` (al final del grafo) inserta todas en PostgreSQL en una sola transacción.
- Garantiza que si un nodo falla, las trazas anteriores igual se persisten.
- Evita múltiples roundtrips a PostgreSQL durante la ejecución del grafo.

### Patrón 7: Subgrafo como Unidad Aislada
Cada subgrafo es un `StateGraph` independiente compilado por separado.
- Se puede testear un subgrafo de forma aislada sin ejecutar el orquestador completo.
- Permite reemplazar un subgrafo (ej: mejorar ConsultationSubgraph) sin tocar el orquestador.
- La interfaz entre orquestador y subgrafo es siempre `NutriVetState`.
