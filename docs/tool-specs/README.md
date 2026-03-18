# Tool Specs — NutriVet.IA Agent Tools v2
> Playbook ref: sección 5.2 — "Tool Spec"
> 5 tools del agente LangGraph. Toda lógica determinista está en domain layer — el LLM solo sintetiza lenguaje natural.

---

## Tool 1 — nutrition_calculator

**Propósito**: Calcular RER (Requerimiento Energético en Reposo) y DER (Requerimiento Energético Diario) de forma determinista usando fórmula NRC.

**Input schema**:
```json
{
  "pet_id": "uuid",
  "weight_kg": 9.6,
  "species": "dog",
  "reproductive_status": "sterilized",
  "activity_level": "low",
  "age_years": 8.0,
  "body_condition_score": 3,
  "physiological_state": "senior",
  "medical_conditions": ["diabetic", "hepatic"]
}
```

**Output schema**:
```json
{
  "rer_kcal": 404.2,
  "der_kcal": 534.0,
  "factor_applied": 1.32,
  "adjustments": {
    "bcs_adjustment": 1.10,
    "age_adjustment": 0.85,
    "condition_adjustment": 0.90
  },
  "meals_per_day": 3,
  "protein_g_day": 120.0,
  "fat_g_day": 20.0,
  "carbs_g_day": 25.0,
  "fiber_g_day": 5.0,
  "water_ml_day_min": 480.0
}
```

**Reglas críticas**:
- NUNCA delegar al LLM — siempre ejecutar función Python determinista
- Los factores de ajuste están en `FACTOR_TABLE` y `BCS_ADJUSTMENTS` en domain layer
- Validado contra caso real: Sally 9.6 kg → 534 kcal/día

**Errores accionables**:
- `WEIGHT_OUT_OF_RANGE`: peso fuera de rango esperado para la especie/talla
- `MISSING_BCS`: BCS requerido para ajuste calórico — solicitar al usuario
- `INVALID_ACTIVITY_FOR_SPECIES`: gatos solo aceptan indoor/outdoor

---

## Tool 2 — food_toxicity_checker

**Propósito**: Verificar si un alimento o ingrediente es tóxico o está contraindicado para la especie y condición médica específica del paciente.

**Input schema**:
```json
{
  "food_name": "uvas",
  "species": "dog",
  "medical_conditions": ["diabetic", "hepatic"],
  "pet_food_allergies": ["chicken", "wheat"]
}
```

**Output schema**:
```json
{
  "food_name": "uvas",
  "is_safe": false,
  "risk_level": "toxic",
  "reason": "Las uvas y pasas son tóxicas para perros — pueden causar insuficiencia renal aguda.",
  "blocked_by": "SPECIES_TOXICITY",
  "safe_alternatives": ["arándanos", "melón", "pera"],
  "action": "BLOCK"
}
```

**Niveles de riesgo**:
- `safe`: apto para el paciente
- `caution`: precaución — limitar cantidad o frecuencia
- `high_risk`: contraindicado para su condición médica
- `toxic`: tóxico para la especie — BLOQUEAR siempre

**Fuentes de bloqueo** (`blocked_by`):
- `SPECIES_TOXICITY`: tóxico para la especie (hard-coded, no negociable)
- `MEDICAL_CONDITION`: contraindicado por condición médica registrada
- `CONFIRMED_ALLERGY`: alérgeno confirmado del paciente
- `UNKNOWN_ALLERGY_RISK`: posible alérgeno (usuario no realizó test)

**Reglas críticas**:
- Listas `TOXIC_DOGS` y `TOXIC_CATS` son hard-coded en domain — nunca LLM
- Si `risk_level = toxic` → `action = BLOCK` siempre, sin excepción
- Restricciones por condición médica en `RESTRICTIONS_BY_CONDITION` (domain layer)

---

## Tool 3 — plan_generator

**Propósito**: Generar el plan nutricional completo según la modalidad elegida (natural o concentrado), aplicando todos los filtros de toxicidad, alergias y condición médica.

