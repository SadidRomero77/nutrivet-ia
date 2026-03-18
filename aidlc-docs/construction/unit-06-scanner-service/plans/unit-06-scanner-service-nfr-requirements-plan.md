# Plan: NFR Requirements — Unit 06: scanner-service

**Unidad**: unit-06-scanner-service
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del scanner-service

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| ImageValidator (clasificación) | < 500ms | Clasificación rápida pre-OCR |
| Upload imagen a R2 | < 2s p95 | Depende de tamaño de imagen (max 5MB) |
| OCR via gpt-4o vision | < 15s p95 | Llamada LLM con imagen |
| Evaluación semáforo (post-OCR) | < 50ms | Python puro — FoodSafetyChecker + restricciones |
| POST /v1/agent/scan (end-to-end) | < 20s p95 | Upload + OCR + evaluación |

**Alerta**: `ocr_success_rate < 85%` → P2 — investigar calidad de imágenes o prompt OCR.

### Quality Gate G4

```
OCR success rate ≥ 85%
Medido: escaneos con resultado parseable / total escaneos
Alerta si < 85% en ventana de 24h → P2
```

### Seguridad

**LLM siempre gpt-4o para OCR (ADR-019)**:
- No se puede cambiar el modelo OCR por tier de usuario.
- El modelo OCR es fijo: `openai/gpt-4o` via OpenRouter.
- Test: mock que verifica que siempre se llama con `model="openai/gpt-4o"`.

**Imparcialidad de marca (Constitution REGLA 7)**:
- El schema de respuesta `ScanResult` no tiene campo `brand_name`.
- El prompt OCR instruye explícitamente a NO retornar nombre de marca.
- Test: verificar que `ScanResult` no tiene campo brand ni manufacturer.

**R2 Storage**:
- Imágenes almacenadas en R2 — no en el sistema de archivos del contenedor.
- Key: `scans/{scan_id}/{content_hash}` — determinístico.
- Imágenes de scan: retención 30 días en R2, luego purge automático.
- No se expone URL pública de R2 al cliente — solo el resultado del scan.

**Datos del pet en prompts**:
- Solo `pet_id` UUID en trazas — no nombre ni especie en texto plano.
- Las condiciones médicas se usan para evaluar restricciones pero no van al prompt OCR.

### Confiabilidad

- Si ImageValidator rechaza → 422 con mensaje claro (no 500).
- Si R2 upload falla → 503 con retry recomendado.
- Si gpt-4o no puede parsear la imagen → `scan_result = null`, `error = "ocr_failed"`.
- Los checks deterministas (toxicidad, restricciones) nunca fallan — Python puro.

### Mantenibilidad

- Cobertura mínima: **80%** en scanner-service modules.
- Type hints obligatorios. Docstrings en español.
- Ruff + bandit: 0 errores antes de PR.

## Checklist NFR scanner-service

- [ ] `ocr_success_rate ≥ 85%` en test set de 20 imágenes reales
- [ ] gpt-4o siempre usado para OCR (test de mock — verificar model param)
- [ ] `ScanResult` schema no tiene campo brand_name (test de schema)
- [ ] Imagen frontal rechazada → 422 (no 500)
- [ ] Semáforo ROJO para tóxico — test determinístico sin LLM
- [ ] Upload a R2 funcional — imagen almacenada antes de llamar LLM
- [ ] Cobertura ≥ 80%
- [ ] Ruff + bandit sin errores

## Referencias

- Global: `_shared/nfr-requirements.md`
- Unit spec: `inception/units/unit-06-scanner-service.md`
- ADR-019: OCR siempre gpt-4o
- Constitution: REGLA 7 (imparcialidad)
- Quality Gates: G4
