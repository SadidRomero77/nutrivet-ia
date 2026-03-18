---
name: observability-setup
description: Configura e implementa observabilidad (LLMOps) para NutriVet.IA siguiendo el Playbook §9. Activar cuando se implementa una nueva feature del agente, se detecta degradación de performance, o antes de un release a producción. Genera trazas mínimas, métricas de latencia/costo/tokens, y estructura de logs JSON sin datos sensibles.
tools: Read, Write, Bash
---

# Skill: observability-setup
> Playbook ref: sección 9 — "Observabilidad y operación (LLMOps para devs)"
> Sin observabilidad, un agente en producción es una caja negra que falla en silencio.

## Cuándo activarte
- Se implementa una nueva tool o flujo del agente
- Se detecta latencia inusual o costos inesperados de LLM
- Antes de un release a producción
- Se necesita debuggear un fallo intermitente

## Métricas mínimas a instrumentar (Playbook §9.1)

Para cada request al agente:

```
□ latencia p50 / p95 (total y por tool)
□ costo estimado en USD (tokens input * precio + tokens output * precio)
□ tokens input / output por llamada LLM
□ tasa de fallos por tool (toxicity_checker, nutrition_calculator, etc.)
□ número de reintentos
□ outputs fuera de formato esperado (schema inválido)
□ incidentes de seguridad (intent de override de toxicidad, RBAC violations)
```

## Estructura de traza mínima por request (Playbook §9.2)

```python
# Cada request del agente debe generar este log estructurado
# NUNCA incluir: plan_content completo, medical_conditions texto libre,
# nombres de mascotas, datos del dueño, firma del veterinario

@dataclass
class AgentTrace:
    trace_id: str                    # UUID único por request
    job: str                         # "plan_generation" | "toxicity_check" | etc.
    pet_id: str                      # UUID — no nombre ni datos
    user_role: str                   # "owner" | "vet"
    timestamp_start: datetime
    timestamp_end: datetime
    latency_ms: int
    
    # LLM metrics
    llm_calls: list[LLMCall]         # cada llamada al modelo
    total_tokens_input: int
    total_tokens_output: int
    estimated_cost_usd: float
    
    # Tool calls
    tool_calls: list[ToolCall]       # nombre, args (sanitizados), duración, status
    
    # Result
    final_status: str                # "ACTIVE" | "PENDING_VET" | "BLOCKED" | "ERROR"
    output_schema_valid: bool
    
    # Security
    toxicity_checks: int             # cuántas validaciones de toxicidad se hicieron
    rbac_violations: int             # intentos de acceso no autorizado (debe ser 0)
```

## Implementación paso a paso

### 1. Verificar dependencias
```bash
pip show structlog opentelemetry-sdk opentelemetry-exporter-otlp 2>/dev/null
# Si no están: pip install structlog opentelemetry-sdk --break-system-packages
```

### 2. Configurar logging estructurado JSON

```python
# app/infrastructure/observability/logging.py
import structlog

def configure_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if settings.ENVIRONMENT == "development"
            else structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

# USO — campos explícitos, sin dumps de objetos enteros
logger.info("plan_generated",
    trace_id=trace_id,
    pet_id=str(pet_id),          # UUID solamente
    status=plan.status,
    latency_ms=elapsed,
    tokens_used=llm_response.usage.total_tokens,
    cost_usd=calculate_cost(llm_response.usage),
    tool_calls_count=len(tool_calls)
    # ❌ NUNCA: plan_content=plan.dict(), pet_name=pet.name
)
```

### 3. Middleware de métricas por request

```python
# app/presentation/middleware/metrics.py
import time
from contextvars import ContextVar

current_trace: ContextVar[AgentTrace] = ContextVar('current_trace')

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    trace = AgentTrace(
        trace_id=str(uuid4()),
        timestamp_start=datetime.utcnow()
    )
    current_trace.set(trace)
    
    response = await call_next(request)
    
    trace.timestamp_end = datetime.utcnow()
    trace.latency_ms = int((trace.timestamp_end - trace.timestamp_start).total_seconds() * 1000)
    
    # Log estructurado de la traza completa
    logger.info("request_completed", **trace.to_log_dict())
    
    # Métricas (si hay Prometheus/Azure Monitor)
    metrics.histogram("request_latency_ms", trace.latency_ms, tags={"job": trace.job})
    metrics.counter("llm_tokens_total", trace.total_tokens_input + trace.total_tokens_output)
    
    return response
```

### 4. Instrumentar tool calls del agente

```python
# Wrapper para tools del agente
def traced_tool(tool_func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        tool_name = tool_func.__name__
        trace = current_trace.get()
        
        try:
            result = await tool_func(*args, **kwargs)
            elapsed = int((time.time() - start) * 1000)
            
            trace.tool_calls.append(ToolCall(
                name=tool_name,
                duration_ms=elapsed,
                status="success",
                # Args sanitizados — solo IDs y tipos, no contenido
                args_summary={"pet_id": kwargs.get('pet_id'), "food_id": kwargs.get('food_id')}
            ))
            return result
            
        except Exception as e:
            trace.tool_calls.append(ToolCall(name=tool_name, status="error", error_type=type(e).__name__))
            metrics.counter("tool_errors_total", 1, tags={"tool": tool_name, "error": type(e).__name__})
            raise
    return wrapper
```

### 5. Calcular costo estimado

```python
# app/infrastructure/observability/cost.py
# Precios GPT-4o (actualizar cuando cambien)
COST_PER_1K_TOKENS = {
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}

def calculate_cost(usage: Usage, model: str) -> float:
    prices = COST_PER_1K_TOKENS.get(model, COST_PER_1K_TOKENS["gpt-4o"])
    return (
        (usage.prompt_tokens / 1000) * prices["input"] +
        (usage.completion_tokens / 1000) * prices["output"]
    )
```

### 6. Dashboard de métricas mínimo

Crear `docs/metrics-baseline.md` con targets iniciales:

```markdown
## Métricas Baseline NutriVet.IA

| Métrica | Target | Alerta si |
|---------|--------|-----------|
| Latencia p95 plan_generation | < 5s | > 8s |
| Latencia p95 toxicity_check | < 200ms | > 500ms |
| Costo por plan generado | < $0.05 USD | > $0.10 |
| Tokens promedio por plan | < 2000 total | > 4000 |
| Tasa de error tool calls | < 1% | > 5% |
| RBAC violations | 0 | > 0 (alerta inmediata) |
| Outputs schema inválido | < 0.5% | > 2% |
```

### 7. Verificar que logs NO contienen datos sensibles

```bash
# Buscar posibles leaks en logs de test
pytest tests/ -v 2>&1 | grep -iE "(nombre|password|token|plan_content|diagnosis|medical_condition)" | head -20

# Si encuentra hits → revisar y limpiar antes de continuar
```

## Reglas críticas

- NUNCA loggear: plan_content completo, medical_conditions libre, nombres de usuarios/mascotas, firmas veterinarias, tokens JWT
- SIEMPRE loggear: trace_id, pet_id (UUID), job, status, latencia, costo, tool calls summary
- `rbac_violations > 0` es una alerta de seguridad — debe disparar notificación inmediata
- Mantener `docs/metrics-baseline.md` actualizado con cada release
- En `RUNBOOK.md` están los pasos de respuesta cuando una métrica cruza el umbral de alerta
