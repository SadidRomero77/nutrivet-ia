# ADR-020 — Plan Nutricional Visual Interactivo por Secciones

**Estado**: Aceptado
**Fecha**: 2026-03-11
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Contexto

El plan nutricional generado por el agente es el producto principal de NutriVet.IA. En versiones anteriores
se planteaba como un documento de texto o PDF. Sin embargo, un plan nutricional contiene información crítica
y variada (alertas de toxicidad, protocolo de transición, cuidados de salud, menú diario) que se vuelve
confusa en formato plano.

El owner necesita consultar su plan fácilmente, navegar por secciones relevantes sin scroll interminable,
y el veterinario necesita revisar el plan en forma organizada para su firma.

## Decisión

El plan nutricional se presenta como una **pantalla Flutter interactiva por secciones colapsables**,
no como un documento PDF o texto plano. La estructura de secciones es fija para todos los planes.

### Estructura de Secciones del Plan

```
┌─────────────────────────────────────────────┐
│  🐾 Plan de [Nombre mascota]                │
│  [Chip especie] [Chip condición si aplica]  │
│  DER: 534 kcal/día  •  BCS: 6/9            │
│  [Disclaimer obligatorio — siempre visible] │
└─────────────────────────────────────────────┘

  SECCIÓN 1: ⚠️  Alimentos Prohibidos
  ├── Alimentos tóxicos (TOXIC_DOGS/CATS)     ← siempre expandida
  └── Restricciones por condición médica

  SECCIÓN 2: 🔄  Protocolo de Transición (7 días)
  ├── Barra de progreso visual día a día
  ├── Porcentaje actual/nuevo por día
  └── Alertas: síntomas a vigilar

  SECCIÓN 3: 🏥  Cuidados de Salud
  ├── Indicaciones por condición médica activa
  ├── Señales de alerta → consultar vet
  └── Hidratación requerida (ml/día)

  SECCIÓN 4: 📅  Plan por Días
  ├── Vista semanal (tabs: Lun-Dom)
  ├── Por comida: desayuno / almuerzo / cena / snack
  ├── Ingrediente + gramos + instrucción de preparación
  └── Kcal por comida + total del día

  SECCIÓN 5: 📊  Resumen Nutricional
  ├── Macros: proteína / grasa / carbohidrato / fibra (% y gramos)
  ├── Micronutrientes clave (Ca, P, Omega-3)
  └── Comparativa vs. requerimiento NRC (barra de progreso)
```

### Comportamiento de Secciones

- **Sección 1 (Prohibidos)**: siempre visible y expandida al abrir el plan — es información de seguridad crítica
- **Sección 2 (Transición)**: expandida si el plan es nuevo o está en fase de transición; colapsada si el plan ya está activo
- **Secciones 3-5**: colapsables, el usuario puede expandir/colapsar libremente
- **Plan por días**: tabs horizontales (Lun → Dom), con indicador de "día actual" resaltado
- **Estado PENDING_VET**: banner prominente en la parte superior, todas las secciones son solo lectura

### Exportación

- **PDF**: genera snapshot del plan en el mismo layout de secciones (no diseño diferente)
- **Compartir**: incluye solo Sección 4 (Plan por días) + Disclaimer + branding NutriVet.IA
- Solo disponible para planes en estado `ACTIVE`

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| **Secciones interactivas (elegida)** | Navegación clara, información crítica destacada | Más desarrollo UI |
| Documento PDF estático | Familiar | No interactivo, difícil de actualizar |
| Chat con el plan (todo conversacional) | Natural | Difícil de consultar información específica rápidamente |
| Lista de ingredientes plana | Simple | No comunica la estructura del plan ni las alertas de seguridad |

## Consecuencias

**Positivas**:
- La Sección 1 (Prohibidos) siempre visible reduce riesgo de error del owner.
- La navegación por tabs en Sección 4 es familiar y fácil de usar.
- El layout de secciones es el mismo en app y PDF — coherencia visual.
- El veterinario puede revisar cada sección durante el proceso HITL.

**Negativas**:
- Requiere más trabajo de UI en Flutter (tabs, acordeones, barras de progreso).
- El generador de PDF debe respetar el mismo layout de secciones.

## Impacto en Unidades

- **U-04 plan-service**: el `PlanResponse` (Pydantic) debe estructurar los datos por secciones
- **U-08 export-service**: el generador de PDF debe consumir el mismo esquema de secciones
- **U-09 mobile-app**: implementar `PlanDetailScreen` con las 5 secciones descritas
