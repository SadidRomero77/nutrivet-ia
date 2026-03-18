# Domain Entities — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Scanner Service

### LabelScan (Aggregate Raíz)
- `scan_id: UUID`
- `pet_id: UUID` — mascota a la que se evalúa el producto
- `owner_id: UUID`
- `image_type: ImageType` — tipo de imagen aceptado
- `status: ScanStatus` — estado del procesamiento
- `r2_image_key: str | None` — clave en Cloudflare R2 donde se almacena la imagen
- `raw_ocr_text: str | None` — texto extraído por OCR
- `parsed_nutrients: NutritionalProfile | None` — perfil nutricional parseado
- `evaluation: ProductEvaluation | None` — resultado de la evaluación
- `semaphore: SemaphoreColor | None` — verde/amarillo/rojo
- `error_message: str | None`
- `created_at: datetime`
- `completed_at: datetime | None`

### ProductEvaluation
Resultado detallado de la evaluación del producto vs. perfil de la mascota.
- `evaluation_id: UUID`
- `scan_id: UUID`
- `overall_score: float` — 0.0–1.0
- `semaphore: SemaphoreColor`
- `findings: list[EvaluationFinding]`
- `toxic_ingredients_found: list[str]` — de TOXIC_DOGS/TOXIC_CATS
- `restricted_ingredients_found: list[str]` — de RESTRICTIONS_BY_CONDITION
- `missing_nutrients: list[str]`
- `excess_nutrients: list[str]`
- `recommendation: str` — generado por LLM post-validación

### NutritionalProfile (Value Object)
Perfil nutricional parseado de la etiqueta escaneada.
- `protein_pct: float | None`
- `fat_pct: float | None`
- `fiber_pct: float | None`
- `moisture_pct: float | None`
- `ash_pct: float | None`
- `calories_per_100g: float | None`
- `ingredients: list[str]` — lista de ingredientes parseada del texto OCR

## Enums del Scanner

### ImageType
```python
class ImageType(str, Enum):
    NUTRITION_TABLE  = "nutrition_table"
    INGREDIENTS_LIST = "ingredients_list"
    # NUNCA: brand, logo, packaging_front
```

### ScanStatus
```python
class ScanStatus(str, Enum):
    PENDING     = "pending"
    PROCESSING  = "processing"
    COMPLETED   = "completed"
    FAILED      = "failed"
    REJECTED    = "rejected"  # imagen inválida (no es tabla nutricional)
```

### SemaphoreColor
```python
class SemaphoreColor(str, Enum):
    GREEN  = "green"   # producto adecuado para la mascota
    YELLOW = "yellow"  # producto con advertencias menores
    RED    = "red"     # producto no recomendado o tóxico
```

### EvaluationFinding
```python
@dataclass
class EvaluationFinding:
    finding_type: Literal["toxic", "restricted", "excess", "deficiency", "allergen"]
    nutrient_or_ingredient: str
    detail: str
    severity: Literal["critical", "warning", "info"]
```
