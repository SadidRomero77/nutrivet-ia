# Requisito: Alimentación Actual como Paso Formal del Wizard

## Problema que resuelve
Sin conocer qué come la mascota HOY, el agente no puede calcular si se necesita un protocolo de transición alimentaria. Un cambio brusco de dieta causa problemas digestivos (diarrea, vómito, rechazo del alimento).

## Usuarios afectados
- [x] Owner (completa el wizard)

## Motivación clínica
La transición gradual (7 días) es estándar en nutrición veterinaria. Sin este dato, el agente generaría planes que podrían causar problemas digestivos inmediatos al implementarse.

## Comportamientos esperados

```gherkin
Scenario: Wizard pregunta alimentación actual
  Given el owner está completando el wizard de mascota
  When llega al paso de "Alimentación actual"
  Then el sistema muestra tres opciones: "Solo concentrado", "Solo dieta natural", "Mixto"
  And cada opción tiene una descripción breve para guiar al owner

Scenario: Plan incluye transición cuando la modalidad es diferente a la dieta actual
  Given la mascota come "concentrado" actualmente
  And el owner selecciona modalidad "Natural" para el plan
  When el agente genera el plan
  Then el plan incluye un protocolo de transición de 7 días
  And el protocolo especifica qué porcentaje de cada tipo incluir cada día

Scenario: Sin transición cuando la modalidad coincide con la dieta actual
  Given la mascota come "natural" actualmente
  And el owner selecciona modalidad "Natural" para el plan
  When el agente genera el plan
  Then el plan NO incluye protocolo de transición
  And puede incluir ajustes de ingredientes directamente

Scenario: Alerta de alergias desconocidas al usar dieta mixta
  Given la mascota tiene alimentación actual "mixto"
  And el owner no ha registrado alergias
  When el agente analiza el perfil
  Then muestra alerta recomendando prueba de alérgenos
  And el owner debe confirmar explícitamente para continuar
```

## Criterios de aceptación
- [ ] Campo `current_diet` guardado en PetProfile antes de generar plan.
- [ ] El protocolo de transición se incluye automáticamente cuando `current_diet ≠ modalidad_plan`.
- [ ] El protocolo de transición detalla los 7 días con porcentajes exactos.
- [ ] El campo es actualizable (si el owner cambia la dieta de su mascota, puede actualizarlo).

## Lo que NO incluye
- Análisis detallado de la marca/tipo de concentrado actual (eso es el OCR scanner).
- Transición para mascotas recién adoptadas (caso especial — se trata como "desconocido").

## Referencia PRD
Sección: Flujo de generación del plan — Paso 3: Identificación de alimentación actual.

## Impacto en arquitectura
- PetProfile: nuevo campo `current_diet: CurrentDiet` (enum: CONCENTRADO / NATURAL / MIXTO).
- Wizard Flutter: nuevo step entre BCS y antecedentes médicos.
- NRC Calculator: recibe `current_diet` para determinar si incluir `transition_protocol`.
- Plan Generation Subgraph: verifica `current_diet vs modalidad` → incluye/excluye transición.
