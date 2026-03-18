# Tech Stack Decisions — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Scanner Service

### OpenRouter gpt-4o para OCR
**Decisión**: `openai/gpt-4o` via OpenRouter siempre, para todos los tiers.
**Razón**: gpt-4o tiene la mejor capacidad de visión para tablas nutricionales y texto estructurado. Un modelo inferior podría omitir ingredientes o transcribirlos incorrectamente — riesgo de seguridad para el paciente.
**Alternativas rechazadas**: Qwen2.5-VL-7B local (menor precisión en tablas, riesgo de seguridad), Claude-3-vision (mismo tier que gpt-4o en calidad pero OpenRouter ya tiene gpt-4o integrado), Tesseract OCR (OCR clásico sin comprensión de estructura de tabla).

### boto3 para Cloudflare R2
**Decisión**: `boto3==1.34.x` con endpoint personalizado de R2.
**Razón**: R2 es S3-compatible. boto3 es el cliente S3 más maduro en Python. No se necesita un cliente específico de Cloudflare.
**Configuración**: `signature_version="s3v4"` requerido por R2.
**Alternativas rechazadas**: `cloudflare-python` SDK (enfocado en la API de Cloudflare, no en R2 S3), `aiobotocore` (async boto3, puede agregarse si hay bottleneck de I/O en uploads).

### python-multipart para Upload de Imágenes
**Decisión**: `python-multipart` para recibir imágenes como `multipart/form-data` en FastAPI.
**Razón**: FastAPI requiere `python-multipart` para archivos (`UploadFile`). Ya es una dependencia estándar del proyecto.

### Pillow para Validación de Formato
**Decisión**: `Pillow==10.x` para verificar que el archivo es una imagen válida (JPEG/PNG/WEBP) antes de enviarlo a R2.
**Razón**: Previene uploads de archivos no-imagen disfrazados de imágenes. Verificación rápida sin llamada externa.
```python
from PIL import Image
import io
img = Image.open(io.BytesIO(image_bytes))
if img.format not in ("JPEG", "PNG", "WEBP"):
    raise ValueError(f"Formato no soportado: {img.format}")
```

### JSONB para findings y ingredients
**Decisión**: PostgreSQL JSONB para `findings`, `ingredients`, `toxic_ingredients_found`.
**Razón**: Estructura variable (número de findings por escaneo varía). JSONB permite queries sobre el contenido (`@>` para buscar por ingrediente tóxico). No requiere tabla adicional de findings.

### Dependencias del Scanner Service

```
boto3==1.34.x
Pillow==10.3.x
python-multipart==0.0.9   # ya en requirements base
httpx==0.27.x             # OpenRouter client
sqlalchemy[asyncio]==2.0.x
```

### Variables de Entorno del Scanner

```env
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=nutrivet-scans
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
OPENROUTER_API_KEY=         # compartida con otros servicios
MAX_SCAN_IMAGE_SIZE_MB=10
```
