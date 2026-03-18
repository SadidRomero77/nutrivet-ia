# Plan: NFR Design — Unit 06: scanner-service

**Unidad**: unit-06-scanner-service
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a scanner-service

### Patrón: Image-First Upload (Upload antes de OCR)

**Contexto**: La imagen debe estar en R2 antes de llamar a gpt-4o. Esto permite
reintentar el OCR sin re-subir la imagen y separa responsabilidades.

**Diseño**:
```python
# infrastructure/agent/subgraphs/scanner.py (nodo upload)
async def upload_image_node(state: NutriVetState) -> NutriVetState:
    """Sube imagen a R2 ANTES de llamar al OCR. Falla rápido si R2 no disponible."""
    scan_id = str(uuid4())
    content_hash = hashlib.sha256(state["image_bytes"]).hexdigest()[:16]
    r2_key = f"scans/{scan_id}/{content_hash}.jpg"

    await r2_client.upload(
        key=r2_key,
        data=state["image_bytes"],
        content_type="image/jpeg"
    )
    return {**state, "scan_id": scan_id, "r2_key": r2_key}
```

### Patrón: Validation-Before-OCR (Evitar gasto de cuota gpt-4o)

**Contexto**: gpt-4o vision es el LLM más caro del sistema. Validar la imagen ANTES
de llamar al OCR evita desperdiciar quota en imágenes de logos o marcas.

**Diseño**:
```
Nodo 1: image_validator → clasifica imagen
  ↓ RECHAZADA → error 422 (no llega al OCR)
  ↓ ACEPTADA → upload_image → ocr_node
```

**Clasificación de la imagen** (nodo `image_validator`):
- Opción A: Usar un LLM pequeño (llama) para clasificar rápido y barato.
- Opción B: Heurística basada en aspect ratio y detección de tablas.
- Implementar Opción A inicialmente — más confiable.

### Patrón: Deterministic-Post-OCR (Safety checks después del OCR)

**Contexto**: Los checks de seguridad (toxicidad, restricciones) son determinísticos
y no dependen del LLM — corren DESPUÉS del OCR sobre los ingredientes extraídos.

**Diseño**:
```python
# infrastructure/agent/nodes/nutritional_evaluator.py
def determine_semaphore(
    ingredients: list[str],
    nutritional_profile: NutritionalProfile,
    pet_profile: dict
) -> SemaphoreResult:
    """Evaluación determinística. Sin LLM. Sin red. < 50ms."""

    # 1. Tóxicos (BLOQUEANTE)
    for ing in ingredients:
        if food_safety_checker.check_ingredient(ing, pet_profile["species"]):
            return SemaphoreResult(color="rojo", reason="toxic", ingredient=ing)

    # 2. Restricciones médicas
    conditions = pet_profile.get("medical_conditions", [])
    for ing in ingredients:
        violations = restriction_engine.validate(ing, conditions)
        if violations:
            return SemaphoreResult(color="rojo", reason="restricted", ingredient=ing)

    # 3. Alergias
    allergies = pet_profile.get("allergies", [])
    for ing in ingredients:
        if ing.lower() in [a.lower() for a in allergies]:
            return SemaphoreResult(color="amarillo", reason="allergy", ingredient=ing)

    # 4. Balance nutricional (comparar vs NRC targets)
    if not nutritional_profile.meets_nrc_targets(pet_profile):
        return SemaphoreResult(color="amarillo", reason="nutritional_mismatch")

    return SemaphoreResult(color="verde")
```

### Patrón: Brand Name Stripping

**Contexto**: El resultado del scanner nunca debe incluir nombre de marca (Constitution REGLA 7).

**Diseño**: El schema `ScanResult` simplemente no tiene campo `brand_name`.
Adicionalmente, el prompt OCR instruye a no retornar el nombre:

```python
OCR_SYSTEM_PROMPT = """
Eres un analizador de etiquetas nutricionales de alimentos para mascotas.
Extrae ÚNICAMENTE los valores nutricionales y la lista de ingredientes.
NO retornes nombre de marca, fabricante, ni información de contacto.
Retorna en formato JSON con campos: protein_pct, fat_pct, moisture_pct,
fiber_pct, kcal_per_100g, ingredients (lista de strings).
"""
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `nodes/image_validator.py` | 90% | Unit tests — tipos válidos e inválidos |
| `nodes/nutritional_evaluator.py` | 100% | Unit tests — semáforo determinístico |
| `subgraphs/scanner.py` | 80% | Integration tests |
| `infrastructure/db/label_scan_repository.py` | 80% | Integration tests |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- Constitution: REGLA 7 (imparcialidad — solo tabla nutricional)
- ADR-019: OCR siempre gpt-4o
