# Plan: Code Generation — Unit 09: mobile-app

**Unidad**: unit-09-mobile-app
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar la app móvil Flutter completa: 10 pantallas, offline-first con Hive,
Riverpod state management, GoRouter, SSE streaming, polling y HITL veterinario.
Todos los 21 user stories cubiertos.

**Estructura**: Feature-first Dart packages (`lib/features/`).

---

## Pasos de Implementación

### Paso 1 — pubspec.yaml con Todas las Dependencias

- [ ] Crear `mobile/pubspec.yaml`:
  ```yaml
  dependencies:
    flutter_riverpod: ^2.5.1
    riverpod_annotation: ^2.3.5
    go_router: ^14.2.0
    dio: ^5.4.3
    hive_flutter: ^1.1.0
    image_picker: ^1.1.2
    fl_chart: ^0.68.0
    share_plus: ^10.0.0
    permission_handler: ^11.3.1
    flutter_secure_storage: ^9.2.2
    http: ^1.2.1
    flutter_animate: ^4.5.0
    cached_network_image: ^3.3.1
    crypto: ^3.0.3
    intl: ^0.19.0

  dev_dependencies:
    flutter_test:
    riverpod_generator: ^2.4.3
    build_runner: ^2.4.11
    mocktail: ^1.0.4
  ```

### Paso 2 — Core: API Client, Router, Hive, Theme

- [ ] `lib/core/api_client.dart` — Dio + JwtRefreshInterceptor + baseUrl por flavor
- [ ] `lib/core/api_endpoints.dart` — constantes de endpoints
- [ ] `lib/core/hive_service.dart` — inicialización + boxes por feature
- [ ] `lib/core/app_router.dart` — GoRouter con guards por rol:
  ```dart
  // Rutas protegidas:
  /home → owner (redirect a /auth si no autenticado)
  /vet  → vet (redirect a /auth si no autenticado o no es vet)
  /auth → público (redirect a /home si ya autenticado)
  ```
- [ ] `lib/core/app_theme.dart` — ThemeData con colores de NutriVet.IA

### Paso 3 — Feature: Auth

- [ ] `lib/features/auth/data/auth_data_source.dart` — POST /v1/auth/login, register, refresh
- [ ] `lib/features/auth/application/auth_notifier.dart` — Riverpod StateNotifier
- [ ] `lib/features/auth/presentation/auth_screen.dart` — tabs login + registro
  - Login: email + password + botón
  - Registro: email + password + confirm + rol selector
  - Error handling: 401 → "Credenciales incorrectas"

### Paso 4 — Feature: Pet / Wizard

- [ ] `lib/features/pet/data/pet_data_source.dart` — CRUD pets + claim
- [ ] `lib/features/pet/application/pet_notifier.dart`
- [ ] `lib/features/pet/application/wizard_notifier.dart` — draft en Hive
- [ ] `lib/features/pet/presentation/wizard_screen.dart`:
  - 6 steps con PageView
  - Paso 3: campo `talla` OCULTO si `species == "gato"`
  - Paso 4: opciones de `activity_level` según especie
  - Paso 4: BCS selector visual con 9 imágenes de silueta
  - Draft guardado en Hive en cada cambio
- [ ] `lib/features/pet/presentation/clinic_pet_wizard_screen.dart` (vet only)
- [ ] `lib/features/pet/presentation/claim_code_screen.dart` — input + submit

### Paso 5 — Feature: Plan

- [ ] `lib/features/plan/data/plan_data_source.dart` — generate, get, poll, HITL
- [ ] `lib/features/plan/application/plan_notifier.dart`:
  - Polling: cada 3s, máx 60s, progreso visible
  - Cache: leer de Hive primero, actualizar desde backend
- [ ] `lib/features/plan/presentation/plan_screen.dart`:
  - 5 `ExpansionTile` colapsables
  - Sección 1: SIEMPRE expandida al abrir
  - Sección 2: `TabBar` Lun/Mar/Mié/Jue/Vie/Sáb/Dom
  - Sección 4: visible solo si `has_transition_protocol == true`
  - Badge PENDING_VET: chip naranja visible
  - Botón "Exportar PDF": visible solo si `status == ACTIVE`
  - Disclaimer: texto pequeño al pie de la pantalla

### Paso 6 — Feature: Agent / Chat

- [ ] `lib/features/agent/data/chat_data_source.dart` — SSE via http package
- [ ] `lib/features/agent/application/chat_notifier.dart`:
  - Stream de tokens via SSE
  - Historial de Hive (últimos 50 por pet)
  - Contador de cuota Free visible
