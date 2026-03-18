# Plan: Code Generation — Unit 06: scanner-service

**Unidad**: unit-06-scanner-service
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Reemplazar el stub del scanner en el orquestador LangGraph con la implementación
completa: ImageValidator, pipeline OCR (gpt-4o), evaluación semáforo determinística
y persistencia en label_scans.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.

---

## Pasos de Implementación

### Paso 1 — Estructura de Archivos

- [ ] `backend/infrastructure/agent/nodes/image_validator.py` — nodo clasificador
- [ ] `backend/infrastructure/agent/nodes/nutritional_evaluator.py` — semáforo determinístico
- [ ] `backend/infrastructure/agent/subgraphs/scanner.py` — REEMPLAZA stub de unit-05
- [ ] `backend/infrastructure/db/label_scan_repository.py`
- [ ] `backend/presentation/schemas/scan_schemas.py` — ScanResult (sin brand_name)
- [ ] `tests/scanner/test_image_validator.py` (vacío)
- [ ] `tests/scanner/test_nutritional_evaluator.py` (vacío)
- [ ] `tests/scanner/test_scanner_subgraph.py` (vacío)

### Paso 2 — Tests RED: ImageValidator

- [ ] Escribir `tests/scanner/test_image_validator.py`:
  - `test_imagen_frontal_rechazada` — imagen de logo → 422 con mensaje claro
  - `test_empaque_frontal_rechazado` — imagen de frente del producto → rechazada
  - `test_tabla_nutricional_aceptada` — imagen de tabla nutricional → aceptada
  - `test_ingredientes_aceptados` — imagen de lista de ingredientes → aceptada
  - `test_imagen_ambigua_rechazada` — imagen no reconocible → rechazada con "unknown"
  - `test_mensaje_rechazo_incluye_instruccion`
- [ ] Verificar que todos FALLAN (RED)

### Paso 3 — Tests RED: Nutritional Evaluator (Semáforo)

- [ ] Escribir `tests/scanner/test_nutritional_evaluator.py`:
  - `test_toxico_semaforo_rojo` — cebolla en ingredientes para perro → ROJO
  - `test_restringido_diabetico_rojo` — ingrediente restringido + diabético → ROJO
  - `test_alergia_amarillo` — ingrediente en alergias del pet → AMARILLO
  - `test_desequilibrio_nutricional_amarillo`
  - `test_adecuado_verde` — sin tóxicos, restricciones, ni alergias → VERDE
  - `test_resultado_sin_marca` — ScanResult no tiene campo brand_name
  - `test_semaforo_deterministico` — mismo input → mismo output siempre
- [ ] Verificar que todos FALLAN (RED)

### Paso 4 — Tests RED: Scanner Subgraph

- [ ] Escribir `tests/scanner/test_scanner_subgraph.py`:
  - `test_siempre_usa_gpt4o` — mock verifica que model="openai/gpt-4o" siempre
  - `test_imagen_sube_a_r2_antes_de_ocr` — upload ocurre antes de llamar LLM
  - `test_ocr_fallido_retorna_error_controlado` — timeout OCR → error manejado
  - `test_flujo_completo_tabla_nutricional_verde`
  - `test_flujo_completo_toxico_rojo`
  - `test_disclaimer_en_resultado`
- [ ] Verificar que todos FALLAN (RED)

### Paso 5 — GREEN: ImageValidator Node

- [ ] Implementar `image_validator.py`:
  - Clasificador de tipo de imagen (LLM mini o heurística)
  - Retorna `image_type: "nutrition_table" | "ingredient_list" | "rejected"`
  - Si `rejected` → populate `state["error"]` con mensaje de instrucción
  - Wiring: si rejected → END del subgrafo con 422

### Paso 6 — GREEN: NutritionalEvaluator Node

- [ ] Implementar `nutritional_evaluator.py`:
  - `determine_semaphore(ingredients, nutritional_profile, pet_profile)` — puro, sin LLM
  - Orden: tóxicos → restricciones → alergias → balance nutricional → verde
  - Retorna `SemaphoreResult` con color, issues, recomendación
- [ ] Implementar `ScanResult` schema (Pydantic, SIN campo brand_name)
- [ ] Verificar que todos los tests del semáforo PASAN

### Paso 7 — GREEN: ScannerSubgraph (5 Nodos)

- [ ] Implementar `scanner.py` (reemplaza stub de unit-05):
  - Nodo 1: `image_validator` — clasifica imagen
  - Nodo 2: `upload_to_r2` — sube a Cloudflare R2
  - Nodo 3: `ocr_with_gpt4o` — extrae valores nutricionales e ingredientes
  - Nodo 4: `evaluate_nutrition` — semáforo determinístico
  - Nodo 5: `persist_scan` — guarda en label_scans + agent_trace
- [ ] LangGraph wiring: `image_validator → conditional: rejected? → END : upload_to_r2 → ...`

### Paso 8 — Alembic Migration

- [ ] `alembic revision -m "013_label_scans"` → tabla label_scans + índice
- [ ] Revisar migración generada
- [ ] Confirmar con Sadid antes de `alembic upgrade head` en staging

### Paso 9 — FastAPI Endpoint

- [ ] Implementar `POST /v1/agent/scan` en `presentation/routers/agent_router.py`:
  ```python
  @router.post("/v1/agent/scan")
  async def scan_label(
      pet_id: UUID,
      image: UploadFile = File(...),
      current_user: User = Depends(get_current_user)
  ):
      """Escanea etiqueta nutricional. Solo acepta tabla nutricional o lista de ingredientes."""
      # multipart/form-data
  ```

### Paso 10 — Cobertura y Calidad

- [ ] `pytest --cov=backend/infrastructure/agent/subgraphs/scanner tests/scanner/ --cov-fail-under=80`
- [ ] `pytest --cov=backend/infrastructure/agent/nodes/nutritional_evaluator tests/scanner/ --cov-fail-under=100`
- [ ] `ruff check backend/` → 0 errores
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM
- [ ] Test manual: verificar que gpt-4o siempre usado (no cambiar por tier)

---

## Criterios de Done

- [ ] Stub de unit-05 reemplazado por implementación completa
- [ ] Imagen frontal (logo) rechazada con mensaje claro
- [ ] gpt-4o siempre usado para OCR (independiente del tier)
- [ ] Semáforo determinístico: tóxicos/restricciones → ROJO, alergias → AMARILLO, ok → VERDE
- [ ] Resultado NUNCA incluye nombre de marca (verificado en schema)
- [ ] Disclaimer presente en todo resultado
- [ ] `ocr_success_rate ≥ 85%` en test set de imágenes reales
- [ ] Cobertura ≥ 80%, ruff + bandit sin errores

## Tiempo Estimado

4-5 días (TDD + R2 integration + OCR testing con imágenes reales)

## Dependencias

- Unit 01: FoodSafetyChecker, MedicalRestrictionEngine (para semáforo)
- Unit 02: JWT middleware, RBAC
- Unit 03: PetProfile (para evaluar restricciones y alergias)
- Unit 04: OpenRouterClient (reutilizado para gpt-4o)
- Unit 05: NutriVetState, scanner stub (a reemplazar)

## Referencias

- Unit spec: `inception/units/unit-06-scanner-service.md`
- ADR-019: OCR siempre gpt-4o
- Constitution: REGLA 7 (imparcialidad)
- Quality Gates: G4 (OCR ≥ 85%)
