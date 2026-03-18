# Plan: Code Generation — Unit 08: export-service

**Unidad**: unit-08-export-service
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar el servicio de exportación de planes a PDF: WeasyPrint server-side,
5 secciones (ADR-020), upload a Cloudflare R2 y pre-signed URL con TTL 1 hora.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.

---

## Pasos de Implementación

### Paso 1 — Estructura de Carpetas

- [ ] `backend/application/interfaces/pdf_generator.py` — IPDFGenerator ABC
- [ ] `backend/application/interfaces/storage_client.py` — IStorageClient ABC
- [ ] `backend/application/use_cases/export_plan_use_case.py`
- [ ] `backend/infrastructure/pdf/pdf_generator.py` — WeasyPrint implementation
- [ ] `backend/infrastructure/pdf/templates/plan_template.html` — Jinja2 (5 secciones)
- [ ] `backend/infrastructure/pdf/templates/base_layout.html` — footer con disclaimer
- [ ] `backend/infrastructure/pdf/templates/assets/style.css`
- [ ] `backend/infrastructure/storage/r2_client.py` — boto3 S3-compatible
- [ ] `backend/presentation/routers/export_router.py`
- [ ] `backend/presentation/schemas/export_schemas.py`
- [ ] `tests/export/test_export_plan_use_case.py` (vacío)
- [ ] `tests/export/test_pdf_generator.py` (vacío)
- [ ] `tests/export/test_r2_client.py` (vacío)

### Paso 2 — Tests RED: ExportPlanUseCase

- [ ] Escribir `tests/export/test_export_plan_use_case.py`:
  - `test_exportar_plan_active_retorna_url` — plan ACTIVE → URL pre-signed retornada
  - `test_exportar_pending_vet_falla` — plan PENDING_VET → 422
  - `test_exportar_under_review_falla` — plan UNDER_REVIEW → 422
  - `test_exportar_archived_falla` — plan ARCHIVED → 422
  - `test_owner_puede_exportar` — owner_id == user_id → permitido
  - `test_vet_puede_exportar_su_paciente` — assigned_vet_id == user_id → permitido
  - `test_otro_owner_no_autorizado` → 403
  - `test_mismo_plan_cache_hit` — segunda exportación usa R2 existente (no re-genera)
  - `test_presigned_url_expira_1h` — ExpiresIn == 3600
- [ ] Verificar que todos FALLAN (RED)

### Paso 3 — Tests RED: PDFGenerator

- [ ] Escribir `tests/export/test_pdf_generator.py`:
  - `test_pdf_generado_es_bytes` — retorna bytes no vacíos
  - `test_pdf_incluye_disclaimer` — parsear PDF y verificar texto del disclaimer
  - `test_pdf_incluye_sustitutos` — sección 5 presente con sustitutos
  - `test_pdf_protocolo_transicion_si_flag` — sección 4 solo si `has_transition_protocol=True`
  - `test_pdf_sin_protocolo_si_no_flag` — sección 4 ausente si `has_transition_protocol=False`
  - `test_pdf_incluye_nombre_vet_si_aprobado` — portada con "Aprobado por: [vet_name]"
  - `test_disclaimer_en_todas_las_paginas` — verificar footer en múltiples páginas
- [ ] Verificar que todos FALLAN (RED)

### Paso 4 — Tests RED: R2StorageClient

- [ ] Escribir `tests/export/test_r2_client.py`:
  - `test_upload_retorna_r2_key`
  - `test_presigned_url_ttl_es_exactamente_3600` — verificar ExpiresIn=3600
  - `test_exists_true_si_objeto_en_r2`
  - `test_exists_false_si_objeto_no_en_r2`
  - `test_upload_falla_retry_x2` — mock R2 error → retry
- [ ] Verificar que todos FALLAN (RED)

### Paso 5 — GREEN: Interfaces

- [ ] Implementar `IPDFGenerator` ABC:
  - `generate(plan_data: dict) -> bytes`
