# Business Logic Model — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos del Scanner Service

### Flujo Principal: Escaneo de Etiqueta

```
POST /scanner/scan (multipart: image_file + pet_id + image_type)
  ↓
1. Validar Pydantic schema: image_type ∈ {nutrition_table, ingredients_list}
2. Validar tamaño de imagen: max 10MB
3. Validar formato: JPEG/PNG/WEBP
4. Crear LabelScan(status=PENDING)
5. Subir imagen a Cloudflare R2: key = scans/{owner_id}/{scan_id}.{ext}
6. LabelScan.r2_image_key = key
7. LabelScan.status = PROCESSING

  ↓ Nodo: ImageValidator (determinista)
8. Obtener imagen de R2
9. Enviar a gpt-4o con prompt: "¿Esta imagen muestra una tabla nutricional o una lista de ingredientes de un alimento para mascotas? Responde SOLO: nutrition_table, ingredients_list, o invalid."
10. Si respuesta == "invalid" → LabelScan.status = REJECTED, retornar error

  ↓ Nodo: OCR Extraction
11. Enviar imagen a gpt-4o-vision con prompt estructurado para extraer:
    - Lista de ingredientes (si ingredients_list)
    - Tabla nutricional: proteína, grasa, fibra, humedad, cenizas, calorías (si nutrition_table)
12. Parsear respuesta JSON del LLM → NutritionalProfile
13. Si parseo falla → LabelScan.status = FAILED

  ↓ Nodo: ToxicityCheck (determinista)
14. Para cada ingrediente en parsed_nutrients.ingredients:
    FoodSafetyChecker.check(ingredient, pet.especie)
    Si tóxico → agregar a toxic_ingredients_found, semaphore = RED

  ↓ Nodo: MedicalRestrictionsCheck (determinista)
15. MedicalRestrictionEngine.check_all(ingredients, pet.condiciones_medicas)
    Si restricción violada → agregar a restricted_ingredients_found, semaphore = RED (o YELLOW si leve)

  ↓ Nodo: AllergyCheck (determinista)
16. Verificar ingredientes contra pet.alergias
    Si alérgeno encontrado → semaphore = RED

  ↓ Nodo: SemaphoreCalculation (determinista)
17. Si cualquier finding.severity == "critical" → RED
18. Si cualquier finding.severity == "warning" y sin críticos → YELLOW
19. Si sin findings → GREEN

  ↓ Nodo: LLM Recommendation (creativo, no determina semáforo)
20. Enviar NutritionalProfile + semaphore + findings a LLM
21. LLM genera texto de recomendación (máx 200 palabras)

22. Persistir ProductEvaluation y LabelScan.status = COMPLETED
23. Retornar { scan_id, semaphore, findings, recommendation } + HTTP 200
```

### Flujo: Obtener Resultado de Escaneo

```
GET /scanner/scans/{scan_id}
  ↓
1. Verificar ownership
2. Retornar LabelScan con ProductEvaluation si status == COMPLETED
3. Si status == PROCESSING → HTTP 202 (aún procesando)
4. Si status == FAILED/REJECTED → HTTP 422 con error_message
```

### Flujo: Historial de Escaneos del Pet

```
GET /pets/{pet_id}/scans
  ↓
1. Verificar ownership
2. Retornar list[LabelScan] ordenado por created_at DESC
3. Sin imagen (solo metadata y resultado)
```
