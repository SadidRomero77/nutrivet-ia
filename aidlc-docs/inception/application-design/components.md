# Components — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10

---

## Capa: Domain

### NRCCalculator
- **Responsabilidad**: Calcula RER y DER determinísticamente (Python puro, nunca LLM)
- **Entradas**: `peso_kg`, `factor_edad`, `factor_reproductivo`, `factor_actividad`, `factor_bcs`
- **Salidas**: `rer_kcal: float`, `der_kcal: float`
- **Dependencias**: ninguna

### FoodSafetyChecker
- **Responsabilidad**: Valida ingredientes contra TOXIC_DOGS y TOXIC_CATS hard-coded
- **Entradas**: `ingredient_name: str`, `species: Species`
- **Salidas**: `is_toxic: bool`, `reason: str | None`
- **Dependencias**: ninguna (constantes Python)

### MedicalRestrictionEngine
- **Responsabilidad**: Aplica RESTRICTIONS_BY_CONDITION para las 13 condiciones soportadas
- **Entradas**: `conditions: list[MedicalCondition]`, `ingredient_name: str`
- **Salidas**: `is_restricted: bool`, `restriction_detail: str | None`
- **Dependencias**: ninguna (constantes Python)

### PetProfile (Aggregate Root)
- **Responsabilidad**: Entidad raíz del perfil de mascota — 13 campos + `pet_origin` (app_pet/clinic_pet) + campos opcionales ClinicPet (`owner_name`, `owner_phone`)
- **Entradas**: 13 campos del wizard + campos opcionales de propietario
- **Salidas**: `PetProfile` validado con invariantes
- **Dependencias**: value objects (Species, Size, ActivityLevel, BCS, ReproductiveStatus, CurrentDiet)

### NutritionPlan (Aggregate Root)
- **Responsabilidad**: Entidad raíz del plan — máquina de estados, contenido del plan, set de sustitutos pre-aprobados
- **Entradas**: `pet_id`, `modality`, `content`, `substitute_set`, `plan_type`, `status`
- **Salidas**: `NutritionPlan` con estado gestionado
- **Dependencias**: value objects (PlanStatus, PlanModality, PlanType)

### UserAccount (Aggregate Root)
- **Responsabilidad**: Usuario con rol (owner/vet) y tier de suscripción con límites
- **Entradas**: `email`, `role`, `subscription_tier`
- **Salidas**: `UserAccount` con límites aplicados
- **Dependencias**: value objects (UserRole, SubscriptionTier)

---

## Capa: Application

### PlanGenerationUseCase
- **Responsabilidad**: Orquesta generación async: calcula RER/DER → valida seguridad → enruta LLM (por tier + condiciones) → genera sustitutos → determina HITL → crea job
- **Entradas**: `pet_id`, `modality`, `user_id`
- **Salidas**: `job_id: str` (patrón async — el cliente hace polling)
- **Dependencias**: NRCCalculator, FoodSafetyChecker, MedicalRestrictionEngine, LLMRouter, PlanRepository, JobRepository, AgentTraceRepository

### HitlReviewUseCase
- **Responsabilidad**: Gestiona revisión veterinaria — aprobar con review_date, validar sustitutos, o devolver con comentario obligatorio
- **Entradas**: `plan_id`, `vet_id`, `action`, `comment?`, `review_date?`
- **Salidas**: `NutritionPlan` actualizado
- **Dependencias**: PlanRepository, NotificationService, VetRepository

### PetProfileUseCase
- **Responsabilidad**: CRUD de mascotas incluyendo ClinicPet (con owner_name + owner_phone)
- **Entradas**: campos del wizard + campos opcionales de propietario
- **Salidas**: `PetProfile` creado o actualizado
- **Dependencias**: PetRepository, UserRepository

### WeightTrackingUseCase
- **Responsabilidad**: Registra y recupera historial de peso/BCS (append-only)
- **Entradas**: `pet_id`, `weight_kg`, `bcs`, `recorded_at`
- **Salidas**: `WeightRecord` creado
- **Dependencias**: WeightRepository

### ExportPlanUseCase
- **Responsabilidad**: Genera PDF del plan ACTIVE y crea pre-signed URL en Cloudflare R2 con TTL 1h
- **Entradas**: `plan_id`, `user_id`
- **Salidas**: `download_url: str`
- **Dependencias**: PlanRepository, PDFGenerator, R2StorageClient

### PetClaimUseCase
- **Responsabilidad**: Convierte ClinicPet en AppPet vinculándola a cuenta del owner mediante código de reclamación (TTL 30 días)
- **Entradas**: `claim_code`, `owner_id`
- **Salidas**: `PetProfile` actualizado (clinic_pet → app_pet)
- **Dependencias**: PetRepository, ClaimCodeRepository

### AuthUseCase
- **Responsabilidad**: Registro, login, refresh de tokens JWT
- **Entradas**: `email`, `password`, `role`
- **Salidas**: `access_token` (15min), `refresh_token` (rotativo)
- **Dependencias**: UserRepository, JWTService

---

## Capa: Infrastructure

### PostgreSQLPetRepository
- **Responsabilidad**: Persistencia de PetProfile — tabla `pets` con columna `pet_origin`, `owner_name`, `owner_phone`
- **Dependencias**: SQLAlchemy, PostgreSQL 16 (Docker en Hetzner)

