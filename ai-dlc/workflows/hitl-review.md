# Workflow — HITL (Human-In-The-Loop) Revisión Veterinaria

**Aplica solo a**: Mascotas con condición médica registrada.
**Actor humano**: Veterinario firmante (rol `vet`).

---

## Diagrama de Flujo

```
Plan generado con condición médica
plan.status = PENDING_VET
       │
       ▼
Notificación push al vet asignado
"Nuevo plan para revisión: {pet_name} — {conditions}"
       │
       ▼
Vet accede al dashboard clínico
  → Ve: perfil completo de la mascota
  → Ve: plan generado por el agente (ingredientes, porciones, DER)
  → Ve: trazabilidad completa (agent_traces inmutables)
  → Ve: restricciones aplicadas por condición
       │
       ├──── Vet APRUEBA ────────────────────────────────────────┐
       │     → plan.status = ACTIVE                              │
       │     → plan.approved_by = vet_id                        │
       │     → plan.review_date = (para plan temporal_medical)  │
       │     → Notificación push al owner: "Plan aprobado"      │
       │                                                         │
       └──── Vet RECHAZA / MODIFICA ─────────────────────────────┘
             → Vet edita el plan con justificación obligatoria
             → plan.status = ACTIVE (si vet edita y aprueba)
             → Cambio registrado en plan_changes (inmutable)
             → Notificación push al owner con nota del vet
```

---

## Reglas de Negocio del Workflow

1. **HITL es exclusivo** para mascotas con condición médica. Mascotas sanas → ACTIVE directo, nunca pasan por vet.
2. **Si owner agrega condición a plan ACTIVE** → plan vuelve a `PENDING_VET` automáticamente.
3. El vet **puede editar** el plan, pero toda edición queda en `plan_changes` con justificación obligatoria.
4. El vet **no puede sobrescribir** las restricciones hard-coded de `RESTRICTIONS_BY_CONDITION`.
5. **`review_date`** es obligatorio para planes `temporal_medical` — el vet lo define al aprobar.
6. El vet **no puede** ver nombres de otros owners/mascotas fuera de su scope — RBAC estricto.

---

## Tipos de Plan Post-HITL

| Tipo | Cuándo | `review_date` |
|------|--------|---------------|
| `temporal_medical` | Condición médica activa | Obligatorio (vet define) |
| `life_stage` | Cachorro/gatito | Automático (milestones: 3m, 6m, 12m, 18m) |
| `estándar` | Mascota sana | No aplica (sin expiración) |

---

## Estados del Plan

```
PENDING_VET
    │
    ├── Vet aprueba → ACTIVE
    │                   │
    │                   ├── Trigger (review_date o milestone) → UNDER_REVIEW
    │                   │                                            │
    │                   │                                      PENDING_VET (si vet asignado)
    │                   │                                      o ACTIVE directo (si sana)
    │                   │
    │                   └── Owner agrega condición → PENDING_VET
    │
    └── Plan anterior → ARCHIVED
```
