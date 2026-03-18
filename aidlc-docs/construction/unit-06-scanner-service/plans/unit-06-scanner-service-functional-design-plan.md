# Plan: Functional Design — Unit 06: scanner-service

**Unidad**: unit-06-scanner-service
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del scanner de etiquetas nutricionales: validación de imagen,
pipeline OCR via OpenRouter gpt-4o vision, evaluación semáforo y regla crítica de
imparcialidad (sin marca en resultado).

## Regla Crítica de Imparcialidad (Constitution REGLA 7)

```
NUNCA aceptar imagen de marca, logo o empaque frontal.
SOLO aceptar: tabla nutricional O lista de ingredientes.

NUNCA incluir nombre de marca en el resultado.
El schema de respuesta NO tiene campo brand_name.
```

Esta regla garantiza imparcialidad hacia marcas y evita responsabilidad legal.

## ImageValidator — Primer Nodo (Pre-OCR)

**Propósito**: Rechazar imágenes inválidas ANTES de llamar a gpt-4o (cuota costosa).

```python
ACCEPTED_IMAGE_TYPES = {"nutrition_table", "ingredient_list"}
REJECTED_IMAGE_TYPES = {"brand_logo", "front_package", "unknown"}

def validate_image(state: NutriVetState) -> NutriVetState:
    """
    Clasifica la imagen usando un LLM o regla heurística.
    Si no es tabla nutricional o lista de ingredientes → rechazar con 422.
    """
    # Clasificación de la imagen — puede usar mini-LLM o heurística visual
    # Si image_type en REJECTED_IMAGE_TYPES → error con mensaje claro al usuario
```

**Mensaje de rechazo** (si imagen inválida):
```
"Solo puedo analizar la tabla nutricional o la lista de ingredientes del producto.
Por favor, fotografía esa sección específica del empaque."
```

## Pipeline OCR — OpenRouter gpt-4o Vision

```
Todos los tiers usan gpt-4o para OCR (ADR-019 — sin excepción):
  Free tier   → gpt-4o vision (OCR)
  Básico tier → gpt-4o vision (OCR)
  Premium tier → gpt-4o vision (OCR)
  Vet tier    → gpt-4o vision (OCR)

Flujo:
  1. Upload imagen a R2 (key: scans/{scan_id}/{hash})
  2. Pasar r2_key + prompt al OCR LLM
  3. Extraer: proteínas, grasas, carbohidratos, humedad, fibra, calorías, ingredientes[]
  4. Retornar structured output (NutritionalProfile)
```

**Prompt OCR** (ejemplo):
```
"Extrae los valores nutricionales de esta imagen. Retorna SOLO los valores numéricos
y la lista de ingredientes en formato JSON. NO incluyas nombre de marca ni fabricante."
```

## Evaluación Semáforo — Resultado del Scanner

```
ROJO   (🔴): ingrediente tóxico detectado (FoodSafetyChecker) O ingrediente
              restringido para condición médica activa (MedicalRestrictionEngine)
AMARILLO (🟡): posible alergia detectada O desequilibrio nutricional significativo
VERDE  (🟢): perfil nutricional adecuado para la mascota
```

**Orden de evaluación** (determinístico, post-OCR):
1. FoodSafetyChecker — tóxicos → ROJO inmediato
2. MedicalRestrictionEngine — restricciones por condición → ROJO
3. Allergy check — contra `pet.allergies` → AMARILLO
4. Nutritional balance — proteínas/grasas fuera de rango NRC → AMARILLO
5. Si ningún problema → VERDE

## Resultado del Scanner — Schema

```json
{
  "scan_id": "uuid",
  "semaphore": "rojo|amarillo|verde",
  "detected_issues": [
    {
      "severity": "critical|warning",
      "issue_type": "toxic|restricted|allergy|nutritional_mismatch",
      "ingredient": "nombre del ingrediente problemático",
      "reason": "explicación en español"
    }
  ],
  "nutritional_profile": {
    "protein_pct": 28.5,
    "fat_pct": 15.0,
    "moisture_pct": 10.0,
    "fiber_pct": 3.5,
    "kcal_per_100g": 380
  },
  "recommendation": "texto de recomendación",
  "disclaimer": "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
  // SIN campo brand_name — por diseño
}
```

## Casos de Prueba Críticos

- [ ] Imagen frontal (logo) → rechazada con mensaje claro (nodo ImageValidator)
- [ ] Tabla nutricional → aceptada, OCR ejecutado
- [ ] Lista de ingredientes → aceptada, OCR ejecutado
- [ ] Cebolla en ingredientes → ROJO (FoodSafetyChecker)
- [ ] Ingrediente restringido para diabético → ROJO (MedicalRestrictionEngine)
- [ ] Ingrediente en alergias del pet → AMARILLO
- [ ] Proteínas adecuadas, sin tóxicos ni restricciones → VERDE
- [ ] Resultado nunca incluye nombre de marca (test de schema)
- [ ] Siempre usa gpt-4o independientemente del tier (test de mock)
- [ ] OCR success rate ≥ 85% (Quality Gate G4)

## Referencias

- Spec: `aidlc-docs/inception/units/unit-06-scanner-service.md`
- ADR-019: OCR siempre gpt-4o
- Constitution: REGLA 7 (solo tabla nutricional o ingredientes)
- Quality Gates: G4 (≥ 85% OCR success rate)
