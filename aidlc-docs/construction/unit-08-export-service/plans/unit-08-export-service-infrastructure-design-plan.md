# Plan: Infrastructure Design — Unit 08: export-service

**Unidad**: unit-08-export-service
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| ExportRouter (FastAPI) | Contenedor Docker — FastAPI + Uvicorn en Hetzner CPX31 |
| ExportPlanUseCase | `application/use_cases/export_plan_use_case.py` |
| PDFGenerator (WeasyPrint) | `infrastructure/pdf/pdf_generator.py` |
| R2StorageClient | `infrastructure/storage/r2_client.py` |
| HTML Template | `infrastructure/pdf/templates/plan_template.html` (Jinja2) |

**WeasyPrint**: corre in-process en el contenedor FastAPI — no como servicio separado.
La generación de PDF es síncrona (< 5s) — no requiere ARQ worker.

### PDF Generation — WeasyPrint

**Dependencias del sistema** (agregar al Dockerfile):
```dockerfile
FROM python:3.11-slim

# Dependencias del sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
RUN pip install weasyprint==62.3 jinja2==3.1.4
```

**Template Jinja2**:
```
infrastructure/pdf/templates/
  ├── plan_template.html      — template principal (5 secciones)
  ├── base_layout.html        — base con disclaimer en footer (todas las páginas)
  └── assets/
      ├── style.css           — estilos del PDF
      └── bcs_silhouettes/    — imágenes de silueta BCS (1-9)
```

**Generación**:
```python
# infrastructure/pdf/pdf_generator.py
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader

async def generate_pdf(plan_data: dict) -> bytes:
    """Genera PDF desde template Jinja2 + datos del plan. Retorna bytes."""
    env = Environment(loader=FileSystemLoader("infrastructure/pdf/templates"))
    template = env.get_template("plan_template.html")
    html_content = template.render(**plan_data)
    return HTML(string=html_content).write_pdf()
```

### Storage — Cloudflare R2

**Bucket**: `nutrivet-storage-{env}` (compartido con scanner service)

**Key structure**:
```
pdfs/{plan_id}/{content_hash}.pdf
```

**Pre-signed URL** (boto3 S3-compatible):
```python
# infrastructure/storage/r2_client.py
import boto3

def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Genera URL pre-signed con TTL 1 hora. ExpiresIn hardcoded a 3600."""
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT_URL"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
    )
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": os.environ["R2_BUCKET_NAME"], "Key": key},
        ExpiresIn=3600  # Hardcoded — no configurable
    )
```

**Retención de PDFs**: Sin lifecycle rule — los PDFs se retienen indefinidamente.
Son el resultado final del servicio y pueden ser accedidos múltiples veces.

### Variables de Entorno Requeridas

```bash
# R2 — compartido con unit-06
R2_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<R2 access key>
R2_SECRET_ACCESS_KEY=<R2 secret key>
R2_BUCKET_NAME=nutrivet-storage-prod

# Database — ya configurado
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/nutrivet
```

### No Requiere Alembic Migration

El export-service no crea tablas propias. Usa la tabla `plans` (creada en unit-04)
para verificar status y obtener datos del plan. El `r2_key` del PDF puede almacenarse
en la tabla `plans` como campo adicional si se quiere cachear.

**Opción**: agregar columna `pdf_r2_key VARCHAR(500)` a la tabla `plans` en una migration
adicional en unit-04 o unit-08 — decidir con Sadid.

## Notas Arquitecturales

1. **WeasyPrint en-process vs servicio dedicado**: Para el volumen inicial del piloto
   (< 100 exports/día), WeasyPrint en-process es suficiente. Si escala, mover a
   servicio dedicado con ARQ worker.

2. **R2StorageClient compartido**: El mismo `R2StorageClient` lo usa el scanner
   (unit-06) para imágenes y el export (unit-08) para PDFs. Mismo bucket, diferentes
   prefijos de key (`scans/` vs `pdfs/`).

3. **Content-hash como cache key**: `SHA-256(json.dumps(plan_data, sort_keys=True))[:16]`
   garantiza que el mismo plan genera la misma key en R2, evitando re-generación innecesaria.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- Unit spec: `inception/units/unit-08-export-service.md`
- ADR-020: estructura 5 secciones del plan
