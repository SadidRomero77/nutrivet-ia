# NFR Requirements — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Export Service

### NFR-EXPORT-01: PDF Generation < 10s (p95)
- El pipeline de exportación (generar PDF + upload R2 + presigned URL) debe completar en < 10 segundos en p95.
- WeasyPrint: típicamente 2-5 segundos para un plan de 2-3 páginas.
- Upload R2: 1-2 segundos para 1-3MB con la conexión de Hetzner Ashburn a Cloudflare.

### NFR-EXPORT-02: Disclaimer Siempre Presente
- El PDF generado SIEMPRE contiene el disclaimer en el footer.
- Verificado en test: generar PDF de prueba → comprobar que el texto del disclaimer aparece en el contenido.
- Test: `assert PLAN_DISCLAIMER in extract_text_from_pdf(pdf_bytes)`.

### NFR-EXPORT-03: Solo Planes ACTIVE Exportables
- Intentar exportar plan con status != ACTIVE → HTTP 422.
- Verificado en test parametrizado: PENDING_VET, UNDER_REVIEW, ARCHIVED → 422.

### NFR-EXPORT-04: Presigned URL TTL 1 Hora
- La URL expira en 1 hora (3600 segundos).
- Verificado en test: `assert url_expires_at - created_at == timedelta(hours=1)`.

### NFR-EXPORT-05: PDF en R2 — No en PostgreSQL
- El contenido binario del PDF nunca se almacena en PostgreSQL.
- Solo la clave R2 y la presigned URL se almacenan.
- Verificado: el modelo ORM `ExportResultModel` no tiene campo `LargeBinary`.

### NFR-EXPORT-06: Cobertura de Tests ≥80%
- `pytest --cov=app/application/exports tests/exports/ --cov-fail-under=80`
- Tests obligatorios: export plan ACTIVE, export plan PENDING_VET (422), URL expired (nueva generada), PDF contiene disclaimer, PDF contiene firma vet si aplica.

### NFR-EXPORT-07: WeasyPrint Dependencies en Dockerfile
- El `Dockerfile` debe incluir las dependencias del sistema para WeasyPrint (libcairo2, libpango, etc.).
- Sin estas dependencias → WeasyPrint falla silenciosamente o con error críptico.
- Verificado en CI: build del Docker image + test de generación de PDF.

### NFR-EXPORT-08: 0 XSS en PDFs
- El template usa `autoescape=True` en Jinja2.
- Verificado en test: inyectar `<script>` en una sección del plan → el PDF no ejecuta scripts (PDF no ejecuta JavaScript, pero el HTML intermedio sí puede ser vulnerable).

### NFR-EXPORT-09: Logs sin Nombre de Pet
- Los logs del export service no incluyen el nombre de la mascota.
- Solo se loggea: `plan_id`, `export_id`, `owner_id (UUID)`, `file_size_bytes`, `duration_ms`.

### NFR-EXPORT-10: Exportación Disponible para Todos los Tiers
- El endpoint de export no verifica el tier (no hay restricción por tier).
- Verificado en test: exportar con free tier → 201 (igual que premium).
