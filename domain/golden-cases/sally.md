# Golden Case — Sally (Referencia Clínica Canónica)

**Fuente de verdad**: Este archivo es la única definición canónica del caso Sally.
Todos los demás documentos deben referenciar este archivo, no copiar los datos.
Validado por: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Perfil de la Mascota

| Campo | Valor |
|-------|-------|
| Nombre | Sally |
| Especie | Perro |
| Raza | French Poodle |
| Sexo | Hembra |
| Edad | 8 años |
| Peso | 9.6 kg |
| Estado reproductivo | Esterilizada |
| Nivel de actividad | Sedentaria |
| BCS | 6/9 |
| Talla | Mediano M (9-14 kg) |

## Condiciones Médicas (5)

1. Diabetes Mellitus
2. Hepatopatía
3. Hiperlipidemia
4. Gastritis
5. Cistitis / Enfermedad urinaria

## Output Esperado

| Métrica | Valor | Tolerancia |
|---------|-------|-----------|
| RER | ≈ 396 kcal | ± 0.5 kcal |
| DER | ≈ 534 kcal/día | ± 0.5 kcal |
| LLM routing | `anthropic/claude-sonnet-4-5` | Override clínico: 5 condiciones ≥ 3 |
| Estado del plan | `PENDING_VET` | HITL obligatorio (condiciones médicas) |

## Factores NRC Aplicados

| Factor | Valor | Justificación |
|--------|-------|--------------|
| factor_edad | 1.4 | Senior (> 7 años) |
| factor_reproductivo | 0.9 | Esterilizada |
| factor_actividad | 1.2 | Sedentaria |
| factor_bcs | 1.0 | BCS 6 — mantenimiento |

## Cálculo de Referencia

```python
RER = 70 × 9.6^0.75 = 70 × 5.655... ≈ 396 kcal
DER = 396 × 1.4 × 0.9 × 1.2 × 1.0 ≈ 534 kcal/día
```

## Uso en el Proyecto

- **Test bloqueante CI**: `tests/domain/test_nrc_calculator.py::test_sally_golden_case`
- **Quality Gate G8**: DER reproducible ±0.5 kcal
- **Quality Gate G6**: Lady Carolina evalúa el plan generado para este caso
- **LLM override**: 5 condiciones médicas → `anthropic/claude-sonnet-4-5` en cualquier tier

## Restricciones Activas para Sally

Por sus condiciones médicas, el plan debe excluir (RESTRICTIONS_BY_CONDITION):

- **Diabética**: azúcar, miel, frutas dulces, harinas refinadas, arroz blanco
- **Hepática/Hiperlipidemia**: grasas saturadas altas, carne procesada, yema de huevo en exceso
- **Pancreática/Gastritis**: alimentos grasos, picantes, condimentos, comida muy caliente/fría
- **Cistitis**: sodio alto, alimentos formadores de oxalatos en exceso

> Restricciones completas en: `domain/safety/restrictions.py` → `RESTRICTIONS_BY_CONDITION`
