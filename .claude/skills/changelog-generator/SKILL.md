---
name: changelog-generator
description: Genera y actualiza CHANGELOG.md de NutriVet.IA desde el historial de commits y PRs. Produce dos versiones (técnica y producto), determina la versión SemVer automáticamente, y alerta cuando un cambio requiere validación de Lady Carolina o dispara evals.
tools: Read, Write, Edit, Bash, Glob
---

# Skill: changelog-generator
> Versión: 2.0 — NutriVet.IA
> Estándar: Keep a Changelog + Conventional Commits + SemVer

## Cuándo activar

- Al cerrar un sprint o milestone
- Antes de cada release (Quality Gates deben estar en verde primero)
- Cuando `CHANGELOG.md` no existe o está desactualizado
- Para generar resumen de cambios para Lady Carolina o Dr. Andrés

---

## Pre-requisitos

| Recurso | Cómo acceder |
|---------|-------------|
| Historial de commits | `git log` via Bash |
| PRs cerrados | MCP GitHub si está activo |
| `CHANGELOG.md` actual | Leer si existe — si no, crear desde cero |
| `aidlc-docs/aidlc-state.md` | Para contexto de fase actual |

---

## PASO 1 — Determinar el rango de cambios

Elegir una de estas opciones en orden de preferencia:

**Opción A — Desde el último tag** (preferida):
```bash
git tag --sort=-version:refname | head -1
git log {último-tag}..HEAD --pretty=format:"%h|%ad|%an|%s" --date=short --no-merges
```

**Opción B — Rango manual** (si el usuario lo especifica):
```bash
git log --since="{fecha}" --pretty=format:"%h|%ad|%an|%s" --date=short --no-merges
```

**Opción C — Todo el historial** (primera vez, si no existe `CHANGELOG.md`):
```bash
git log --pretty=format:"%h|%ad|%an|%s" --date=short --no-merges
```

Si el repositorio no tiene commits aún → informar al usuario y detener.
Documentar el rango usado al inicio del proceso.

---

## PASO 2 — Recopilar y clasificar commits

Construir una lista con: hash corto · fecha · autor · mensaje.

Asignar cada commit a **una** categoría según el prefijo del mensaje:

| Prefijo del commit | Categoría | Emoji |
|-------------------|-----------|-------|
| `feat:` | Nuevas Funcionalidades | ✨ |
| `fix:` | Correcciones | 🐛 |
| `security:` | Seguridad | 🔒 |
| `perf:` | Rendimiento | ⚡ |
| `docs:` | Documentación | 📚 |
| `chore:` | Mantenimiento | 🔧 |
| `BREAKING CHANGE:` | Cambios Incompatibles | 💥 |
| `clinical:` | Cambios Clínicos | 🏥 |
| `agent:` | Agente / LLM | 🤖 |
| `refactor:` | Refactoring | 🔄 |

**Categorías propias de NutriVet.IA** — no omitirlas nunca:
- `clinical:` → cambios en `TOXIC_DOGS`, `TOXIC_CATS`, `RESTRICTIONS_BY_CONDITION`, RER/DER, condiciones médicas
- `agent:` → cambios en LangGraph, prompts, LLM routing, tools del agente

**Omitir siempre:**
- Merges automáticos (`Merge branch...`, `Merge pull request...`)
- Commits de solo whitespace, typos sin impacto funcional
- `wip:` sin contenido de producto

**Fallback si un commit no tiene prefijo Conventional Commits:**
Inferir la categoría por palabras clave en el mensaje. Usar `🔧 Mantenimiento` como último recurso.

---

## PASO 3 — Detectar alertas de acción requerida

Antes de escribir el changelog, revisar si algún commit activa una alerta:

| Si el commit toca... | Alerta a incluir |
|---------------------|-----------------|
| `toxic_foods.py`, `TOXIC_DOGS`, `TOXIC_CATS` | `⚠️ Requiere validación Lady Carolina (Regla 1)` |
| `medical_restrictions.py`, `RESTRICTIONS_BY_CONDITION` | `⚠️ Requiere validación Lady Carolina (Regla 2)` |
| `nrc_calculator.py`, RER/DER | `⚠️ Verificar Golden Case Sally ±0.5 kcal (G8)` |
| Prompts del agente, LLM routing, tools LangGraph | `⚠️ Disparar eval-runner antes del siguiente release` |
| Endpoints de auth, JWT, RBAC | `⚠️ Ejecutar security-checker` |
| Schema de base de datos | `⚠️ Migración Alembic requerida — confirmar con Sadid` |

Estas alertas se muestran al usuario **antes** de escribir el archivo, y también se incluyen en el changelog como notas bajo el ítem correspondiente.

---

## PASO 4 — Determinar la versión SemVer

**Si ya existe `CHANGELOG.md`:**
Leer la versión más reciente registrada. Proponer la siguiente según:

| Tipo de cambios presentes | Incremento |
|--------------------------|-----------|
| `💥 BREAKING CHANGE` | MAJOR (`1.0.0 → 2.0.0`) |
| `✨ feat` o `🏥 clinical` o `🤖 agent` | MINOR (`0.1.0 → 0.2.0`) |
| Solo `🐛 fix`, `📚 docs`, `🔧 chore`, `⚡ perf` | PATCH (`0.1.1 → 0.1.2`) |
| Solo `🔒 security` | PATCH mínimo, con nota urgente |

Mostrar la propuesta al usuario antes de escribir. Si el usuario ajusta la versión, respetar su decisión.

**Si NO existe `CHANGELOG.md`:**
Usar `v0.1.0` como versión inicial. Indicar que puede ajustarse.

---

## PASO 5 — Escribir el CHANGELOG.md

