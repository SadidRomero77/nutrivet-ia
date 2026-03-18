# Business Logic Model — unit-04-plan-service
**Unidad**: unit-04-plan-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos E2E del Plan Service

### Flujo 1: Solicitar Generación de Plan

```
POST /plans/generate { pet_id, modalidad }
  ↓
1. Verificar ownership: pet.owner_id == current_user.user_id
2. Verificar límite de planes del tier
3. Verificar que no hay plan ACTIVE o PENDING_VET ya existente para el pet
4. Crear PlanJob(status="queued")
5. Encolar en ARQ: await arq_queue.enqueue("generate_plan_worker", job_id)
6. Retornar { job_id } + HTTP 202 Accepted
```

### Flujo 2: Worker ARQ — generate_plan_worker(job_id)

```
ARQ worker ejecuta en background:
  ↓
1. Cargar PlanJob y PetProfile desde DB
2. Actualizar PlanJob.status = "processing"
3. Calcular NRC: nrc_result = NRCCalculator().calculate(pet_profile)
   [RER/DER calculados en Python — NUNCA por LLM]
4. Determinar modelo LLM: model = LLMRouter().resolve_model(pet_profile)
5. Construir prompt con:
   - pet_id (UUID, sin nombre ni especie en texto)
   - nrc_result.der_kcal, nrc_result.rer_kcal
   - condiciones_medicas desencriptadas
   - modalidad (natural/concentrado)
   - instrucciones del sistema
6. Llamar OpenRouter API: response = await openrouter.complete(model, prompt)
7. Registrar AgentTrace(llm_model, tokens, latency, node="plan_generation")
8. Parsear respuesta: sections = parse_plan_sections(response.content)
9. Validar cada ingrediente: FoodSafetyChecker.check_all(ingredients, especie)
   → Si tóxico: PlanJob.status="failed", error_message="Ingrediente tóxico detectado"
   → STOP — no persistir el plan
10. Validar restricciones médicas: MedicalRestrictionEngine.check_all(ingredients, conditions)
    → Si violación: re-generar con prompt corregido (max 2 reintentos)
    → Si persiste: PlanJob.status="failed"
11. Determinar status: si condiciones_medicas → PENDING_VET, else ACTIVE
12. Crear NutritionPlan con todas las secciones validadas
13. PlanJob.status = "completed", result_plan_id = plan.plan_id
14. Enviar push notification al owner
```

### Flujo 3: Polling del Job

```
GET /plans/jobs/{job_id}
  ↓
1. Verificar ownership del job
2. Retornar PlanJob { status, result_plan_id, error_message }
3. Si status == "completed" → el cliente carga GET /plans/{result_plan_id}
```

### Flujo 4: Firma de Plan por Vet (HITL)

```
PATCH /plans/{plan_id}/approve (requiere role == "vet")
  ↓
1. Verificar que plan.status == PENDING_VET
2. Verificar que el vet tiene acceso a la mascota (ClinicPet o asignación)
3. Vet puede editar secciones (con registro de cambio en AgentTrace)
4. Si vet aprueba:
   - plan.status = ACTIVE
   - plan.vet_id = vet.user_id
   - plan.activated_at = now()
   - Si temporal_medical: plan.review_date seteado por vet
5. Push notification al owner: "Tu plan fue aprobado"

PATCH /plans/{plan_id}/return (requiere role == "vet")
  ↓
1. Verificar plan.status == PENDING_VET
2. Requiere vet_comment (obligatorio)
3. plan.status permanece PENDING_VET
4. plan.vet_comment = comment
5. Push notification al owner con el comentario
```

### Flujo 5: Archivar Plan

```
Trigger automático: owner genera nuevo plan → plan anterior a ARCHIVED
  ↓
1. plan_anterior.status = ARCHIVED
2. plan_anterior.archived_at = now()
3. El plan archivado permanece accesible en histórico (nunca DELETE)
```
