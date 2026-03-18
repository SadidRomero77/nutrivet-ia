# Business Logic Model — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos de la App Mobile (Flutter)

### Flujo 1: Auth — Registro y Login

```
Pantalla: AuthScreen
  ↓
Usuario ingresa email + password + role
  ↓
AuthNotifier.login(email, password)
  ↓
ApiClient.post("/auth/login") → AuthToken
  ↓
flutter_secure_storage.write("access_token", token)
flutter_secure_storage.write("refresh_token", refresh)
HiveService.saveUserSession(user_id, role, tier)
  ↓
GoRouter.go("/home")
```

### Flujo 2: Wizard de Mascota (6 Pasos)

```
Pantalla: PetWizardScreen (6 steps)
  ↓
Paso 1: nombre + especie + raza
Paso 2: sexo + edad + peso
Paso 3: talla (solo perros) + estado reproductivo
Paso 4: nivel actividad + BCS (selector visual 9 siluetas)
Paso 5: condiciones médicas (multi-select 13 condiciones)
Paso 6: alergias + alimentación actual
  ↓ (en cada paso)
WizardDraftNotifier.updateDraft(field, value)
HiveService.saveDraft(draft)  ← persistencia local
  ↓ (al finalizar paso 6)
Si draft.isComplete:
  ApiClient.post("/pets", draft) → PetProfile
  HiveService.clearDraft()
  GoRouter.go("/pets/{pet_id}/plan-selector")
Si no: deshabilitar botón "Continuar"
```

### Flujo 3: Generación de Plan

```
Pantalla: PlanSelectorScreen → PlanLoadingScreen → PlanScreen
  ↓
Usuario selecciona modalidad (natural / concentrado)
  ↓
PlanNotifier.generatePlan(pet_id, modalidad)
  ↓
ApiClient.post("/plans/generate") → { job_id }
  ↓
Iniciar polling timer (cada 3s):
  ApiClient.get("/plans/jobs/{job_id}")
    → status="queued"/"processing": mostrar loader
    → status="completed": cargar plan + GoRouter.go("/plans/{plan_id}")
    → status="failed": mostrar error + opción de reintentar
  Timeout 60s: mostrar "Puede tardar un poco más — recibirás notificación"
  ↓
PlanScreen:
  Mostrar 5 secciones del plan
  Mostrar RER/DER
  Si PENDING_VET: banner "Pendiente de revisión veterinaria"
  Si ACTIVE: botón "Exportar PDF" + botón "Compartir"
  Disclaimer al final (siempre visible)
```

### Flujo 4: Chat SSE

```
Pantalla: ChatScreen
  ↓
Usuario escribe mensaje → botón Enviar
  ↓
ChatNotifier.sendMessage(pet_id, message)
  ↓
1. Agregar mensaje del usuario a la lista (optimistic UI)
2. Verificar quota: si upgrade_required → dialog de upgrade, STOP
3. Iniciar SSE request:
   ApiClient.streamPost("/agent/chat", {pet_id, message})
   → EventSource (Dio stream)
4. Por cada chunk:
   chatState.streamingBuffer += chunk
   UI rebuildea con buffer visible (typing effect)
5. Al recibir done:
   chatState.messages.add(AssistantMessage(streamingBuffer))
   chatState.streamingBuffer = ''
6. Persistir en Hive (offline cache)
```

### Flujo 5: Scanner

```
Pantalla: ScannerScreen
  ↓
1. Usuario elige: cámara o galería
2. Seleccionar tipo: "Tabla nutricional" / "Lista de ingredientes"
3. Si imagen > 10MB → redimensionar con flutter_image_compress
4. ScanNotifier.submitScan(pet_id, image, imageType)
   ApiClient.postMultipart("/scanner/scan") → { scan_id, semaphore, findings }
5. Mostrar resultado:
   - Semáforo (verde/amarillo/rojo) con icono grande
   - Lista de findings
   - Texto de recomendación
   - Si RED: alerta prominente
```
