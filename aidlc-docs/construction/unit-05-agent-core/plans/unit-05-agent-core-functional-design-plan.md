# Plan: Functional Design — Unit 05: agent-core

**Unidad**: unit-05-agent-core
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del orquestador LangGraph: NutriVetState, IntentClassifier
(5 intents), Plan Generation Subgraph (10 nodos), ReferralNode y stubs para
consultation y scanner (completados en units 06/07).

## NutriVetState — Estado Compartido (TypedDict)

```python
class NutriVetState(TypedDict):
    # Contexto de la solicitud
    user_id: str
    pet_id: str
    role: str                          # owner / vet
    subscription_tier: str             # free / basico / premium / vet

    # Input del usuario
    user_message: str
    intent: str | None                 # plan_generation / consultation / scanner / referral / emergency

    # Datos de dominio (cargados desde DB)
    pet_profile: dict | None           # PetProfile serializado
    active_plan: dict | None           # NutritionPlan serializado

    # Resultados del agente
    plan_job_id: str | None
    scan_result: dict | None
    agent_response: str | None

    # Trazabilidad
    agent_traces: list[dict]           # acumuladas durante el request — luego persist
    error: str | None
```

## IntentClassifier — 5 Intents

| Intent | Descripción | Routing |
|--------|-------------|---------|
| `plan_generation` | Crear o actualizar plan nutricional | Plan Generation Subgraph |
| `consultation` | Consulta nutricional | Consultation Subgraph |
| `scanner` | Escanear etiqueta de producto | Scanner Subgraph |
| `referral` | Consulta médica (síntomas, medicamentos, diagnósticos) | Referral Node directo |
| `emergency` | Palabras clave de emergencia detectadas | Referral Node (bypass LLM) |

**Detección de emergencia**: ANTES del clasificador LLM. Lista `EMERGENCY_KEYWORDS` es
determinista (Python frozenset) — nunca involucra LLM para detectar emergencias.

```python
EMERGENCY_KEYWORDS = frozenset({
    "convulsión", "convulsiones", "no respira", "inconsciente",
    "veneno", "envenenado", "sangrado", "atropellado",
    "no puede caminar", "no come desde", "desmayo"
})
```

## Plan Generation Subgraph — 10 Nodos

```
1. load_context         → carga PetProfile + active_plan desde DB
2. calculate_nutrition  → NRCCalculator (RER/DER — Python puro, no LLM)
3. apply_restrictions   → MedicalRestrictionEngine (hard-coded)
4. check_safety         → FoodSafetyChecker (hard-coded) — pre-LLM
5. select_llm           → LLMRouter.select_model(tier, conditions_count)
6. generate_with_llm    → OpenRouterClient.generate(prompt, model)
7. validate_output      → FoodSafetyChecker post-LLM (valida output del LLM)
8. generate_substitutes → genera substitute_set aprobado
9. determine_hitl       → requires_vet_review() → PENDING_VET o ACTIVE
10. persist_and_notify  → persiste plan + 5 secciones + agent_trace + notifica
```

**Nodos deterministas** (sin LLM): 1, 2, 3, 4, 5, 7, 8, 9, 10.
**Nodo con LLM**: solo nodo 6 — el LLM es el decisor nutricional (ingredientes, porciones).

## ReferralNode — Consultas Médicas

```python
def referral_node(state: NutriVetState) -> NutriVetState:
    """Genera mensaje estructurado para consultas médicas. Sin LLM."""
    is_emergency = state["intent"] == "emergency"
    return {
        **state,
        "agent_response": build_referral_message(
            is_emergency=is_emergency,
            vet_contact=VET_CONTACT_INFO,
            emergency_action="Ir al veterinario de emergencias más cercano" if is_emergency else None
        )
    }
```

**Estructura del mensaje de referral**:
```
"[Nombre mascota] podría tener una consulta médica que está fuera de mi área.
Te recomiendo contactar a tu veterinario de confianza.
Contacto: [vet_contact si está disponible]
[Si emergencia]: Acción urgente: Llevar inmediatamente al veterinario."
```

## Consultation Subgraph (Stub — Completar en Unit 07)

Stub que retorna: `{"agent_response": "Consultation subgraph not yet implemented"}`.
El stub permite que el orquestador funcione mientras unit-07 no esté listo.

## Scanner Subgraph (Stub — Completar en Unit 06)

Stub que retorna: `{"agent_response": "Scanner subgraph not yet implemented"}`.
El stub permite que el orquestador funcione mientras unit-06 no esté listo.

## Flujo del Orquestador (LangGraph)

```
START
  → load_context_node (carga pet_profile + active_plan)
  → emergency_detector (determinístico — keyword check)
      ↓ emergency → referral_node → END
  → intent_classifier (LLM)
      ↓ plan_generation → plan_generation_subgraph → END
      ↓ consultation    → consultation_subgraph → END
      ↓ scanner         → scanner_subgraph → END
      ↓ referral        → referral_node → END
```

## Casos de Prueba Críticos

- [ ] Intent "consulta nutricional sobre proteínas" → `consultation`
- [ ] Intent "convulsión" → `emergency` (sin LLM, < 1ms)
- [ ] Intent "quiero crear un plan para mi perro" → `plan_generation`
- [ ] Consulta médica ("síntomas de fiebre") → `referral`
- [ ] Emergencia no consume cuota de preguntas del Free tier
- [ ] Plan subgraph: RER/DER calculado sin LLM (Sally: ±0.5 kcal)
- [ ] Plan subgraph: output LLM validado post-generación (FoodSafetyChecker)
- [ ] Orquestador carga contexto (pet_profile + active_plan) antes de clasificar

## Referencias

- Spec: `aidlc-docs/inception/units/unit-05-agent-core.md`
- ADR-019: LLM routing
- Domain: `_shared/domain-entities.md`
- Business logic: `_shared/business-logic-model.md`
