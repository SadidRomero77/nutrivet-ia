# Bounded Contexts — NutriVet.IA

Mapa de los contextos delimitados del sistema y sus relaciones.

---

## Mapa de Contextos

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          NutriVet.IA System                              │
│                                                                          │
│  ┌─────────────┐      ┌──────────────────┐      ┌─────────────────────┐ │
│  │  Identity   │─────▶│  Pet Management  │─────▶│ Nutrition Planning  │ │
│  │  Context    │      │     Context      │      │      Context        │ │
│  │             │      │                  │      │                     │ │
│  │ Users       │      │ PetProfile       │      │ NutritionPlan       │ │
│  │ Auth/JWT    │      │ MedicalCondition │      │ NRC Calculator      │ │
│  │ RBAC        │      │ FoodAllergy      │      │ LLM Routing         │ │
│  │ Subscriptions│     │ BCS              │      │ Plan Generation     │ │
│  └─────────────┘      └──────────────────┘      │ Weight Journey      │ │
│                                │                └──────────┬──────────┘ │
│                                │                           │            │
│                                ▼                           ▼            │
│                       ┌────────────────┐      ┌───────────────────────┐ │
│                       │  Vet Review   │      │   Agent Conversation  │ │
│                       │   Context     │      │       Context         │ │
│                       │               │      │                       │ │
│                       │ HITL          │      │ Consultation Subgraph │ │
│                       │ PlanApproval  │      │ Referral Node         │ │
│                       │ PlanChange    │      │ Intent Classification │ │
│                       │ VetDashboard  │      │ NutriVetState         │ │
│                       └───────────────┘      └───────────────────────┘ │
│                                                                          │
│                       ┌───────────────┐                                 │
│                       │   Scanning    │                                 │
│                       │   Context     │                                 │
│                       │               │                                 │
│                       │ OCR Pipeline  │                                 │
│                       │ LabelScan     │                                 │
│                       │ ProductEval   │                                 │
│                       └───────────────┘                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Descripción de Cada Contexto

### 1. Identity Context
**Responsabilidad**: Autenticación, autorización y gestión de subscripciones.

| Entidad/Concepto | Descripción |
|------------------|-------------|
| `User` | Owner o Vet con email, rol y tier de subscripción |
| `RefreshToken` | Token rotativo para renovar JWT |
| `UserConsent` | Registro de consentimiento (GDPR/Ley 1581) |
| `Subscription` | Free / Básico / Premium / Vet con límites |

**Lenguaje**: autenticar, autorizar, registrar, revocar token, verificar rol.

**Relación con otros contextos**: Provee `user_id` y `role` a todos los demás contextos.

---

### 2. Pet Management Context
**Responsabilidad**: Ciclo de vida completo del perfil de mascota.

| Entidad/Concepto | Descripción |
|------------------|-------------|
| `PetProfile` | Aggregate root — 12 campos obligatorios |
| `MedicalCondition` | Una de las 13 condiciones soportadas |
| `FoodAllergy` | Alergia o intolerancia conocida |
| `BCS` | Body Condition Score 1-9 |

**Lenguaje**: registrar mascota, actualizar perfil, agregar condición, reportar alergia.

**Regla crítica**: Agregar una condición médica a una mascota con plan `ACTIVE` → emite evento `MedicalConditionAdded` que dispara re-evaluación del plan.

---

### 3. Nutrition Planning Context
**Responsabilidad**: Generación y ciclo de vida de planes nutricionales.

| Entidad/Concepto | Descripción |
|------------------|-------------|
| `NutritionPlan` | Aggregate root — plan con tipo, estado, contenido |
| `NRCCalculator` | Calculadora determinista de RER/DER |
| `FoodToxicityChecker` | Verificador hard-coded de alimentos |
| `MedicalRestrictions` | RESTRICTIONS_BY_CONDITION hard-coded |
| `LLMRouter` | Selección de modelo según condiciones |
| `WeightJourney` | Fases reducción/mantenimiento/aumento |

**Lenguaje**: generar plan, calcular RER, verificar toxicidad, aplicar restricción, aprobar plan.

**Regla crítica**: NRC Calculator y FoodToxicityChecker son deterministas. El LLM solo actúa con los outputs de estos como restricciones.

---

### 4. Vet Review Context
**Responsabilidad**: HITL — revisión, edición y aprobación de planes por veterinario.

| Entidad/Concepto | Descripción |
|------------------|-------------|
| `PlanApproval` | Acto de firma del vet sobre un plan PENDING_VET |
| `PlanChange` | Modificación de plan por vet con justificación |
| `VetDashboard` | Vista clínica de planes pendientes |

**Lenguaje**: revisar plan, firmar plan, rechazar plan, editar con justificación, asignar review_date.

**Regla crítica**: Solo mascotas con condición médica llegan a este contexto. El vet no puede acceder a mascotas fuera de su scope.

---

### 5. Agent Conversation Context
**Responsabilidad**: Interacción conversacional del agente con el owner.

| Entidad/Concepto | Descripción |
|------------------|-------------|
| `ConversationHistory` | Historial de mensajes en NutriVetState |
| `Intent` | Clasificación: nutricional / médica / plan / scan |
| `ReferralMessage` | Mensaje estructurado de derivación al vet |

**Lenguaje**: consultar, responder, derivar al vet, clasificar intención.

**Regla crítica**: Si `intent == medical` → siempre derivar. Nunca responder consultas de síntomas, medicamentos o diagnósticos.

---

### 6. Scanning Context
**Responsabilidad**: OCR de etiquetas nutricionales y evaluación del producto.

| Entidad/Concepto | Descripción |
|------------------|-------------|
| `LabelScan` | Resultado del análisis OCR |
| `ProductEvaluation` | Semáforo verde/amarillo/rojo vs perfil mascota |
| `ImageValidator` | Verifica que la imagen es tabla nutricional o ingredientes |

**Lenguaje**: escanear etiqueta, extraer tabla nutricional, evaluar producto, emitir semáforo.

**Regla crítica**: Rechazar imágenes que no sean tabla nutricional o lista de ingredientes. NUNCA logos, marcas o empaque frontal.

---

## Relaciones Entre Contextos

| Relación | Tipo | Dirección | Evento/Mecanismo |
|----------|------|-----------|-----------------|
| Identity → Pet Management | Customer/Supplier | Identity provee user_id | JWT claims |
| Pet Management → Nutrition Planning | Customer/Supplier | Pet provee PetProfile | `PetProfileCompleted` event |
| Nutrition Planning → Vet Review | Customer/Supplier | Plan provee plan_id | `PlanPendingVet` event |
| Vet Review → Nutrition Planning | Conformist | Vet actualiza status | `PlanApproved` event |
| Pet Management → Nutrition Planning | Event | Agrega condición | `MedicalConditionAdded` event |
| Nutrition Planning → Agent Conversation | Shared Kernel | NutriVetState | Estado compartido LangGraph |
| Scanning → Nutrition Planning | Customer/Supplier | Scan usa PetProfile | API call |
