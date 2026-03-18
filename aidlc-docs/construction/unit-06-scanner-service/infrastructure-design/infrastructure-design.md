# Infrastructure Design — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura del Scanner Service

### R2StorageClient

```python
# infrastructure/scanner/r2_storage_client.py
import boto3
from botocore.config import Config

class R2StorageClient:
    """Cliente Cloudflare R2 (S3-compatible) para almacenar imágenes de escaneo."""

    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )

    async def upload_scan_image(self, scan_id: UUID, owner_id: UUID, image_bytes: bytes, ext: str) -> str:
        """Subir imagen de escaneo a R2. Retorna la clave R2."""
        key = f"scans/{owner_id}/{scan_id}.{ext}"
        self._client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=image_bytes,
            ContentType=f"image/{ext}",
        )
        return key

    def get_presigned_url(self, r2_key: str, expires_in: int = 3600) -> str:
        """Generar URL pre-firmada para acceso temporal a la imagen."""
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.R2_BUCKET_NAME, "Key": r2_key},
            ExpiresIn=expires_in,
        )
```

### OpenRouterOCRClient

```python
# infrastructure/scanner/openrouter_ocr_client.py
class OpenRouterOCRClient:
    """Cliente para OCR con gpt-4o vision via OpenRouter. Siempre usa gpt-4o."""

    OCR_MODEL = "openai/gpt-4o"  # NUNCA cambiar este modelo para OCR

    async def extract_nutrition_info(self, image_url: str) -> dict:
        """Extraer información nutricional de la imagen via gpt-4o vision."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": OCR_PROMPT},
                ]
            }
        ]
        response = await self._openrouter_client.complete(
            model=self.OCR_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )
        return json.loads(response)
```

### OCR Prompt

```python
OCR_PROMPT = """
Analiza esta imagen de etiqueta de alimento para mascotas.
Si es una TABLA NUTRICIONAL, extrae en JSON:
{ "type": "nutrition_table", "protein_pct": float, "fat_pct": float,
  "fiber_pct": float, "moisture_pct": float, "ash_pct": float,
  "calories_per_100g": float, "ingredients": ["list", "of", "ingredients"] }

Si es una LISTA DE INGREDIENTES, extrae en JSON:
{ "type": "ingredients_list", "ingredients": ["ingredient1", "ingredient2", ...] }

Si NO es ninguna de las dos, responde:
{ "type": "invalid", "reason": "descripción de lo que es la imagen" }

Responde SOLO con JSON válido, sin texto adicional.
"""
```

## Dependencias del Scanner Service

```
boto3==1.34.x      # R2/S3 client
httpx==0.27.x      # OpenRouter calls
Pillow==10.x       # Validación de formato de imagen
python-multipart   # FastAPI multipart form data
```
