# Domain Events — NutriVet.IA

Eventos que cruzan bounded contexts. Son inmutables y representan algo que ocurrió en el dominio.

---

## Catálogo de Eventos

### Identity Context

| Evento | Cuándo se emite | Consumidores |
|--------|-----------------|-------------|
| `UserRegistered` | Owner o vet se registra exitosamente | Notification, Audit |
| `UserSubscriptionChanged` | Owner cambia de tier | Pet Management (límites) |
| `TokenRevoked` | Logout o refresh token comprometido | Auth middleware |

---

### Pet Management Context

| Evento | Cuándo se emite | Payload | Consumidores |
|--------|-----------------|---------|-------------|
| `PetProfileCreated` | Wizard de mascota completado (12 campos) | `pet_id`, `species`, `owner_id` | Nutrition Planning |
| `PetProfileUpdated` | Owner actualiza cualquier campo del perfil | `pet_id`, `fields_changed` | Nutrition Planning |
| `MedicalConditionAdded` | Owner agrega condición médica a mascota | `pet_id`, `condition`, `plan_id` | Nutrition Planning (→ PENDING_VET) |
| `AllergyRegistered` | Nueva alergia/intolerancia registrada | `pet_id`, `allergen` | Nutrition Planning |

---

### Nutrition Planning Context

| Evento | Cuándo se emite | Payload | Consumidores |
|--------|-----------------|---------|-------------|
| `PlanGenerationRequested` | Owner solicita generación de plan | `pet_id`, `modality`, `async_job_id` | Agent (LangGraph) |
| `PlanGenerated` | Agente completa la generación | `plan_id`, `pet_id`, `status`, `model_used` | Vet Review o Owner (notificación) |
| `PlanActivated` | Plan pasa a ACTIVE (mascota sana) | `plan_id`, `pet_id` | Notification → Owner |
| `PlanPendingVet` | Plan con condición médica espera firma | `plan_id`, `pet_id`, `vet_id` | Vet Review → Notification → Vet |
| `PlanArchived` | Plan anterior archivado al generar nuevo | `plan_id`, `replaced_by_plan_id` | Audit |
| `ToxicIngredientDetected` | Ingrediente tóxico detectado en output LLM | `pet_id`, `ingredient`, `plan_id` | Audit, Alert (P0) |

---

### Vet Review Context

| Evento | Cuándo se emite | Payload | Consumidores |
|--------|-----------------|---------|-------------|
| `PlanApprovedByVet` | Vet firma el plan | `plan_id`, `vet_id`, `review_date?` | Nutrition Planning (→ ACTIVE), Notification → Owner |
| `PlanEditedByVet` | Vet modifica el plan antes de aprobar | `plan_id`, `vet_id`, `justification`, `changes` | Audit (plan_changes) |
| `PlanUnderReview` | Plan ACTIVE alcanza review_date o milestone | `plan_id`, `trigger_reason` | Vet Review |

---

### Agent Conversation Context

| Evento | Cuándo se emite | Payload | Consumidores |
|--------|-----------------|---------|-------------|
| `MedicalQueryDetected` | Agente detecta consulta médica | `session_id`, `query_snippet_anon` | Referral Node |
| `ReferralIssued` | Agente emite mensaje de derivación al vet | `session_id`, `urgency_level` | Notification |
| `NutritionalQueryAnswered` | Agente responde consulta nutricional | `session_id`, `model_used` | AgentTrace |

---

### Scanning Context

| Evento | Cuándo se emite | Payload | Consumidores |
|--------|-----------------|---------|-------------|
| `LabelScanRequested` | Owner envía imagen | `scan_id`, `pet_id` | Scanner Subgraph |
| `LabelScanCompleted` | OCR exitoso y evaluación lista | `scan_id`, `result`, `semaphore_color` | Notification → Owner |
| `InvalidImageRejected` | Imagen no es tabla nutricional/ingredientes | `scan_id`, `reason` | Notification → Owner |

---

## Formato de Evento (Python)

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)  # Inmutable
class DomainEvent:
    event_id: UUID
    occurred_at: datetime
    version: int = 1

@dataclass(frozen=True)
class PlanGenerated(DomainEvent):
    plan_id: UUID
    pet_id: UUID       # ID anónimo — nunca nombre
    status: str        # ACTIVE o PENDING_VET
    model_used: str    # ollama-qwen7b | groq-llama70b | gpt-4o
    der_kcal: float
```

**Regla**: Los eventos de dominio son inmutables (`frozen=True`). No se modifican una vez creados.