- [ ] `lib/features/agent/presentation/chat_screen.dart`:
  - `StreamBuilder` para tokens progresivos con fade-in animation
  - Typing indicator (tres puntos) mientras espera primer token
  - Chips de preguntas frecuentes
  - Contador "X de 3 preguntas hoy" para Free tier
  - Disclaimer en cada respuesta del agente

### Paso 7 — Feature: Scanner / OCR

- [ ] `lib/features/scanner/data/scanner_data_source.dart` — multipart upload
- [ ] `lib/features/scanner/application/scanner_notifier.dart`
- [ ] `lib/features/scanner/presentation/ocr_screen.dart`:
  - `image_picker` para cámara
  - Overlay con guía rectangular y texto instrucción
  - Resultado: semáforo verde/amarillo/rojo con detalle de problemas
  - Si rechazada: snackbar con instrucción

### Paso 8 — Feature: Dashboard

- [ ] `lib/features/dashboard/data/dashboard_data_source.dart` — historial peso
- [ ] `lib/features/dashboard/application/dashboard_notifier.dart`
- [ ] `lib/features/dashboard/presentation/dashboard_screen.dart`:
  - `LineChart` de fl_chart para peso vs tiempo
  - `BarChart` de fl_chart para BCS vs tiempo
  - Datos de `weight_box` Hive + actualización desde backend

### Paso 9 — Feature: Vet Dashboard

- [ ] `lib/features/vet/data/vet_data_source.dart` — GET /v1/vet/plans/pending + approve/return
- [ ] `lib/features/vet/application/vet_notifier.dart`
- [ ] `lib/features/vet/presentation/vet_dashboard_screen.dart`:
  - Lista: PENDING_VET primero (ordenado por fecha)
  - Cada card: pet info + condiciones + botón "Revisar"
  - Al aprobar plan temporal_medical: DatePicker para review_date
  - Al devolver: TextFormField para comentario obligatorio (botón deshabilitado si vacío)

### Paso 10 — Feature: Freemium / Upgrade Gate

- [ ] `lib/features/freemium/presentation/upgrade_gate_screen.dart`:
  - Modal bottom sheet
  - Opciones: Básico ($29.900 COP/mes) y Premium ($59.900 COP/mes)
  - Trigger: automático cuando cuota Free agotada

### Paso 11 — Widget Tests (7 Tests Obligatorios)

- [ ] `test/widget/wizard_talla_oculta_gato_test.dart`
  - Crear WizardScreen con especie "gato" → verificar que `SizeSelector` no existe en árbol
- [ ] `test/widget/wizard_draft_hive_test.dart`
  - Completar 2 pasos → dispose → recrear → verificar que draft se restauró
- [ ] `test/widget/plan_polling_shows_plan_test.dart`
  - Mock `PlanDataSource` retorna READY en 2do poll → verificar `PlanScreen` visible
- [ ] `test/widget/chat_quota_free_test.dart`
  - Mock cuota Free 3/3 → verificar que input deshabilitado + upgrade gate visible
- [ ] `test/widget/chat_upgrade_gate_test.dart`
  - Mock cuota agotada → verificar `UpgradeGateScreen` aparece como modal
- [ ] `test/widget/ocr_semaforo_rojo_test.dart`
  - Mock scan result `semaphore: "rojo"` → verificar icono rojo + texto razón
- [ ] `test/widget/vet_pending_vet_primero_test.dart`
  - Mock lista con ACTIVE + PENDING_VET → verificar PENDING_VET es el primero

### Paso 12 — Integration Test

- [ ] `integration_test/full_flow_test.dart`:
  - Registro de usuario owner
  - Completar wizard (6 pasos, mascota sana)
  - Esperar plan generado (polling)
  - Enviar mensaje al agente
  - Verificar respuesta recibida

---

## Criterios de Done

- [ ] Los 21 user stories cubiertos (verificar contra `inception/units/unit-09-mobile-app.md`)
- [ ] Plan y chat legibles offline (prueba en modo avión)
- [ ] SSE streaming funcional (primer token < 1s)
- [ ] HITL flow completo para vet (approve + return con comentario)
- [ ] Todos los backends integrados (auth, pet, plan, agent, scanner, export)
- [ ] 7 widget tests pasando
- [ ] Integration test pasando
- [ ] JWT en flutter_secure_storage (no SharedPreferences)
- [ ] Disclaimer visible en PlanScreen y ChatScreen

## Tiempo Estimado

10-14 días (10 pantallas + offline-first + SSE + TDD widget tests)

## Dependencias

- Todos los backends (units 01-08) deben estar listos para integration test
- Staging environment de Hetzner activo

## Referencias

- Unit spec: `inception/units/unit-09-mobile-app.md`
- ADR-020: estructura 5 secciones del plan
- ADR-021: SSE streaming
- Constitution: REGLA 8 (disclaimer en toda vista del plan)
