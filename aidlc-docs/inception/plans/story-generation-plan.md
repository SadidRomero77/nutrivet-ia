# Plan: Story Generation — Inception

**Fase AI-DLC**: PASO 2 — User Stories
**Estado**: ✅ Completado
**Fecha**: 2026-03-10

---

## Objetivo

Generar personas y user stories INVEST-compliant para NutriVet.IA.
Sistema multi-persona: owner + vet + agente IA.

## Artefactos Producidos

| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| Personas (3) | `inception/user-stories/personas.md` | ✅ |
| User Stories (21) | `inception/user-stories/stories.md` | ✅ |

## Personas

| Persona | Rol | Segmento |
|---------|-----|---------|
| Valentina | Owner primaria | Perro con condición médica — ICP Segmento A |
| Dr. Andrés | Vet adoptante temprano | BAMPYSVET — primer vet del piloto |
| Carolina | Owner secundaria | Mascota sana, busca optimización |

## Épicas y Stories

| Épica | Stories | Criterio |
|-------|---------|---------|
| Epic 1: Identidad | US-01, US-02, US-03 | Login owner y vet |
| Epic 2: Mascota | US-04, US-05 | Wizard 13 campos + peso |
| Epic 3: Plan | US-06, US-07, US-08 | Generación natural/concentrado |
| Epic 4: HITL | US-09, US-10 | Aprobación veterinaria |
| Epic 5: Agente | US-11, US-12 | Chat nutricional |
| Epic 6: Scanner | US-13 | OCR etiqueta |
| Epic 7: Export | US-14, US-15 | PDF + share |
| Epic 8: Dashboard | US-16, US-17 | Seguimiento owner/vet |
| Epic 9: Freemium | US-18, US-19 | Gates de conversión |
| ClinicPet | US-20, US-21 | Flujo clínico |

## Cobertura INVEST

Todas las stories verificadas como:
- **Independent**: cada una es implementable sola (excepto dependencias de datos)
- **Negotiable**: scope ajustable sin romper el valor central
- **Valuable**: cada story entrega valor al usuario
- **Estimable**: estimación posible basada en unidades de trabajo
- **Small**: cada story cabe en 1 unidad de trabajo
- **Testable**: todas tienen criterios de aceptación y escenarios Gherkin en `behaviors/`