### Reglas de escritura

- Las versiones más recientes van **arriba** (primero la nueva entrada)
- No modificar entradas de versiones ya publicadas — solo agregar nuevas al tope
- Cada ítem: verbo en infinitivo o pasado en español, impacto de producto, no detalle técnico
- Referenciar PR o story si está disponible: `(US-04)`, `(#12)`
- Máximo 1 línea por ítem — sub-ítem con 2 espacios de indentación si necesita más

```
❌ fix: null pointer in nrc_calculator.py line 42
✅ Corregido error que impedía calcular RER para mascotas con peso < 1 kg
```

### Formato del archivo

```markdown
# Changelog — NutriVet.IA

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.0.0/)
Versionado: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

> Cambios en progreso sin versión asignada aún.

---

## [v0.2.0] — 2026-03-17

### ✨ Nuevas Funcionalidades
- Agregado wizard de perfil de mascota con 13 campos obligatorios y selector visual BCS. (US-04)
- Implementado cálculo RER/DER determinista en `nrc_calculator.py` — nunca delegado al LLM. (US-08)

### 🏥 Cambios Clínicos
- Agregadas restricciones hard-coded para condición "cistitis/enfermedad_urinaria".
  > ⚠️ Validado por Lady Carolina Castañeda (MV) — 2026-03-16

### 🤖 Agente / LLM
- Implementado routing LLM: Free → llama-3.3-70b · Básico → gpt-4o-mini · Premium → claude-sonnet-4-5.
- Override clínico: 3+ condiciones médicas siempre usa claude-sonnet-4-5.
  > ⚠️ eval-runner ejecutado — todos los jobs en verde

### 🔒 Seguridad
- JWT access tokens limitados a 15 min con refresh rotativo.
- CORS configurado explícitamente — sin wildcard en staging/prod.

### 🐛 Correcciones
- Corregido error que permitía BCS fuera del rango 1-9 sin lanzar excepción de dominio.

### 📚 Documentación
- AI-DLC Construction completado para unit-01-domain-core (9 unidades planificadas).

### 🔧 Mantenimiento
- Migración Alembic v001 — tablas iniciales: users, pets, plans, agent_traces.

---

## [v0.1.0] — 2026-03-10

### ✨ Nuevas Funcionalidades
- PRD v2.0 consolidado con 13 segmentos y modelo freemium definido.
- AI-DLC Inception completada: 9 unidades de trabajo, 9 features de behaviors.
- Golden Case Sally definido y validado clínicamente (RER ≈ 396 kcal · DER ≈ 534 kcal/día).

---

[Unreleased]: https://github.com/sadid-romero/nutrivet-ai/compare/v0.2.0...HEAD
[v0.2.0]: https://github.com/sadid-romero/nutrivet-ai/compare/v0.1.0...v0.2.0
[v0.1.0]: https://github.com/sadid-romero/nutrivet-ai/releases/tag/v0.1.0
```

---

## PASO 6 — Generar versión de producto

Además de `CHANGELOG.md` (versión técnica), generar un resumen en lenguaje de producto sin jerga técnica. Mostrar al usuario para que pueda compartirlo con Lady Carolina o Dr. Andrés.

Formato del resumen de producto:

```
📋 Resumen de cambios — NutriVet.IA v{X.Y.Z}
Fecha: {fecha}

Qué hay de nuevo:
  • {Descripción en lenguaje de usuario — sin mencionar código}
  • ...

Correcciones:
  • {Bug corregido en lenguaje de impacto al usuario}

Notas clínicas:
  • {Solo si hay cambios en restricciones, toxicidad, o cálculos — con validación}

Estado del proyecto:
  • Fase AI-DLC: {leer de aidlc-state.md}
  • Quality Gates: {estado G1-G8 si aplica}
```

---

## PASO 7 — Verificar antes de finalizar

- [ ] La versión nueva es mayor que la versión anterior en el archivo
- [ ] Todas las categorías usadas tienen al menos 1 ítem
- [ ] No hay commits duplicados ni merges triviales
- [ ] Los ítems están en español de producto (no mensajes crudos de commit)
- [ ] Las alertas de acción requerida están incluidas en los ítems correspondientes
- [ ] Los links de comparación al final del archivo son correctos

---

## PASO 8 — Reportar al usuario

```
✅ CHANGELOG.md actualizado — NutriVet.IA

Nueva versión: v{X.Y.Z} — {fecha}
Commits procesados: {N}
Commits omitidos (triviales): {N}

Categorías:
  ✨ Nuevas Funcionalidades: {N}
  🏥 Cambios Clínicos: {N}
  🤖 Agente / LLM: {N}
  🔒 Seguridad: {N}
  🐛 Correcciones: {N}
  📚 Documentación: {N}
  🔧 Mantenimiento: {N}

⚠️ Acciones requeridas antes del siguiente release:
  {lista de alertas detectadas, o "Ninguna"}

Resumen de producto generado para Lady Carolina / Dr. Andrés:
  {resumen listo para copiar y compartir}
```

---

## Restricciones

| ❌ Prohibido | ✅ Permitido |
|-------------|-------------|
| Copiar mensajes crudos de commit | Reescribir en lenguaje de producto |
| Incluir merges automáticos | Solo commits con contenido real |
| Bajar la versión respecto a la anterior | SemVer siempre ascendente |
| Modificar entradas de versiones ya publicadas | Solo agregar nuevas al tope |
| Inventar cambios fuera del historial | Solo lo que está en commits o PRs |
| Omitir alertas clínicas cuando aplican | Siempre incluirlas si el commit toca dominio clínico |
| Usar inglés en los ítems del changelog | Español en ítems (nombres técnicos de código sí) |
