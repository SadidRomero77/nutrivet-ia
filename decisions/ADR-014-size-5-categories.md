# ADR-014 — 5 Categorías de Talla para Perros con Rangos de Peso

**Estado**: Aceptado
**Fecha**: 2026-03
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Contexto

La clasificación inicial del proyecto usaba 4 tallas para perros (pequeño/mediano/grande/gigante). El modelo de negocio incluye razas toy y miniatura (Chihuahua, Yorkshire, Maltés) que tienen características metabólicas y fisiológicas distintas a un Poodle o Cocker Spaniel. Estas razas micro necesitan su propia categoría para cálculos NRC más precisos.

## Decisión

Ampliar a 5 categorías con rangos de peso explícitos. Gatos no tienen clasificación de talla.

| Código | Nombre | Rango kg | Ejemplos |
|--------|--------|----------|---------|
| `mini` | MINI XS | 1-4 kg | Chihuahua, Yorkshire, Maltés |
| `pequeño` | PEQUEÑO S | 4-9 kg | Poodle Toy, French Poodle, Pomerania |
| `mediano` | MEDIANO M | 9-14 kg | Beagle, Cocker Spaniel, French Bulldog |
| `grande` | GRANDE L | 14-30 kg | Labrador, Golden Retriever, Border Collie |
| `gigante` | GIGANTE XL | +30 kg | Gran Danés, San Bernardo, Mastín |

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| 4 tallas (anterior) | Más simple | Mini/toy no bien representados |
| 5 tallas (elegida) | Refleja fisiología real | 1 enum adicional |
| Sin talla (solo peso) | Más preciso | El peso cambia — la talla es referencia constante |

## Consecuencias

**Positivas**:
- Cálculos NRC más precisos para razas toy.
- Wizard más intuitivo — el owner entiende su raza mejor con descripción que con rango de kg.
- Validación adicional: si el peso declarado es incongruente con la talla elegida → advertencia.

**Negativas**:
- Gatos no tienen talla → `size = None` para gatos — requiere validación en el aggregate.

**Regla de validación**: Si `species == GATO → size must be None`. Si `species == PERRO → size required`.
