# Workflow — Generación de Plan Nutricional

**Subgrafo LangGraph**: `Plan Generation Subgraph`
**Trigger**: Owner completa wizard de mascota y solicita plan.

---

## Diagrama de Flujo

```
Owner solicita plan
       │
       ▼
[1] nutrition_calculator (determinista)
  → RER = 70 × peso_kg^0.75
  → DER = RER × factores
  → BCS → determina fase (reducción/mantenimiento/aumento)
       │
       ▼
[2] food_toxicity_checker (determinista)
  → Verifica lista de ingredientes vs TOXIC_DOGS / TOXIC_CATS
  → Aplica RESTRICTIONS_BY_CONDITION según condiciones médicas
  → Output: ingredientes permitidos + prohibidos
       │
       ▼
[3] LLM Routing (determinista)
  → 0 condiciones → Ollama Qwen2.5-7B
  → 1-2 condiciones → Groq Llama-70B
  → 3+ condiciones → GPT-4o
       │
       ▼
[4] LLM genera plan (no determinista — con guardarraíles)
  → Selecciona ingredientes del set permitido
  → Calcula porciones en gramos (respetando DER)
  → Modalidad A (Natural): ingredientes LATAM + preparación
  → Modalidad B (Concentrado): perfil ideal + criterios selección
       │
       ▼
[5] hitl_router
  → Mascota SANA → plan.status = ACTIVE → notificar owner
  → Mascota CON CONDICIÓN → plan.status = PENDING_VET → notificar vet
       │
       ▼
[6] Registrar en agent_traces (append-only, inmutable)
```

---

## Reglas de Negocio del Workflow

1. Pasos [1] y [2] son siempre deterministas — el LLM no puede sobrescribir sus outputs.
2. El LLM solo decide qué ingredientes elegir DENTRO del set permitido por [2].
3. El LLM no calcula calorías — usa el DER calculado en [1] como restricción.
4. Ningún ingrediente de `TOXIC_DOGS`/`TOXIC_CATS` puede aparecer en el output del LLM. El plan se invalida si ocurre.
5. El paso [5] es determinista: si `pet.medical_conditions` tiene alguna condición → `PENDING_VET`, siempre.

---

## Contexto de Prompt al LLM (anonimizado)

```
Pet ID: {pet_id}           ← UUID anónimo, nunca nombre
Species: {species}
Age category: {age_cat}    ← "adult", "senior", "puppy" — no edad exacta
DER target: {der_kcal} kcal
Allowed ingredients: {allowed_list}
Prohibited ingredients: {prohibited_list}
Medical conditions: {conditions}  ← IDs, no texto libre
Plan modality: {modality}
```

---

## Manejo de Errores

| Error | Respuesta |
|-------|-----------|
| LLM timeout (> 30s) | Retry × 2 → modelo fallback → error controlado al owner |
| Ingrediente tóxico en output LLM | Invalidar plan, log P0, regenerar sin ese ingrediente |
| DER calculado < 200 kcal (sospechoso) | Alerta, verificar inputs, no generar plan |
| Ollama no disponible (0 condiciones) | NO fallback a GPT-4o. Error con mensaje "servicio temporalmente no disponible" |
