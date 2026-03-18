# Skill: PRD Generator

## Propósito
Guiar la creación de un Product Requirements Document (PRD) completo para NutriVet.IA siguiendo las mejores prácticas de product management y spec-driven development.

## Cuándo activar
Cuando el usuario quiera definir o refinar los requisitos de una funcionalidad o del producto completo.

## Proceso

### Paso 1 — Contexto del producto
Lee CLAUDE.md para entender el contexto actual del proyecto antes de hacer cualquier pregunta.

### Paso 2 — Preguntas de descubrimiento
Haz estas preguntas una por una, no todas juntas:
1. ¿Qué problema específico resuelve esta funcionalidad?
2. ¿Quién es el usuario principal? (owner / vet / ambos)
3. ¿Cómo se mide el éxito? (métrica concreta)
4. ¿Qué restricciones existen? (técnicas, médicas, legales)
5. ¿Qué está fuera del alcance?

### Paso 3 — Generar el PRD
Crea el archivo `docs/PRD.md` con esta estructura:
````markdown
# PRD: [Nombre de la Funcionalidad]

## Resumen Ejecutivo
[2-3 oraciones que expliquen qué es, para quién y por qué importa]

## Problema
[Descripción del problema que resuelve]

## Usuarios Afectados
- Rol: [owner / vet]
- Contexto de uso: [cuándo y dónde usan esto]

## Objetivos y Métricas
| Objetivo | Métrica | Meta |
|----------|---------|------|
| [objetivo] | [métrica] | [valor] |

## User Stories
[Formato: Como [rol], quiero [acción], para [beneficio]]

## Criterios de Aceptación (BDD)
```gherkin
Scenario: [nombre del escenario]
  Given [contexto inicial]
  When [acción del usuario]
  Then [resultado esperado]
```

## Restricciones y Reglas de Negocio
- [Restricción 1]
- [Restricción 2]

## Fuera del Alcance
- [Lo que NO incluye esta versión]

## Consideraciones de Seguridad
- [Datos sensibles involucrados]
- [Permisos requeridos]
- [Riesgos identificados]

## Dependencias
- [Otras features o servicios que necesita]
````

### Paso 4 — Validación
Pregunta: "¿Este PRD refleja correctamente lo que necesitas? ¿Hay algo que ajustar?"

## Reglas importantes
- Las restricciones nutricionales y de toxicidad SIEMPRE son no negociables en los criterios de aceptación
- Cada feature debe tener al menos un criterio de aceptación de seguridad
- Si la feature involucra datos médicos de mascotas, agregar sección de privacidad
