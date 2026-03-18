# Plan: NFR Design — Unit 04: plan-service

**Unidad**: unit-04-plan-service
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a plan-service

### Patrón: Async Job (POST → job_id → polling)

**Contexto**: La generación de planes puede tomar hasta 30s (LLM). No se puede
bloquear la conexión HTTP del cliente durante ese tiempo.

**Diseño**:
```python
# presentation/routers/plan_router.py
@router.post("/v1/plans/generate")
async def generate_plan(request: PlanGenerationRequest, current_user: User = Depends(get_current_user)):
    """Encola job de generación. Retorna job_id inmediatamente."""
    job = await plan_generation_use_case.enqueue(request, current_user)
    return {"job_id": str(job.job_id), "status": "QUEUED"}

@router.get("/v1/plans/jobs/{job_id}")
async def get_job_status(job_id: UUID, current_user: User = Depends(get_current_user)):
    """Polling endpoint — cliente llama cada 3s hasta READY o FAILED."""
    job = await plan_generation_use_case.get_job(job_id, current_user.user_id)
    return {"status": job.status, "plan_id": str(job.plan_id) if job.plan_id else None}
```

### Patrón: LLM Retry con Fallback

**Contexto**: OpenRouter puede tener latencia o errores transitorios.

**Diseño**:
```python
# infrastructure/llm/openrouter_client.py
async def generate(self, prompt: str, model: str) -> LLMResponse:
    """LLM call con retry × 2 y fallback a modelo inferior."""
    for attempt in range(3):
        try:
            async with asyncio.timeout(30):
                return await self._call_api(prompt, model)
        except (asyncio.TimeoutError, httpx.HTTPError) as e:
            if attempt == 2:
                fallback = self._get_fallback_model(model)
                if fallback:
                    return await self._call_api(prompt, fallback)
                raise LLMUnavailableError(f"LLM no disponible tras 3 intentos: {e}")
            await asyncio.sleep(2 ** attempt)  # 2s, 4s backoff
```

### Patrón: Append-Only Agent Traces

**Contexto**: Las trazas de LLM son inmutables post-generación (Constitution REGLA 6).

**Diseño**:
```python
# application/interfaces/agent_trace_repository.py
class IAgentTraceRepository(ABC):
    """Repositorio de trazas — SOLO INSERT. Sin update() ni delete()."""

    @abstractmethod
    async def add(self, trace: AgentTrace) -> AgentTrace:
        """Registra nueva traza. Inmutable post-inserción."""
        ...

    @abstractmethod
    async def find_by_plan(self, plan_id: UUID) -> list[AgentTrace]:
        """Lista trazas de un plan — solo lectura."""
        ...
    # No hay update() ni delete() — por diseño
```

### Patrón: Plan State Machine en Aggregate

**Contexto**: Las transiciones de estado del plan deben ser validadas en domain layer,
no en application o presentation.

**Diseño**:
```python
# domain/aggregates/nutrition_plan.py (extensión del domain-core)
VALID_TRANSITIONS = {
    "PENDING_VET": {"ACTIVE", "PENDING_VET"},  # PENDING_VET → puede volver a PENDING_VET (devuelto)
    "ACTIVE": {"UNDER_REVIEW", "PENDING_VET", "ARCHIVED"},
    "UNDER_REVIEW": {"ACTIVE", "ARCHIVED"},
    "ARCHIVED": set()  # terminal state
}

def transition_to(self, new_status: str, actor_id: UUID, comment: str = None) -> None:
    """Transiciona estado — valida transición válida en domain."""
    if new_status not in VALID_TRANSITIONS[self.status]:
        raise InvalidPlanTransitionError(
            f"Transición inválida: {self.status} → {new_status}"
        )
    if new_status == "PENDING_VET" and not comment and self.status == "ACTIVE":
        raise MissingVetCommentError("El vet debe incluir comentario al devolver plan")
    self.status = new_status
```

### Patrón: LLM Router Determinístico

**Contexto**: El routing del LLM debe ser 100% determinístico — nunca involucra un LLM.

**Diseño**:
```python
# application/llm/llm_router.py
def select_model(tier: str, conditions_count: int) -> str:
    """Selecciona modelo LLM de forma determinística. Sin I/O, sin red."""
    if conditions_count >= 3:
        return "anthropic/claude-sonnet-4-5"  # Override clínico — no negociable
    return {
        "free":    "meta-llama/llama-3.3-70b",
        "basico":  "openai/gpt-4o-mini",
        "premium": "anthropic/claude-sonnet-4-5",
        "vet":     "anthropic/claude-sonnet-4-5",
    }.get(tier, "meta-llama/llama-3.3-70b")
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `application/llm/llm_router.py` | 100% | Unit tests — todos los tiers + override |
| `application/use_cases/plan_generation_use_case.py` | 90% | Unit + integration |
| `application/use_cases/hitl_review_use_case.py` | 90% | Unit tests |
| `infrastructure/llm/openrouter_client.py` | 80% | Unit tests con mocks |
| `infrastructure/db/agent_trace_repository.py` | 90% | Unit tests — no update |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- ADR-019: LLM routing + OpenRouter
- ADR-022: async ARQ jobs
- Constitution: REGLA 5 (LLM routing), REGLA 6 (agent_traces)
