# Business Rules — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas Deterministas (Hard-Coded, No Negociables)

### BR-01: Cálculo RER/DER — Nunca LLM
```
RER = 70 × peso_kg^0.75
DER = RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs
```
- El cálculo calórico NUNCA es delegado al LLM.
- Implementado en `domain/nutrition/nrc_calculator.py`.
- Golden case Sally: RER ≈ 396 kcal · DER ≈ 534 kcal/día (tolerancia ±0.5 kcal).

### BR-02: TOXIC_DOGS y TOXIC_CATS — Hard-Coded
- Listas de ingredientes tóxicos definidas como constantes Python en `domain/safety/toxic_foods.py`.
- El LLM NUNCA decide toxicidad.
- Si un ingrediente aparece en la lista → rechazado siempre, sin excepción.
- Alimentos tóxicos para perros (mínimo): uvas, pasas, cebolla, ajo, xilitol, chocolate, macadamia, aguacate (pulpa), alcohol, cafeína, nuez moscada, levadura cruda.
- Alimentos tóxicos para gatos (mínimo): cebolla, ajo, uvas, lilium, chocolate, cafeína, alcohol, xilitol, paracetamol, aceites esenciales.

### BR-03: RESTRICTIONS_BY_CONDITION — Hard-Coded
- 13 condiciones médicas con restricciones de ingredientes hard-coded en `domain/safety/medical_restrictions.py`.
- El LLM no puede sobrescribir estas restricciones.
- En caso de conflicto LLM vs. restricción hard-coded → la restricción gana siempre.
- Condiciones: `diabético · hipotiroideo · cancerígeno · articular · renal · hepático/hiperlipidemia · pancreático · neurodegenerativo · bucal/periodontal · piel/dermatitis · gastritis · cistitis/enfermedad_urinaria · sobrepeso/obesidad`

### BR-04: Máquina de Estados del Plan
```
PENDING_VET → ACTIVE (firma vet)
ACTIVE → UNDER_REVIEW (trigger: condición médica agregada, alerta o revisión periódica)
UNDER_REVIEW → ACTIVE (re-aprobación vet)
ACTIVE → ARCHIVED (plan reemplazado por nuevo plan)
```
- Mascota sana → ACTIVE directo (sin HITL).
- Mascota con condición médica → PENDING_VET → requiere firma vet.
- Si owner agrega condición a plan ACTIVE → vuelve a PENDING_VET automáticamente.

### BR-05: BCS Determina Fase del Plan
- BCS ≥ 7 → fase reducción: `RER(peso ideal) × factor × 0.8`
- BCS 4–6 → fase mantenimiento: `RER × factor`
- BCS ≤ 3 → fase aumento: `RER × factor × 1.2`
- Para reducción, RER se calcula sobre peso ideal estimado, NO sobre peso real.

### BR-06: Ayuno Máximo 12 Horas
- Los planes NUNCA deben incluir ayunos mayores a 12 horas.
- Riesgo: hepatopatía, colestasis, pancreatitis.

### BR-07: Alergias "No Sabe"
- Si `alergias == ["no_sabe"]` → alerta obligatoria en el plan.
- El sistema debe recomendar test de alérgenos antes de proceder.

### BR-08: Factors DER (Referencia)
| Factor | Condición | Valor |
|--------|-----------|-------|
| factor_edad | Cachorro < 4 meses | 3.0 |
| factor_edad | Cachorro 4-12 meses | 2.0 |
| factor_edad | Adulto | 1.0 |
| factor_edad | Senior > 7 años | 0.9 |
| factor_reproductivo | Esterilizado | 0.8 |
| factor_reproductivo | No esterilizado | 1.0 |
| factor_actividad (perro) | Sedentario | 1.2 |
| factor_actividad (perro) | Moderado | 1.4 |
| factor_actividad (perro) | Activo | 1.6 |
| factor_actividad (perro) | Muy activo | 1.8 |
| factor_actividad (gato) | Indoor | 1.0 |
| factor_actividad (gato) | Indoor/outdoor | 1.2 |
| factor_actividad (gato) | Outdoor | 1.4 |
| factor_bcs | BCS ≤ 3 | 1.2 |
| factor_bcs | BCS 4–6 | 1.0 |
| factor_bcs | BCS ≥ 7 | 0.8 |
