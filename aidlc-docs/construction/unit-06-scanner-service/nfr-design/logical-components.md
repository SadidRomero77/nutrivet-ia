# Logical Components — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Scanner Service

### ScanUseCase
**Responsabilidad**: Orquestar el pipeline completo de escaneo.
**Capa**: application/scanner/
**Dependencias**: ScanRepositoryPort, R2StoragePort, OCRClientPort, FoodSafetyChecker, MedicalRestrictionEngine
**Métodos**:
```
scan_label(pet_id, owner_id, image_bytes, image_type) → LabelScan
get_scan(scan_id, owner_id) → LabelScan
list_scans_by_pet(pet_id, owner_id) → list[LabelScan]
```

### ImageValidator
**Responsabilidad**: Validar que la imagen es tabla nutricional o lista de ingredientes.
**Capa**: infrastructure/scanner/
**Dependencias**: OpenRouterOCRClient (gpt-4o con prompt de clasificación)
**Output**: `Literal["nutrition_table", "ingredients_list", "invalid"]`
**Regla crítica**: Debe ser el primer paso antes del OCR de extracción.

### NutritionalProfileParser
**Responsabilidad**: Parsear el JSON del OCR a NutritionalProfile estructurado.
**Capa**: application/scanner/
**Dependencias**: ninguna (parsing de dict a dataclass)
**Manejo de errores**: Si faltan campos clave → `NutritionalProfile` parcial, no fallo total.

### NutritionalProfileEvaluator
**Responsabilidad**: Evaluar el NutritionalProfile contra el perfil completo del pet.
**Capa**: application/scanner/
**Dependencias**: FoodSafetyChecker (domain), MedicalRestrictionEngine (domain)
**Lógica**:
```
check toxicity → findings críticos (RED)
check medical restrictions → findings críticos o warnings
check allergies → findings críticos
check nutritional balance vs DER → findings informativos
calculate semaphore → determinista
```

### R2StorageClient
**Responsabilidad**: Upload de imágenes y presigned URLs de Cloudflare R2.
**Capa**: infrastructure/scanner/
**Implementa**: R2StoragePort

### OpenRouterOCRClient
**Responsabilidad**: Invocar gpt-4o vision para extracción de texto nutricional.
**Capa**: infrastructure/scanner/
**Regla**: SIEMPRE usa `openai/gpt-4o` — nunca un modelo diferente.

### ScannerRouter
**Responsabilidad**: Endpoints HTTP del scanner.
**Capa**: presentation/scanner/
**Endpoints**:
```
POST /scanner/scan                → 200 ScanResult
GET  /scanner/scans/{scan_id}    → 200 LabelScan
GET  /pets/{pet_id}/scans        → 200 list[LabelScan]
```

## Diagrama de Pipeline

```
ScannerRouter (multipart image)
    ↓
ScanUseCase
    ↓
R2StorageClient.upload()         → Cloudflare R2
    ↓
ImageValidator (gpt-4o)          → valid / rejected
    ↓
OCRClient.extract() (gpt-4o)     → NutritionalProfile raw
    ↓
NutritionalProfileParser         → NutritionalProfile structured
    ↓
FoodSafetyChecker (domain)       → toxic_findings (determinista)
    ↓
MedicalRestrictionEngine (domain) → restriction_findings (determinista)
    ↓
AllergyChecker (domain)          → allergy_findings (determinista)
    ↓
SemaphoreCalculator (domain)     → RED / YELLOW / GREEN (determinista)
    ↓
LLM recommendation (OpenRouter)  → texto explicativo (creativo, no determina semáforo)
    ↓
PostgreSQL INSERT (label_scans + product_evaluations)
```
