# Plan: Unit of Work Generation — Inception

**Fase AI-DLC**: PASO 5 — Units Generation
**Estado**: ✅ Completado
**Fecha**: 2026-03-10

---

## Objetivo

Descomponer la aplicación en unidades de trabajo implementables independientemente,
con dependencias claras y criterios de done verificables.

## Artefactos Producidos

| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| Unit specs (9 unidades) | `inception/units/unit-0{1-9}-*.md` | ✅ |
| Registro de unidades | `inception/application-design/unit-of-work.md` | ✅ |
| Matriz de dependencias | `inception/application-design/unit-of-work-dependency.md` | ✅ |
| Story map | `inception/application-design/unit-of-work-story-map.md` | ✅ |

## Criterios de Descomposición

Cada unidad cumple:
1. **Independencia**: puede ser implementada y testeada sin que otras unidades estén completas
2. **Responsabilidad única**: una unidad = una capa o feature cohesiva
3. **Criterios de done**: lista verificable de qué constituye "completado"
4. **Estimación**: rangos de días realistas basados en complejidad
5. **Contratos**: interfaces/APIs documentadas que otras unidades pueden consumir

## Decisiones de Descomposición

| Decisión | Justificación |
|---------|--------------|
| domain-core como unidad separada | Es la base; debe estar 100% antes de todo lo demás |
| agent-core antes de scanner/conversation | El orquestador LangGraph define el estado compartido |
| U-06/07/08 paralelizables | Después de U-05, no dependen entre sí |
| mobile-app al final | Consume todas las APIs — no puede anticiparse |
| auth antes que pet | Los roles (owner/vet) son prerequisito para el CRUD de mascotas |

## Estimación Total

- Mínimo: 55 días (equipo de 1 desarrollador full-stack)
- Máximo: 70 días (con revisiones y ajustes)
- Con paralelización (U-06/07/08): potencial reducción de 10-12 días