- [ ] Implementar `IStorageClient` ABC:
  - `upload(key: str, data: bytes, content_type: str) -> str`
  - `exists(key: str) -> bool`
  - `generate_presigned_url(key: str) -> str`

### Paso 6 — GREEN: ExportPlanUseCase

- [ ] Implementar `ExportPlanUseCase`:
  - `export(plan_id, user_id)` — status check + RBAC + hash + cache check + generate/upload + URL
  - `compute_content_hash(plan_data)` — SHA-256 determinístico
  - TTL hardcoded 3600s (no configurable)
- [ ] Verificar que tests del use case PASAN

### Paso 7 — GREEN: PDFGenerator (WeasyPrint)

- [ ] Crear `base_layout.html` con `@bottom-center` CSS para disclaimer en todas las páginas
- [ ] Crear `plan_template.html` con 5 secciones (Jinja2 extends base_layout)
- [ ] Implementar `PDFGenerator.generate(plan_data)`:
  - Renderiza Jinja2 template con datos del plan
  - Llama `HTML(string=html).write_pdf()`
  - Retorna bytes
- [ ] Test manual: generar PDF del golden case Sally y verificar visualmente

### Paso 8 — GREEN: R2StorageClient (boto3)

- [ ] Implementar `R2StorageClient`:
  - `upload(key, data, content_type)` — `put_object` con retry × 2
  - `exists(key)` — `head_object` con try/except
  - `generate_presigned_url(key)` — TTL hardcoded 3600s
- [ ] Verificar que tests del R2 client PASAN con mocks de boto3

### Paso 9 — FastAPI Endpoint

- [ ] Implementar `POST /v1/plans/{plan_id}/export` en `export_router.py`:
  ```python
  @router.post("/v1/plans/{plan_id}/export")
  async def export_plan(
      plan_id: UUID,
      current_user: User = Depends(get_current_user)
  ) -> ExportResponse:
      """Exporta plan a PDF. Solo planes ACTIVE. Retorna URL pre-signed (1h)."""
      result = await export_use_case.export(plan_id, current_user.user_id)
      return ExportResponse(url=result.url, expires_at=result.expires_at)
  ```
- [ ] Definir `ExportResponse` schema (Pydantic): `url: str, expires_at: datetime`

### Paso 10 — Cobertura y Calidad

- [ ] `pytest --cov=backend/application/use_cases/export_plan_use_case tests/export/ --cov-fail-under=80`
- [ ] `ruff check backend/` → 0 errores
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM
- [ ] Verificar disclaimer en TODAS las páginas del PDF (pytest con pdfminer o pypdf)
- [ ] Test manual con plan real del golden set

---

## Criterios de Done

- [ ] Disclaimer en todas las páginas del PDF (verificado programáticamente)
- [ ] Solo planes ACTIVE exportables (422 para otros estados)
- [ ] Pre-signed URL TTL exactamente 1 hora (3600s)
- [ ] Cache funcional: mismo plan → mismo PDF en R2 (no re-genera)
- [ ] Vet puede exportar planes de sus pacientes
- [ ] Sección 4 (protocolo de transición) solo si `has_transition_protocol=True`
- [ ] Cobertura ≥ 80%, ruff + bandit sin errores

## Tiempo Estimado

3-4 días (TDD + WeasyPrint template + R2 integration)

## Dependencias

- Unit 02: JWT middleware, RBAC
- Unit 04: plans table, plan_sections data
- Unit 06: R2StorageClient (puede reutilizarse — mismo cliente, diferente key prefix)

## Notas de Implementación

- Instalar dependencias del sistema en Dockerfile: `libpango1.0-0 libcairo2 libgdk-pixbuf2.0-0`
- WeasyPrint requiere Python packages: `weasyprint jinja2 pypdf` (pypdf para tests de verificación)
- Verificar que WeasyPrint funciona en el contenedor Docker antes de escribir tests

## Referencias

- Unit spec: `inception/units/unit-08-export-service.md`
- ADR-020: estructura 5 secciones del plan
- Constitution: REGLA 8 (disclaimer obligatorio)
