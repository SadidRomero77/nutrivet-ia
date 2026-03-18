---
name: aidlc-to-linear
description: Sincroniza las unidades de trabajo del AI-DLC de NutriVet.IA con Linear. Lee aidlc-docs/construction/, crea un Epic por unidad y un sub-issue por Paso (no por checkbox) con contexto completo que cumple Definition of Ready — objetivo, task list, ACs, dependencias y referencias.
tools: Read, Glob, mcp__linear__list_projects, mcp__linear__list_issues, mcp__linear__save_issue, mcp__linear__save_comment, mcp__linear__get_issue_status, mcp__linear__list_issue_statuses, mcp__linear__list_teams, mcp__linear__get_project
---

# Skill: aidlc-to-linear
> Versión: 2.0 — NutriVet.IA
> AI-DLC Construction Units → Linear Epics + Sub-issues con Definition of Ready

## Cuándo usar este skill

- Al terminar el diseño de una unidad y querer registrarla en Linear
- Al avanzar Pasos del Code Generation Plan y querer reflejar el progreso
- Para sincronizar sin duplicar issues existentes

**Input requerido**: nombre del proyecto en Linear (ej. `nutrivet-ia`)
Si no se proporciona, preguntar antes de continuar.

---

## Pre-requisitos

| Recurso | Verificar antes de empezar |
|---------|---------------------------|
| MCP Linear activo | Llamar `mcp__linear__list_teams` como prueba; si falla → detener y avisar |
| `aidlc-docs/construction/` | Debe existir con al menos una carpeta `unit-XX-*` |
| `aidlc-docs/aidlc-state.md` | Leer para saber el estado de cada fase |

---

## PASO 1 — Descubrir unidades por carpeta

Usar `Glob` con el patrón `aidlc-docs/construction/unit-*/` para listar todas las carpetas.

Patrón `unit-XX-{nombre}`:
- `unit-01-domain-core` → ID: `unit-01`, Nombre: `domain-core`
- `unit-02-auth-service` → ID: `unit-02`, Nombre: `auth-service`

Ignorar carpetas que no sigan el patrón `unit-\d{2}-*`.

---

## PASO 2 — Leer estado del AI-DLC

Leer `aidlc-docs/aidlc-state.md` y registrar por unidad:
- `✅ Completado` / `⬜ Pendiente` para: Functional Design · NFR Requirements · NFR Design · Infrastructure Design · Code Generation

---

## PASO 3 — Leer los 4 archivos relevantes por unidad

| Archivo | Extraer para... |
|---------|----------------|
| `functional-design/domain-entities.md` | Secciones `### Entidad` → nombre + 1 línea descripción |
| `functional-design/business-rules.md` | Secciones `### BR-XX:` → ID + descripción |
| `nfr-requirements/tech-stack-decisions.md` | Secciones `### Tecnología` → nombre de la decisión |
| `plans/unit-XX-{nombre}-code-generation-plan.md` | Todo — ver detalle abajo |

### Extracción completa del code-generation-plan

Leer el archivo completo y capturar:

**Cabecera del plan:**
- `## Objetivo` → párrafo completo (qué implementa esta unidad)
- `## Tiempo Estimado` → valor
- `## Dependencias` → lista de unidades previas requeridas

**Cuerpo — Pasos:**
Buscar todas las secciones `### Paso N — {Descripción del Paso}`.

Por cada Paso, extraer:
- **Número y título**: `N` y `{Descripción del Paso}`
- **Todos los checkboxes**:
  - `- [ ] texto` → tarea pendiente
  - `- [x] texto` → tarea completada
  - Sub-ítems con indentación (`  - texto`) → incluirlos como contexto del checkbox padre
- **Marcadores especiales**: si un checkbox tiene `— BLOQUEANTE` → anotarlo
- **Estado general del Paso**: Si TODOS los checkboxes son `[x]` → Paso Done. Si alguno es `[ ]` → Paso Todo.

**Pie del plan:**
- `## Criterios de Done` → lista completa (estos son los ACs del Epic)
- `## Referencias` → lista de links a ADRs, constitution, specs

---

## PASO 4 — Crear o actualizar en Linear

### 4.1 — Verificar si el Epic ya existe

Buscar en el proyecto Linear un issue cuyo título contenga el ID `[unit-XX]`.
- Existe → modo actualización (paso 4.4)
- No existe → modo creación (paso 4.2)

---

### 4.2 — Crear el Epic

**Título**: `[unit-XX] {nombre-unidad}`

**Descripción** (usar este template exacto):

```markdown
## Objetivo
{Párrafo completo del ## Objetivo del code-generation-plan}

## Entidades del dominio
- {NombreEntidad} — {descripción 1 línea}

## Reglas de negocio
- {BR-XX} — {descripción 1 línea}

## Stack
- {Tecnología/decisión clave}

## Criterios de Done (ACs del Epic)
- [ ] {AC 1 del ## Criterios de Done del plan}
- [ ] {AC 2}
- [ ] {AC N}

## Estado AI-DLC
| Fase                  | Estado |
|-----------------------|--------|
| Functional Design     | ✅ / ⏳ |
| NFR Requirements      | ✅ / ⏳ |
| NFR Design            | ✅ / ⏳ |
| Infrastructure Design | ✅ / ⏳ |
| Code Generation       | ✅ / ⏳ |

## Info
- Estimación: {Tiempo Estimado del plan}
- Dependencias: {Dependencias del plan o "Ninguna"}
- Specs: {Referencias del plan}
```

**Labels**: `aidlc-unit`

**Prioridad**:
- `unit-01` → Urgent
- `unit-02`, `unit-03` → High
- `unit-04` en adelante → Medium

---

