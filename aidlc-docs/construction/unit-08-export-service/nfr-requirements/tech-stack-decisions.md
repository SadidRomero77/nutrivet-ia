# Tech Stack Decisions — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Export Service

### WeasyPrint para Generación de PDF
**Decisión**: `weasyprint==62.x` para renderizar HTML/CSS a PDF en el servidor.
**Razón**: WeasyPrint produce PDFs de alta calidad desde HTML/CSS — el mismo stack web que los desarrolladores ya conocen. Soporte para estilos complejos, emojis, tablas, y RTL. Activamente mantenido.
**Trade-off**: Requiere librerías del sistema (libcairo, libpango) → Dockerfile más pesado (+50MB).
**Alternativas rechazadas**:
- `reportlab` (API de bajo nivel Python, curva de aprendizaje alta, menos flexible para diseño)
- `fpdf2` (más simple pero limitado para diseño complejo)
- `pdfrw` (manipulación de PDFs existentes — no generación desde cero)
- Puppeteer/headless Chrome (demasiado pesado para el CPX31, requiere Node.js)

### Jinja2 para Templates HTML
**Decisión**: `Jinja2==3.1.x` para renderizar el template HTML del plan.
**Razón**: Template engine estándar de Python. Autoescape nativo. Separación clara entre datos y presentación. Ya es dependencia de FastAPI/Starlette.

### boto3 para R2 (mismo que scanner)
**Decisión**: `boto3==1.34.x` reutilizado del scanner service.
**Razón**: Consistencia. R2 es S3-compatible. No hay razón para un cliente diferente.

### share_plus (Flutter) para Compartición
**Decisión**: `share_plus` package de Flutter para el share sheet nativo.
**Razón**: Accede al share sheet nativo del OS (iOS y Android). Un solo paquete para ambas plataformas. Soporta compartir URLs, texto, y archivos.
**Uso**:
```dart
await Share.shareUri(Uri.parse(downloadUrl));
// Abre el share sheet nativo con la URL del PDF
```

### PDF Generado Sincrónicamente (No en ARQ)
**Decisión**: La generación del PDF ocurre sincrónicamente en el request (no en job async).
**Razón**: WeasyPrint genera PDFs en 2-5 segundos. Este tiempo es aceptable para un export explícito (el usuario espera activamente). Un job async añadiría complejidad sin beneficio real en este caso.
**Trade-off**: El worker de Uvicorn está bloqueado durante el render (CPU-bound). Mitigación: aumentar workers si hay muchos exports concurrentes.

### Dependencias del Export Service

```
weasyprint==62.3      # PDF server-side
Jinja2==3.1.3         # HTML templates (ya en FastAPI deps)
boto3==1.34.x         # R2 client (compartido con scanner)
sqlalchemy[asyncio]   # persistence
```

### Variables de Entorno Específicas del Export

```env
R2_EXPORTS_BUCKET=nutrivet-exports
PDF_PRESIGNED_URL_TTL_SECONDS=3600
# R2 credentials compartidas con scanner service
```