### PostgreSQLPlanRepository
- **Responsabilidad**: Persistencia de NutritionPlan + sustitutos + agent_traces (append-only, sin UPDATE)
- **Dependencias**: SQLAlchemy, PostgreSQL

### PostgreSQLUserRepository
- **Responsabilidad**: Persistencia de UserAccount con tier y rol
- **Dependencias**: SQLAlchemy, PostgreSQL

### PostgreSQLClaimCodeRepository
- **Responsabilidad**: Persistencia de códigos de reclamación con TTL 30 días
- **Dependencias**: SQLAlchemy, PostgreSQL

### LLMRouter
- **Responsabilidad**: Determina el modelo correcto según `(tier, conditions_count)` — ADR-019
- **Entradas**: `tier: SubscriptionTier`, `conditions_count: int`
- **Salidas**: `model_id: str` (string de OpenRouter)
- **Dependencias**: ninguna (lógica determinística)

### OpenRouterClient
- **Responsabilidad**: Cliente único para todos los LLMs vía OpenRouter API (texto + visión/OCR)
- **Entradas**: `model_id`, `messages`, `images?`
- **Salidas**: `completion: str`
- **Dependencias**: OpenRouter API (`OPENROUTER_API_KEY`)

### LangGraphOrchestrator
- **Responsabilidad**: Orquestador central con 4 subgrafos — clasifica intención y enruta
- **Entradas**: `NutriVetState`
- **Salidas**: `NutriVetState` actualizado
- **Dependencias**: OpenRouterClient, NRCCalculator, FoodSafetyChecker, MedicalRestrictionEngine, PostgreSQL (checkpointer)

### PDFGenerator
- **Responsabilidad**: Genera PDF del plan con plantilla HTML (WeasyPrint)
- **Entradas**: `NutritionPlan`, `PetProfile`, `vet_name`
- **Salidas**: `pdf_bytes`
- **Dependencias**: WeasyPrint

### R2StorageClient
- **Responsabilidad**: Sube PDFs e imágenes OCR a Cloudflare R2 y genera pre-signed URLs TTL 1h
- **Dependencias**: boto3 (con R2_ENDPOINT_URL personalizado — API S3-compatible)

### FCMNotificationService
- **Responsabilidad**: Push notifications via Firebase Cloud Messaging
- **Entradas**: `user_id`, `event_type`, `payload`
- **Dependencias**: firebase-admin SDK

### EmailNotificationService
- **Responsabilidad**: Emails transaccionales (plan aprobado, próximo a expirar, marketing)
- **Dependencias**: Resend API (free tier 3K emails/mes) o SMTP configurable via env var

### HiveLocalStorage (Flutter)
- **Responsabilidad**: Caché offline en Flutter — plan activo, historial de chat, peso/BCS, perfil, dashboard
- **Dependencias**: Hive (Flutter package)

### RiverpodStateManagement (Flutter)
- **Responsabilidad**: Gestión de estado en Flutter — async providers, offline/online sync
- **Dependencias**: flutter_riverpod

---

## Capa: Presentation (Backend)

### PlanRouter (FastAPI)
- **Rutas**: `POST /v1/plans` (crea job) · `GET /v1/plans/jobs/{job_id}` (polling) · `GET /v1/plans/{id}` · `PATCH /v1/plans/{id}/ingredient`
- **Dependencias**: PlanGenerationUseCase, HitlReviewUseCase, JWT middleware

### PetRouter (FastAPI)
- **Rutas**: `POST /v1/pets` · `GET /v1/pets/{id}` · `POST /v1/pets/clinic` · `POST /v1/pets/claim` · `POST /v1/pets/{id}/weight`
- **Dependencias**: PetProfileUseCase, PetClaimUseCase, WeightTrackingUseCase, JWT middleware

### AuthRouter (FastAPI)
- **Rutas**: `POST /v1/auth/register` · `POST /v1/auth/login` · `POST /v1/auth/refresh`
- **Dependencias**: AuthUseCase

### ExportRouter (FastAPI)
- **Rutas**: `POST /v1/plans/{id}/export`
- **Dependencias**: ExportPlanUseCase, JWT middleware

### AgentRouter (FastAPI + LangGraph)
- **Rutas**: `POST /v1/agent/chat` · `POST /v1/agent/scan`
- **Dependencias**: LangGraphOrchestrator, JWT middleware

### VetDashboardRouter (FastAPI)
- **Rutas**: `GET /v1/vet/patients` · `GET /v1/vet/patients/{id}/tracking` · `POST /v1/vet/patients/{id}/claim-code`
- **Dependencias**: PetProfileUseCase, WeightTrackingUseCase, JWT middleware (rol: vet)

---

## Capa: Presentation (Mobile — Flutter)

### WizardScreen — wizard 6 pasos owner (draft en Hive hasta completar)
### ClinicPetWizardScreen — wizard vet: 13 campos mascota + owner_name + owner_phone
### PlanScreen — plan activo + set de sustitutos + botón compartir
### ChatScreen — agente conversacional + historial offline (Hive)
### OCRScreen — captura imagen + resultado semáforo
### DashboardScreen — gráficas peso/BCS + estado plan (offline Hive)
### VetDashboardScreen — lista pacientes + seguimiento clínico
### AuthScreen — login / registro (owner y vet)
