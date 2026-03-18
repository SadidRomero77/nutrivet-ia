# NFR Design Patterns — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Plan Service

### Patrón 1: Command Queue (ARQ + Redis)
La generación de plan es un comando que se encola en Redis via ARQ.
- El cliente no espera el resultado (async): recibe `job_id` → hace polling.
- El worker procesa de forma aislada — un fallo del worker no afecta la API.
- Permite reintentos automáticos del job sin impacto al usuario.
- Si el servidor se reinicia, los jobs pendientes en Redis persisten (Redis AOF).

### Patrón 2: Guardarraíles Deterministas + LLM Creativo
El LLM decide ingredientes y balance (creativo), pero el sistema valida post-generación.
```
LLM genera plan
    ↓
FoodSafetyChecker verifica CADA ingrediente (determinista)
    ↓ Si tóxico: STOP
MedicalRestrictionEngine verifica restricciones (determinista)
    ↓ Si violación: re-prompt
NRCCalculator provee RER/DER (determinista, calculado antes del LLM)
```
El LLM nunca ve el resultado de los guardarraíles — solo ve inputs limpios.

### Patrón 3: Retry con Exponential Backoff para LLM
OpenRouter puede tener rate limits o errores transitorios.
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def complete(...):
```
- 3 intentos con espera: 2s → 4s → 8s.
- Si agota reintentos → `PlanJob.status = "failed"` con mensaje descriptivo.

### Patrón 4: Immutable Event Log (AgentTrace)
Cada invocación al LLM se registra como un evento inmutable.
- Permite auditoría completa del proceso de generación.
- Permite debugging de planes incorrectos sin modificar el historial.
- El trigger en PostgreSQL previene UPDATE accidental.
- Un plan complejo puede tener 3-5 trazas (re-prompts por restricciones).

### Patrón 5: Status Poll en lugar de WebSocket
El cliente hace polling simple vs. una conexión WebSocket persistente.
- Simplicidad: `GET /plans/jobs/{job_id}` cada 3 segundos.
- El job típicamente completa en 10-30 segundos.
- Flutter tiene timer para polling automático.
- Sin estado adicional en el servidor para conexiones abiertas.

### Patrón 6: Prompt Engineering con UUIDs
El prompt al LLM usa solo UUIDs y datos nutricionales, NUNCA PII:
```python
prompt = f"""
Genera un plan nutricional para pet_id={pet_id}.
RER: {rer_kcal} kcal, DER: {der_kcal} kcal.
Condiciones: {[c.condition for c in conditions]}  # solo el nombre de la condición
Modalidad: {modalidad}
Restricciones a aplicar: {restrictions_summary}
"""
```
El nombre del dueño, el nombre de la mascota y la especie NO aparecen en el prompt.

### Patrón 7: Fallback de Modelo LLM
Si el modelo asignado falla (timeout, error), se intenta con el modelo de tier inferior:
```
claude-sonnet-4-5 → falla → gpt-4o-mini (solo si no es override clínico)
gpt-4o-mini       → falla → llama-3.3-70b
llama-3.3-70b     → falla → job.status = "failed"
```
EXCEPCIÓN: Override clínico (3+ condiciones) — NO se degrada a modelo inferior.