**Input schema**:
```json
{
  "pet_id": "uuid",
  "modality": "natural",
  "nutritional_requirements": { "der_kcal": 534, "protein_g_day": 120, "..." },
  "approved_ingredients": { "proteins": [...], "carbs": [...], "vegetables": [...] },
  "forbidden_ingredients": ["uvas", "cebolla", "..."],
  "medical_conditions": ["diabetic", "hepatic"],
  "meals_per_day": 3,
  "preferences": { "avoid_fish": false }
}
```

**Output schema — modalidad natural**:
```json
{
  "modality": "natural",
  "daily_kcal": 534,
  "meals_per_day": 3,
  "macros_per_meal": {
    "protein_g": 40,
    "carbs_g": 10,
    "vegetables_g": 30,
    "total_g": 80
  },
  "approved_proteins": ["pechuga de pollo", "res magra", "salmón (2x/semana)"],
  "approved_carbs": ["arroz blanco/integral", "papa sin cascara", "quinoa"],
  "approved_vegetables": ["zanahoria", "habichuela", "espinaca", "pepino"],
  "approved_fruits": ["pera", "melón", "arándanos", "fresa"],
  "fiber_addition": "Hojuelas de avena crudas (1 cdta/porción, 3x/semana)",
  "flavor_additions": ["sal marina (pizca)", "albahaca", "orégano", "romero"],
  "forbidden_foods": ["cebolla", "ajo", "uvas", "chocolate", "cerdo", "..."],
  "preparation_notes": "Cocinar sin aceite, sin sal, sin ajo ni cebolla. Pesar porciones cocidas en gramera.",
  "snacks": [
    { "name": "Gomitas de proteína", "recipe": "1 taza caldo + 2 sobres gelatina sin sabor", "portion": "2 cubitos/día" },
    { "name": "Caldo de proteína tibio", "portion": "1/4 taza/ración" },
    { "name": "Fruta del listado", "portion": "5g" },
    { "name": "Huevo cocido", "portion": "1/4 huevo gallina, 2x/semana" }
  ],
  "supplements_reference": [
    { "name": "Omega-3", "indication": "Función hepática y antiinflamatorio" },
    { "name": "Cúrcuma", "dose": "1/4 cdta en cocción de proteína/día", "indication": "Hepático/biliar" }
  ],
  "transition_protocol": {
    "day_1_2": "75% alimento actual + 25% nuevo",
    "day_3_4": "50% + 50%",
    "day_5_6": "25% + 75%",
    "day_7_plus": "100% nuevo plan"
  },
  "emergency_protocol": "Suspender dieta sólida. Solo proteína + papa/arroz. Si grave: dieta líquida 4-6x/día. Si no mejora en 24h: veterinario.",
  "dental_hygiene_note": "Con dieta natural: lavar plato después de cada comida. Considerar enjuague bucal veterinario en agua de bebida.",
  "water_intake_note": "Es normal que disminuya el consumo de agua con dieta natural. Ofrecer agua fresca, cubitos de hielo o frutas ricas en agua.",
  "disclaimer": "Este plan es una guía nutricional complementaria. No reemplaza el tratamiento médico ni la consulta veterinaria."
}
```

**Output schema — modalidad concentrate**:
```json
{
  "modality": "concentrate",
  "daily_kcal": 534,
  "ideal_profile": {
    "protein_pct_min": 26,
    "fat_pct_max": 10,
    "fiber_pct_min": 4,
    "carbs_pct_max": 35,
    "moisture_pct_range": "8-12"
  },
  "recommended_protein_sources": ["pollo", "pescado", "pavo"],
  "avoid_ingredients": ["maíz como primer ingrediente", "colorantes artificiales", "azúcar"],
  "food_type": "dry",
  "meals_per_day": 3,
  "life_stage": "senior",
  "transition_protocol": { "..." },
  "disclaimer": "..."
}
```

**Reglas críticas**:
- `forbidden_foods` NO se puede modificar — siempre incluye la lista de tóxicos para la especie
- Si condición médica → plan marcado como `PENDING_VET`
- Suplementos son referenciales — no son prescripción médica
- Snacks son saludables, entre comidas — no reemplazar porciones principales

---

## Tool 4 — product_scanner

