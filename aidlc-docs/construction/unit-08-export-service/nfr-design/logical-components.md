# Logical Components — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Export Service

### ExportPlanUseCase
**Responsabilidad**: Orquestar la exportación de un plan ACTIVE a PDF y upload a R2.
**Capa**: application/exports/
**Dependencias**: PlanRepositoryPort, PetRepositoryPort, VetRepositoryPort, PDFGeneratorPort, R2ExportPort, ExportRepositoryPort
**Métodos**:
```
export_plan(plan_id, owner_id) → ExportResult
get_download_url(export_id, owner_id) → str (presigned URL renovada)
list_exports_by_plan(plan_id, owner_id) → list[ExportResult]
```

### PDFGenerator (WeasyPrint)
**Responsabilidad**: Renderizar HTML/CSS a PDF bytes usando WeasyPrint.
**Capa**: infrastructure/exports/
**Implementa**: PDFGeneratorPort
**Input**: PDFContent (structured data)
**Output**: `bytes` (contenido del PDF)
**Regla crítica**: El disclaimer SIEMPRE se incluye en el footer — hardcoded en el template.

### Jinja2Template
**Responsabilidad**: Template HTML del plan nutricional.
**Capa**: infrastructure/exports/templates/
**Archivos**: `plan.html`, `styles.css`
**Regla**: `autoescape=True` para prevenir XSS (aunque el contenido es interno, buena práctica).

### R2ExportClient
**Responsabilidad**: Upload del PDF a Cloudflare R2 y generación de presigned URLs.
**Capa**: infrastructure/exports/
**Implementa**: R2ExportPort

### PostgreSQLExportRepository
**Responsabilidad**: Persistencia de ExportResult en PostgreSQL.
**Capa**: infrastructure/exports/
**Implementa**: ExportRepositoryPort

### ExportRouter
**Responsabilidad**: Endpoints HTTP del export service.
**Capa**: presentation/exports/
**Endpoints**:
```
POST /plans/{plan_id}/export          → 201 ExportResult
GET  /exports/{export_id}/url         → 200 { download_url, expires_at }
GET  /plans/{plan_id}/exports         → 200 list[ExportResult]
```

## Diagrama de Componentes

```
ExportRouter (presentation)
    ↓
ExportPlanUseCase (application)
    ├── PlanRepositoryPort ←── PostgreSQLPlanRepository
    ├── PetRepositoryPort  ←── PostgreSQLPetRepository (nombre del pet)
    ├── VetRepositoryPort  ←── PostgreSQLVetRepository (firma del vet)
    ├── PDFGeneratorPort   ←── PDFGenerator (WeasyPrint + Jinja2)
    │                              ↓ render HTML
    │                         → PDF bytes
    ├── R2ExportPort       ←── R2ExportClient (boto3)
    │                              ↓ upload PDF bytes
    │                         → R2 key + presigned URL
    └── ExportRepositoryPort ←── PostgreSQLExportRepository
```

## Manejo de Errores

| Error | HTTP Status | Acción |
|-------|-------------|--------|
| Plan no ACTIVE | 422 | "Solo planes activos pueden exportarse" |
| Plan no existe | 404 | "Plan no encontrado" |
| No es el owner | 403 | "Acceso denegado" |
| WeasyPrint falla | 500 | Log + "Error generando PDF, intenta nuevamente" |
| R2 upload falla | 500 | Retry × 2, luego error 500 |
| Presigned URL expirada | 200 | Generar nueva URL automáticamente |
