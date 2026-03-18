# Plan: Infrastructure Design — Unit 06: scanner-service

**Unidad**: unit-06-scanner-service
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| ScannerSubgraph (reemplaza stub) | `infrastructure/agent/subgraphs/scanner.py` |
| ImageValidator node | `infrastructure/agent/nodes/image_validator.py` |
| NutritionalEvaluator node | `infrastructure/agent/nodes/nutritional_evaluator.py` |
| R2StorageClient (upload) | `infrastructure/storage/r2_client.py` (compartido con unit-08) |
| OCRClient (gpt-4o) | `infrastructure/llm/openrouter_client.py` — modelo fijo gpt-4o |
| ScanResultRepository | `infrastructure/db/label_scan_repository.py` |

**Servidor**: In-process dentro del contenedor FastAPI en Hetzner CPX31.
El scanner corre como subgrafo de LangGraph — no es un servicio separado.

### Storage — Cloudflare R2

**Bucket**: `nutrivet-storage-{env}` (ej: `nutrivet-storage-prod`, `nutrivet-storage-staging`)

**Key structure**:
```
scans/{scan_id}/{content_hash}.{jpg|png|webp}
```

**Acceso**:
- Upload: boto3 `put_object` con `ContentType: image/*`
- No se genera pre-signed URL para scans — las imágenes son internas al sistema
- Retención: 30 días (lifecycle rule configurada en R2)

### Storage — PostgreSQL

**Tabla `label_scans`**:
```sql
CREATE TABLE label_scans (
    scan_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id          UUID NOT NULL,  -- sin FK — anónimo para trazabilidad
    owner_id        UUID REFERENCES users(user_id),
    r2_key          VARCHAR(500) NOT NULL,      -- clave en R2
    image_type      VARCHAR(30) NOT NULL,       -- nutrition_table / ingredient_list / rejected
    semaphore       VARCHAR(10),                -- rojo / amarillo / verde / null (si rechazado)
    ocr_success     BOOLEAN DEFAULT FALSE,
    nutritional_profile JSONB,
    detected_issues JSONB,
    llm_model_used  VARCHAR(100) DEFAULT 'openai/gpt-4o',
    latency_ms      INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_label_scans_pet_id ON label_scans(pet_id, created_at DESC);
```

### OCR — OpenRouter gpt-4o Vision

- **Modelo**: `openai/gpt-4o` — fijo para todos los tiers (ADR-019).
- **Endpoint**: `https://openrouter.ai/api/v1/chat/completions`
- **Formato**: multimodal — imagen como base64 o URL de R2.

**Flujo de imagen**:
```
1. Cliente sube imagen (multipart/form-data) → FastAPI endpoint
2. FastAPI valida tipo MIME (image/jpeg, image/png, image/webp — max 5MB)
3. Upload a R2 → r2_key obtenido
4. r2_key + prompt → gpt-4o vision
5. gpt-4o accede a imagen desde R2 URL (o base64 si R2 URL no es pública)
```

**Nota**: Si R2 no tiene URLs públicas → usar base64 encoding de la imagen en el prompt.

### Alembic Migrations

```
013_label_scans.py → tabla label_scans + índice
```

### Variables de Entorno Requeridas

```bash
# R2 — compartido con unit-08
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<R2 access key>
R2_SECRET_ACCESS_KEY=<R2 secret key>
R2_BUCKET_NAME=nutrivet-storage-prod

# OpenRouter — ya configurado desde unit-04
OPENROUTER_API_KEY=<clave de OpenRouter>
```

## Notas Arquitecturales

1. **Image-first upload**: La imagen se sube a R2 ANTES de llamar a gpt-4o. Esto
   separa el almacenamiento del procesamiento y permite reintentar el OCR sin
   re-subir la imagen.

2. **R2 vs inline base64**: Si R2 no permite URLs públicas en el plan gratuito,
   usar base64 encoding. El R2Client abstraerá esta diferencia.

3. **Retención de imágenes**: Las imágenes de scan se retienen 30 días (lifecycle
   rule en R2). Después se eliminan automáticamente — las imágenes no son datos
   médicos críticos, solo son el input del OCR.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- Unit spec: `inception/units/unit-06-scanner-service.md`
- ADR-019: OCR siempre gpt-4o via OpenRouter
