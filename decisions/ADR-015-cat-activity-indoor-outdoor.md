# ADR-015 — Actividad de Gatos: Indoor / Indoor-Outdoor / Outdoor

**Estado**: Aceptado
**Fecha**: 2026-03
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Contexto

La versión inicial del proyecto usaba los mismos niveles de actividad para perros y gatos (sedentario/moderado/activo/muy_activo). Sin embargo, los estándares NRC para felinos clasifican la actividad de manera diferente — la distinción principal en gatos es si tienen acceso al exterior o no, lo que impacta directamente su gasto energético base.

## Decisión

Implementar clasificaciones de actividad separadas por especie:

```python
class DogActivityLevel(str, Enum):
    SEDENTARIO = "sedentario"       # Factor: ~1.2
    MODERADO = "moderado"           # Factor: ~1.4
    ACTIVO = "activo"               # Factor: ~1.6
    MUY_ACTIVO = "muy_activo"       # Factor: ~1.8

class CatActivityLevel(str, Enum):
    INDOOR = "indoor"               # Factor: ~1.0 (NRC felino estándar)
    INDOOR_OUTDOOR = "indoor_outdoor"  # Factor: ~1.2
    OUTDOOR = "outdoor"             # Factor: ~1.4
```

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| Mismo enum para ambas especies | Más simple | Clínicamente incorrecto para felinos |
| Enums separados (elegida) | Clínicamente correcto, NRC-compliant | Complejidad adicional en el modelo |
| Solo indoor/outdoor sin "mixto" | Más simple | No refleja la realidad — muchos gatos son mixtos |

## Consecuencias

**Positivas**:
- Cálculos NRC más precisos para gatos.
- Nomenclatura más intuitiva para owners de gatos — "indoor vs outdoor" es más comprensible que "sedentario".
- Clínicamente correcto según literatura veterinaria.

**Negativas**:
- El campo `activity_level` en el aggregate tiene tipo union `DogActivityLevel | CatActivityLevel`.
- Validación obligatoria en el aggregate: `species == GATO → activity_level instanceof CatActivityLevel`.

**Impacto en UI**: El wizard de Flutter muestra opciones diferentes de actividad según la especie seleccionada en el paso 2.
