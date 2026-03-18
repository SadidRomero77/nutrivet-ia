# Component Methods — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10

Solo se documentan los métodos críticos de cada componente.

---

## Domain Layer

### NRCCalculator

```python
def calculate_rer(peso_kg: float) -> float:
    """Calcula Resting Energy Requirement. RER = 70 × peso_kg^0.75"""

def calculate_der(rer: float, factor_edad: float, factor_reproductivo: float,
                  factor_actividad: float, factor_bcs: float) -> float:
    """Calcula Daily Energy Requirement aplicando todos los factores."""

def get_weight_journey_factor(bcs: int) -> float:
    """Retorna factor de ajuste: BCS≤3→1.2 · BCS 4-6→1.0 · BCS≥7→0.8"""
```
**Errores**: `ValueError` si peso_kg ≤ 0 o bcs fuera de rango 1-9.

---

### FoodSafetyChecker

```python
def is_toxic(ingredient_name: str, species: Species) -> tuple[bool, str | None]:
    """Verifica si el ingrediente está en TOXIC_DOGS o TOXIC_CATS.
    Retorna (True, razón) si es tóxico. (False, None) si es seguro."""

def validate_ingredient_list(ingredients: list[str], species: Species) -> list[ToxicityResult]:
    """Valida una lista completa de ingredientes. Retorna todos los resultados."""
```
**Errores**: Nunca — retorna siempre un resultado. Los tóxicos son decisión determinística.

---

### MedicalRestrictionEngine

```python
def is_restricted(ingredient_name: str,
                  conditions: list[MedicalCondition]) -> tuple[bool, str | None]:
    """Verifica si el ingrediente está restringido para alguna de las condiciones.
    Retorna (True, detalle) si está restringido."""

def get_all_restrictions(conditions: list[MedicalCondition]) -> dict[str, list[str]]:
    """Retorna mapa completo de ingredientes → restricciones para las condiciones dadas."""
```

---

## Application Layer

### PlanGenerationUseCase

```python
async def execute(pet_id: UUID, modality: PlanModality,
                  user_id: UUID) -> str:
    """Crea un job de generación de plan. Retorna job_id para polling.
    El plan se genera en background — el cliente consulta GET /plans/jobs/{job_id}."""

async def get_job_status(job_id: str) -> PlanJobStatus:
    """Retorna estado del job: PENDING | PROCESSING | READY | FAILED"""
```
**Errores**: `PetNotFoundError` · `InsufficientTierError` · `PlanGenerationError`

---

### HitlReviewUseCase

```python
async def approve(plan_id: UUID, vet_id: UUID,
                  review_date: date | None = None) -> NutritionPlan:
    """Aprueba el plan → ACTIVE. review_date obligatorio para planes con condición médica."""

async def return_with_comment(plan_id: UUID, vet_id: UUID,
                               comment: str) -> NutritionPlan:
    """Devuelve el plan a PENDING_VET con comentario obligatorio. Sin estado RECHAZADO."""

async def validate_substitute_set(plan_id: UUID, vet_id: UUID,
                                   approved_substitutes: list[UUID],
                                   rejected_substitutes: list[UUID]) -> NutritionPlan:
    """Vet valida el set de sustitutos generado por el agente."""
```
**Errores**: `PlanNotFoundError` · `VetNotAuthorizedError` · `CommentRequiredError`

---

### ExportPlanUseCase

```python
async def export_to_pdf(plan_id: UUID, user_id: UUID) -> str:
    """Genera PDF del plan ACTIVE y retorna pre-signed URL S3 con TTL 72h.
    Solo planes en estado ACTIVE son exportables."""
```
**Errores**: `PlanNotActiveError` · `UnauthorizedError`

---

### PetClaimUseCase

```python
async def claim_pet(claim_code: str, owner_id: UUID) -> PetProfile:
    """Vincula ClinicPet al owner. Convierte clinic_pet → app_pet.
    Preserva historial completo. El vet sigue vinculado."""
```
**Errores**: `ClaimCodeNotFoundError` · `ClaimCodeExpiredError` · `PetAlreadyClaimedError`

---

## Infrastructure Layer

### LLMRouter

```python
def route(tier: SubscriptionTier, conditions_count: int) -> str:
    """Retorna el model_id de OpenRouter según tier y condiciones.
    Override: conditions_count >= 3 → siempre claude-sonnet-4-5."""
```

---

### OpenRouterClient

```python
async def complete(model_id: str, messages: list[dict],
                   max_tokens: int = 4096) -> str:
    """Llamada de texto al modelo via OpenRouter. Timeout 55s."""

async def complete_with_vision(model_id: str, messages: list[dict],
                                image_bytes: bytes) -> str:
    """Llamada con imagen para OCR. Siempre usa openai/gpt-4o."""
```
**Errores**: `LLMTimeoutError` · `LLMRateLimitError` · `LLMUnavailableError`
**Retry**: × 2 reintentos con backoff exponencial antes de fallar.

---

### LangGraphOrchestrator

```python
async def process(state: NutriVetState) -> NutriVetState:
    """Punto de entrada del orquestador. Clasifica intención y enruta al subgrafo correcto:
    - plan_generation: crear/actualizar plan
    - consultation: consulta nutricional
    - scanner: OCR de etiqueta
    - referral: consulta médica → remite al vet"""
```
