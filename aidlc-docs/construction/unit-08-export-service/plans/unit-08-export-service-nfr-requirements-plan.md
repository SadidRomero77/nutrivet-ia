# Plan: NFR Requirements — Unit 08: export-service

**Unidad**: unit-08-export-service
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del export-service

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| PDF generation (WeasyPrint) | < 5s p95 | HTML → PDF con imágenes de silueta BCS |
| R2 upload (nuevo PDF) | < 2s p95 | Depende del tamaño del PDF (~200KB) |
| R2 pre-signed URL generation | < 100ms | Solo firma, sin upload |
| POST /v1/plans/{id}/export (cache hit) | < 200ms | Solo generación de pre-signed URL |
| POST /v1/plans/{id}/export (cache miss) | < 8s p95 | PDF generation + upload + URL |

### Seguridad

**Status check obligatorio**:
- Verificar `plan.status == "ACTIVE"` ANTES de generar PDF.
- Cualquier otro status → 422 con mensaje claro: "Solo se pueden exportar planes activos."

**RBAC para exportación**:
- `owner_id == current_user.user_id` → permitido.
- `assigned_vet_id == current_user.user_id` → permitido.
- Cualquier otro usuario → 403.

**Pre-signed URL TTL**:
- Exactamente 3600 segundos (1 hora).
- No configurable — hardcoded en `ExportPlanUseCase`.
- Test: verificar `expires_in == 3600` en la llamada a `generate_presigned_url`.

**Disclaimer en TODAS las páginas**:
- El template Jinja2 incluye el disclaimer en el `base_layout` — no en secciones individuales.
- Test automatizado: parsear el PDF generado y verificar que el disclaimer aparece en cada página.

**R2 Storage**:
- Key structure: `pdfs/{plan_id}/{content_hash}.pdf`
- Content hash: SHA-256 de los datos del plan en el momento de generación.
- Los PDFs son internos — la URL pre-signed es temporal y de solo lectura.

### Confiabilidad

- Si WeasyPrint falla (ej: librerías del sistema no instaladas) → 503 con mensaje de diagnóstico.
- Si R2 upload falla → retry × 2, luego 503.
- Si plan se modifica después de generar el PDF → nuevo content_hash → nuevo PDF en próxima exportación.

### Mantenibilidad

- Cobertura mínima: **80%** en export-service modules.
- Type hints obligatorios. Docstrings en español.
- Ruff + bandit: 0 errores antes de PR.

## Checklist NFR export-service

- [ ] PDF generation p95 < 5s (test con plan real del golden set)
- [ ] Pre-signed URL TTL exactamente 3600s (verificar en test)
- [ ] Solo status ACTIVE exportable → test plan PENDING_VET → 422
- [ ] Disclaimer en todas las páginas → parsear PDF en test
- [ ] Otro owner → 403 (test de RBAC)
- [ ] Vet asignado puede exportar → test de RBAC
- [ ] Cache: mismo plan → mismo key R2 (no re-upload si sin cambios)
- [ ] Cobertura ≥ 80%
- [ ] Ruff + bandit sin errores

## Referencias

- Global: `_shared/nfr-requirements.md`
- Unit spec: `inception/units/unit-08-export-service.md`
- ADR-020: estructura 5 secciones del plan
- Constitution: REGLA 8 (disclaimer obligatorio en toda vista del plan)
