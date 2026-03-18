# Infrastructure Design — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura del Export Service

### PDFGenerator (WeasyPrint + Jinja2)

```python
# infrastructure/exports/pdf_generator.py
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

class PDFGenerator:
    """Genera PDF del plan nutricional desde template HTML/CSS."""

    def __init__(self):
        self._jinja = Environment(
            loader=FileSystemLoader("templates/pdf/"),
            autoescape=True,  # prevenir XSS en templates
        )

    def generate(self, pdf_content: PDFContent) -> bytes:
        """Generar PDF como bytes desde el contenido del plan."""
        template = self._jinja.get_template("plan.html")
        html_content = template.render(
            pet_name=pdf_content.pet_name,
            generated_date=pdf_content.generated_date,
            sections=pdf_content.sections,
            rer_kcal=pdf_content.rer_kcal,
            der_kcal=pdf_content.der_kcal,
            vet_signature=pdf_content.vet_signature,
            disclaimer=pdf_content.disclaimer,  # inmutable
        )
        return HTML(string=html_content).write_pdf(
            stylesheets=[CSS(filename="templates/pdf/styles.css")]
        )
```

### Template HTML del Plan (Jinja2)

```html
<!-- templates/pdf/plan.html -->
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Plan Nutricional NutriVet.IA</title></head>
<body>
  <header>
    <img src="static/logo.png" alt="NutriVet.IA" class="logo">
    <h1>Plan Nutricional</h1>
    <p class="pet-name">Para: {{ pet_name }}</p>
    <p class="date">Generado: {{ generated_date }}</p>
    <p class="nrc">RER: {{ rer_kcal }} kcal | DER: {{ der_kcal }} kcal/día</p>
  </header>

  {% for section in sections %}
  <section>
    <h2>{{ loop.index }}. {{ section.title }}</h2>
    <div class="content">{{ section.content }}</div>
  </section>
  {% endfor %}

  {% if vet_signature %}
  <section class="vet-signature">
    <h2>Revisado y aprobado por:</h2>
    <p>{{ vet_signature.vet_name }}</p>
    <p>{{ vet_signature.clinica or "" }}</p>
    <p>Fecha de firma: {{ vet_signature.signed_at }}</p>
  </section>
  {% endif %}

  <footer>
    <p class="disclaimer">{{ disclaimer }}</p>
  </footer>
</body>
</html>
```

### R2ExportClient

```python
# infrastructure/exports/r2_export_client.py
class R2ExportClient:
    """Cliente R2 para PDFs exportados."""

    async def upload_pdf(self, r2_key: str, pdf_bytes: bytes) -> int:
        """Subir PDF a R2. Retorna tamaño en bytes."""
        self._client.put_object(
            Bucket=settings.R2_EXPORTS_BUCKET,
            Key=r2_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
            ContentDisposition=f'attachment; filename="plan-nutrivet.pdf"',
        )
        return len(pdf_bytes)

    def generate_presigned_url(self, r2_key: str) -> tuple[str, datetime]:
        """Generar presigned URL con TTL 1 hora."""
        url = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.R2_EXPORTS_BUCKET, "Key": r2_key},
            ExpiresIn=3600,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return url, expires_at
```

## Dependencias del Export Service

```
weasyprint==62.x      # PDF generation server-side
Jinja2==3.1.x         # HTML templates
boto3==1.34.x         # R2/S3 client
# Dependencias del sistema: libcairo2, libpango (instaladas en Dockerfile)
```