### 4.3 — Crear sub-issues: UNO POR PASO (no uno por checkbox)

> **Regla fundamental**: cada sub-issue = un Paso completo del plan.
> Los checkboxes del Paso van dentro de la descripción como task list.
> Esto mantiene Linear manejable y cada issue cumple Definition of Ready.

Para cada `### Paso N — {Descripción}` extraído del plan:

**Título**: `[unit-XX · Paso N] {Descripción del Paso}`

Ejemplos:
- `[unit-01 · Paso 4] Tests RED — NRCCalculator`
- `[unit-01 · Paso 5] GREEN — Implementar NRCCalculator`
- `[unit-01 · Paso 14] Cobertura y Calidad`

**Descripción** (usar este template):

```markdown
## Qué hacer
{Todos los checkboxes del Paso como task list markdown, preservando sub-ítems}

- [ ] {checkbox 1}
  - {sub-ítem si existe}
- [ ] {checkbox 2} ⚠️ BLOQUEANTE {si tiene el marcador}
- [x] {checkbox completado}

## Criterios de Done (AC)
- [ ] Todos los ítems de la task list completados
- [ ] {AC específico derivado del nombre del paso}
  - Si el paso es "Tests RED": pytest confirma que TODOS los tests FALLAN (esperado — TDD)
  - Si el paso es "GREEN / Implementar": pytest confirma que los tests del paso anterior PASAN
  - Si el paso es "Cobertura y Calidad": cobertura ≥ 80%, ruff + bandit sin errores
  - Si el paso crea archivos: archivos existen en las rutas especificadas

## Contexto
- Unidad: [unit-XX] {nombre-unidad}
- Paso: {N} de {total de pasos}
- Depende de: Paso {N-1} completado {o "Sin dependencia — primer paso" si N=1}

## Referencias
{Lista del ## Referencias del plan, si existe}
- Plan completo: `aidlc-docs/construction/unit-XX-{nombre}/plans/unit-XX-{nombre}-code-generation-plan.md`
- Reglas: `.claude/rules/02-construction.md`
```

**Parent**: Epic de la unidad (creado en 4.2)

**Estado**:
- Todos los checkboxes del Paso son `[x]` → **Done**
- Al menos uno es `[ ]` → **Todo**

**Labels**: `paso-N` + tipo de paso:
- Paso contiene "Tests RED" o "Tests" → añadir label `tdd-red`
- Paso contiene "GREEN" o "Implementar" → añadir label `tdd-green`
- Paso contiene "Cobertura" o "Calidad" → añadir label `quality-gate`

---

### 4.4 — Modo actualización (Epic ya existe)

1. Releer el `code-generation-plan.md` actual.
2. Para cada Paso cuyo estado cambió a Done (todos los checkboxes en `[x]`):
   - Cambiar estado del sub-issue a **Done**
   - Agregar comentario: `Completado · {fecha ISO} · AI-DLC Code Generation`
3. Actualizar la tabla `## Estado AI-DLC` del Epic.
4. Actualizar los `## Criterios de Done` del Epic marcando los ACs que correspondan.

---

## PASO 5 — Reportar al usuario

```
✅ AI-DLC → Linear completado (v2.0 — Definition of Ready)

Proyecto: {nombre}

{unit-XX} {nombre}
  Epic:       #{id} — {creado / actualizado}
  Sub-issues: {N} Pasos creados ({M} Todo · {K} Done)
  ACs del Epic: {N} criterios de done registrados
  DoR check:  ✅ Objetivo · ✅ Task list · ✅ ACs · ✅ Dependencias · ✅ Referencias

Próximo paso:
  /aidlc-construction → ejecutar el plan
  Luego volver a este skill para sincronizar el avance.
```

---

## Definition of Ready — verificación por sub-issue

Antes de crear cada sub-issue, confirmar:

| Criterio DoR | Fuente en el plan |
|-------------|------------------|
| ✅ Contexto completo | Objetivo del plan + descripción del Paso |
| ✅ Criterios de aceptación | ACs derivados del tipo de paso (RED/GREEN/calidad) |
| ✅ Estructura Épica → Issue | Epic padre siempre creado primero |
| ✅ Sin ambigüedad | Task list con rutas de archivos y nombres de tests exactos |
| ✅ Links a specs | Referencias del plan + link al code-generation-plan |
| ✅ Scope definido | "Depende de Paso N-1" define qué está fuera del scope del issue |

---

## Restricciones

| ❌ Prohibido | ✅ Permitido |
|-------------|-------------|
| Un sub-issue por checkbox | Un sub-issue por Paso completo |
| Omitir Criterios de Done del plan | Siempre incluirlos como ACs del Epic |
| Omitir Referencias del plan | Siempre incluirlas en el sub-issue |
| Asumir ID de unidad desde H1 de archivos | Solo desde nombre de carpeta `unit-XX-{nombre}` |
| Modificar archivos en `aidlc-docs/` | Solo lectura |
| Crear duplicados si el Epic ya existe | Buscar primero, actualizar si existe |
| Crear sub-issues sin Epic padre | Epic primero siempre |

---

## Mapa de archivos por unidad

```
aidlc-docs/construction/
  unit-01-domain-core/
    functional-design/
      domain-entities.md       ← entidades para el Epic
      business-rules.md        ← reglas para el Epic
    nfr-requirements/
      tech-stack-decisions.md  ← stack para el Epic
    plans/
      unit-01-domain-core-code-generation-plan.md
        ├── ## Objetivo         → descripción del Epic
        ├── ## Criterios de Done → ACs del Epic
        ├── ## Dependencias     → info del Epic
        ├── ## Referencias      → links en sub-issues
        └── ### Paso N —        → un sub-issue por Paso
```
