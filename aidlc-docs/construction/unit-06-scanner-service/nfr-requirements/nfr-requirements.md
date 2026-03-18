# NFR Requirements — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Scanner Service

### NFR-SCAN-01: OCR Success Rate ≥85% (Quality Gate G4)
- El porcentaje de escaneos que producen un `NutritionalProfile` válido debe ser ≥85%.
- Medido sobre imágenes de entrenamiento con tablas nutricionales reales de LATAM.
- Alerta P2 si cae por debajo de 85% en producción.

### NFR-SCAN-02: 0% Tóxicos No Detectados
- Si la lista de ingredientes contiene un ingrediente de TOXIC_DOGS/TOXIC_CATS, el semáforo DEBE ser RED.
- Zero tolerancia a falsos negativos en detección de tóxicos.
- Verificado en test: 20 imágenes con ingrediente tóxico → 100% RED.

### NFR-SCAN-03: Solo gpt-4o para OCR
- El modelo OCR es `openai/gpt-4o` siempre. Nunca degradar.
- Verificado en test: el `OCR_MODEL` constant == "openai/gpt-4o".
- El tier del usuario NO influye en el modelo de OCR.

### NFR-SCAN-04: Imagen Nunca en PostgreSQL
- El campo `condiciones_medicas_encrypted` en tabla `pets` no es el único dato sensible.
- Las imágenes de escaneo NUNCA se almacenan como BYTEA en PostgreSQL.
- Solo la clave R2 se almacena en DB.
- Verificado: el modelo ORM `LabelScanModel` no tiene campo de tipo `LargeBinary`.

### NFR-SCAN-05: Semáforo Determinista
- El color del semáforo es determinado por código, no por LLM.
- Verificado en test unitario: `calculate_semaphore([finding_critical]) == RED` sin llamada a LLM.

### NFR-SCAN-06: Tiempo de Procesamiento < 30s
- El pipeline completo (upload + validate + OCR + evaluate + persist) debe completar en < 30s.
- El bottleneck es gpt-4o vision (típicamente 5-15s).
- Alerta si el procesamiento p95 supera 30s.

### NFR-SCAN-07: Imagen Rechazada con Explicación Clara
- Si `ImageType = "invalid"` → HTTP 422 con mensaje: "La imagen no muestra una tabla nutricional ni una lista de ingredientes. Por favor, sube solo la tabla nutricional o la lista de ingredientes del producto."
- No se cobra el scan fallido al usuario.

### NFR-SCAN-08: Cobertura de Tests ≥80%
- `pytest --cov=app/application/scanner tests/scanner/ --cov-fail-under=80`
- Tests obligatorios: imagen válida (nutrition_table), imagen válida (ingredients_list), imagen inválida (rejected), ingrediente tóxico (RED), restricción médica violada (RED), limpio (GREEN).

### NFR-SCAN-09: Retención de Imágenes 90 días
- Las imágenes en R2 se eliminan automáticamente a los 90 días.
- Job ARQ cron mensual: `purge_old_scan_images()`.
- Los datos de evaluación en PostgreSQL se retienen indefinidamente (no contienen imagen).