**Propósito**: Analizar imagen de tabla nutricional o lista de ingredientes de un concentrado comercial y evaluar su adecuación para el paciente específico.

**Input schema**:
```json
{
  "image_base64": "...",
  "image_type": "nutritional_table",
  "pet_id": "uuid",
  "pet_profile": {
    "species": "dog",
    "weight_kg": 9.6,
    "der_kcal": 534,
    "medical_conditions": ["diabetic", "hepatic"],
    "food_allergies": []
  }
}
```

**Validación previa (antes de llamar GPT-4o)**:
```
image_type DEBE ser: 'nutritional_table' | 'ingredients_list'
Si imagen contiene principalmente texto de marca → rechazar con código NO_BRAND_IMAGES
```

**Output schema**:
```json
{
  "extracted_values": {
    "protein_pct": 28.0,
    "fat_pct": 12.0,
    "carbs_pct": 40.0,
    "fiber_pct": 4.0,
    "moisture_pct": 10.0,
    "phosphorus_mg_100g": 900,
    "sodium_mg_100g": 350,
    "ingredients_ordered": ["pollo", "arroz", "maíz", "grasa de pollo", "..."]
  },
  "adequacy": "caution",
  "concerns": [
    "Nivel de grasa del 12% puede ser elevado para paciente con hepatopatía (recomendado <10%)",
    "Maíz como tercer ingrediente — fuente de carbohidratos de alto índice glucémico para diabético"
  ],
  "positives": [
    "Pollo como primer ingrediente — proteína magra adecuada",
    "Nivel de fósforo aceptable para función hepática"
  ],
  "recommendation": "Este concentrado es una opción de precaución. Consulta con tu veterinario sobre el nivel de grasa dado el diagnóstico de hepatopatía.",
  "confidence": 0.87,
  "disclaimer": "Esta evaluación es referencial y no reemplaza la opinión veterinaria."
}
```

**Errores accionables**:
- `NO_BRAND_IMAGES`: imagen contiene principalmente marca/logo — solicitar solo tabla nutricional
- `LOW_CONFIDENCE`: OCR con baja confianza — solicitar imagen con mejor iluminación
- `MISSING_VALUES`: tabla incompleta — indicar qué valores no se pudieron extraer

---

## Tool 5 — concentrate_advisor

**Propósito**: Generar el perfil del concentrado ideal para el paciente y, si hay sponsors verificados que coincidan, mostrarlos con el tag "Patrocinado".

**Input schema**:
```json
{
  "pet_id": "uuid",
  "nutritional_requirements": { "der_kcal": 534, "..." },
  "medical_conditions": ["diabetic", "hepatic"],
  "food_allergies": ["wheat"],
  "size": "small",
  "age_years": 8.0,
  "physiological_state": "senior"
}
```

**Output schema**:
```json
{
  "ideal_profile": {
    "protein_pct_min": 26,
    "fat_pct_max": 10,
    "fiber_pct_min": 4,
    "avoid_ingredients": ["azúcar", "trigo", "colorantes", "maíz primer ingrediente"],
    "preferred_protein_source": ["pollo", "pescado", "pavo"],
    "food_type": "dry",
    "life_stage_label": "Senior"
  },
  "sponsored_options": [
    {
      "sponsor_id": "uuid",
      "brand_name": "...",
      "disclosure": "Contenido patrocinado",
      "nutritional_match_pct": 92,
      "suitable_for_conditions": ["diabetic", "hepatic"]
    }
  ],
  "shopping_guide": "Busca un alimento seco para perro adulto/senior, con mínimo 26% proteína, máximo 10% grasa, sin trigo ni azúcar en sus primeros 5 ingredientes.",
  "disclaimer": "Las recomendaciones de concentrado son orientativas. Siempre verifica con tu veterinario."
}
```

**Reglas críticas**:
- Si `sponsored_options` tiene elementos → `disclosure` siempre presente y visible
- Solo incluir sponsors donde `suitable_conditions` incluye TODAS las condiciones del paciente
- Si sponsor tiene `contraindicated_conditions` que incluye alguna condición del paciente → NO mostrar
- Máximo 3 sponsors por resultado
