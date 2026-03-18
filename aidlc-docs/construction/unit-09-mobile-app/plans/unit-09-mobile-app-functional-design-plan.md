# Plan: Functional Design — Unit 09: mobile-app

**Unidad**: unit-09-mobile-app
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio de la app móvil Flutter: 10 pantallas, offline-first con
Hive, Riverpod para state management, GoRouter para navegación por rol, y patrones
de UX para wizard, SSE streaming, polling y HITL.

## Pantallas — 10 Screens

| Screen | Descripción | Acceso |
|--------|-------------|--------|
| `AuthScreen` | Login + registro (tabs) | Público |
| `WizardScreen` | 6 pasos — 13 campos PetProfile | Owner |
| `ClinicPetWizardScreen` | Wizard para crear ClinicPet (con owner_name + phone) | Vet |
| `PlanScreen` | 5 secciones colapsables ADR-020 | Owner + Vet |
| `ChatScreen` | SSE streaming ADR-021 + cuota Free | Owner |
| `OCRScreen` | Cámara + guía nutricional + semáforo | Owner |
| `DashboardScreen` | Gráficas de peso/BCS (fl_chart) | Owner |
| `VetDashboardScreen` | Lista PENDING_VET primero + HITL approve/return | Vet |
| `UpgradeGateScreen` | Modal con opciones Básico/Premium | Owner |
| `ClaimCodeScreen` | Ingreso de código para reclamar ClinicPet | Owner |

## Offline-First con Hive

| Dato | Hive Box | TTL |
|------|----------|-----|
| JWT tokens | `auth_box` (encrypted) | Según JWT expiry |
| Wizard draft | `wizard_box` | Hasta completar + 7 días |
| Plan activo | `plan_box` | 7 días |
| Historial chat | `chat_box` | Últimos 50 mensajes |
| Historial peso | `weight_box` | 90 días |

**Regla offline**: Plan y chat son legibles sin red. Write operations requieren red — mostrar indicador.

## WizardScreen — 6 Pasos

```
Paso 1: Nombre + Especie + Raza
  - Al seleccionar "gato" → ocultar campo Talla en paso 3
  - Selector de especie con iconos

Paso 2: Sexo + Edad + Peso
  - Edad: selector meses/años con toggle
  - Peso: teclado numérico decimal

Paso 3: Talla (SOLO si especie == "perro") + Estado Reproductivo
  - Si especie == "gato" → step 3 muestra solo Estado Reproductivo

Paso 4: Nivel de Actividad + BCS
  - Actividad: opciones diferentes según especie (perros vs gatos)
  - BCS: selector visual 1-9 con imágenes de silueta

Paso 5: Antecedentes Médicos + Alergias
  - Multi-select chips con los 13 + "Ninguno conocido"
  - Campo libre para alergias adicionales

Paso 6: Alimentación Actual
  - "¿Qué come hoy tu mascota?"
  - Opciones: concentrado / natural / mixto
```

**Draft**: `WizardNotifier` guarda cada paso en Hive automáticamente.
Draft persiste si el usuario cierra la app sin completar.

## PlanScreen — 5 Secciones Colapsables

```
Sección 1: Resumen Nutricional → SIEMPRE EXPANDIDA al abrir
Sección 2: Plan Semanal → tabs Lun/Mar/Mié/Jue/Vie/Sáb/Dom
Sección 3: Instrucciones de Preparación → colapsable
Sección 4: Protocolo de Transición → colapsable (visible solo si has_transition_protocol)
Sección 5: Sustitutos Aprobados → colapsable

Estado PENDING_VET: badge visible + mensaje "En revisión veterinaria"
Botón exportar PDF: visible solo si status == ACTIVE
```

**Polling job_id**: `PlanNotifier` hace polling cada 3s durante máximo 60s
(20 intentos) con barra de progreso visible al usuario.

## ChatScreen — SSE Streaming

```
StreamBuilder: muestra tokens progressivamente (fade-in animation)
Typing indicator: tres puntos animados mientras llega el primer token
Chips de sugerencias: 3-4 preguntas frecuentes en pantalla inicial

Free tier UX:
  - Contador visible: "3 de 3 preguntas hoy" / "7 de 9 preguntas totales"
  - Al alcanzar límite: UpgradeGateScreen modal automático
```

## VetDashboardScreen — HITL

```
Lista de planes ordenada: PENDING_VET primero, luego ACTIVE
Para cada plan PENDING_VET:
  - Nombre del pet (species + breed)
  - Condiciones médicas del pet
  - Botón "Revisar" → abre PlanScreen con opciones HITL

HITL en PlanScreen (modo vet):
  - Botón "Aprobar": abre DatePicker si plan temporal_medical
  - Botón "Devolver": abre TextInput para comentario obligatorio
  - Comentario vacío → botón Devolver deshabilitado
```

## OCRScreen — Guía de Cámara

```
Overlay de guía: rectángulo con instrucción "Encuadra la tabla nutricional"
Al tomar foto: validación automática (ImageValidator)
  → Si rechazada: snackbar con instrucción "Fotografía la tabla nutricional"
  → Si aceptada: muestra semáforo con detalle de problemas detectados
```

## Casos de Prueba Críticos (Widget Tests)

- [ ] `wizard_talla_oculta_gato` — especie gato → campo talla no visible
- [ ] `wizard_draft_hive` — salir a paso 3 + volver → draft restaurado
- [ ] `plan_polling_shows_plan` — mock job READY → PlanScreen visible
- [ ] `chat_quota_free` — 3 preguntas enviadas → cuarta deshabilitada
- [ ] `chat_upgrade_gate` — cuota agotada → UpgradeGateScreen modal
- [ ] `ocr_semaforo_rojo` — resultado rojo → UI muestra rojo + razón
- [ ] `vet_pending_vet_primero` — PENDING_VET plans al tope de la lista

## Referencias

- Spec: `aidlc-docs/inception/units/unit-09-mobile-app.md`
- ADR-020: estructura 5 secciones del plan
- ADR-021: SSE streaming
- Domain: `_shared/domain-entities.md` (13 campos PetProfile)
