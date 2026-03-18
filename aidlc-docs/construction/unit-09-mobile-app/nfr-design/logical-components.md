# Logical Components — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Mobile App

### GoRouter (Routing)
**Responsabilidad**: Routing declarativo con guards de autenticación.
**Configuración**:
```dart
final router = GoRouter(
  initialLocation: '/splash',
  redirect: (context, state) {
    final isAuth = ref.read(authProvider).isAuthenticated;
    if (!isAuth && !isPublicRoute(state.location)) return '/login';
    return null;
  },
  routes: [
    GoRoute(path: '/splash',           builder: (_,__) => SplashScreen()),
    GoRoute(path: '/login',            builder: (_,__) => AuthScreen()),
    GoRoute(path: '/register',         builder: (_,__) => RegisterScreen()),
    GoRoute(path: '/home',             builder: (_,__) => HomeScreen()),
    GoRoute(path: '/pets/wizard',      builder: (_,__) => PetWizardScreen()),
    GoRoute(path: '/pets/:id/plan',    builder: (_,s) => PlanScreen(petId: s.pathParameters['id']!)),
    GoRoute(path: '/pets/:id/chat',    builder: (_,s) => ChatScreen(petId: s.pathParameters['id']!)),
    GoRoute(path: '/pets/:id/scanner', builder: (_,s) => ScannerScreen(petId: s.pathParameters['id']!)),
    GoRoute(path: '/plans/:id',        builder: (_,s) => PlanDetailScreen(planId: s.pathParameters['id']!)),
  ],
);
```

### AuthProvider (Riverpod)
**Responsabilidad**: Gestión del estado de autenticación global.
**State**: `AuthState`
**Methods**: `login()`, `register()`, `logout()`, `refreshToken()`
**Persiste en**: `flutter_secure_storage` (tokens), Hive (user info básica)

### PetProvider (Riverpod)
**Responsabilidad**: Lista de mascotas del owner, CRUD.
**State**: `AsyncValue<List<PetModel>>`
**Methods**: `loadPets()`, `createPet()`, `updatePet()`

### WizardDraftProvider (Riverpod)
**Responsabilidad**: Estado del wizard step-by-step con persistencia en Hive.
**State**: `PetWizardDraft`
**Methods**: `updateField()`, `nextStep()`, `submit()`, `reset()`
**Persiste en**: Hive (draft sobrevive cierre de app)

### PlanProvider (Riverpod)
**Responsabilidad**: Generación de plan, polling, y estado del plan activo.
**State**: `PlanState`
**Methods**: `generatePlan()`, `pollJob()`, `loadPlan()`, `exportPlan()`

### ChatProvider (Riverpod)
**Responsabilidad**: Estado del chat con streaming SSE.
**State**: `ChatState`
**Methods**: `sendMessage()`, `loadHistory()`, `checkQuota()`
**Nota**: Gestiona el streaming buffer durante el typing effect.

### ScanProvider (Riverpod)
**Responsabilidad**: Estado del scanner de etiquetas.
**State**: `ScanState`
**Methods**: `pickImage()`, `submitScan()`, `reset()`

## Pantallas Principales (10 screens)

| Screen | Ruta | Provider |
|--------|------|----------|
| SplashScreen | /splash | AuthProvider |
| AuthScreen | /login | AuthProvider |
| RegisterScreen | /register | AuthProvider |
| HomeScreen | /home | PetProvider |
| PetWizardScreen | /pets/wizard | WizardDraftProvider |
| PlanSelectorScreen | /pets/:id/plan-selector | PlanProvider |
| PlanDetailScreen | /plans/:id | PlanProvider |
| ChatScreen | /pets/:id/chat | ChatProvider |
| ScannerScreen | /pets/:id/scanner | ScanProvider |
| WeightJourneyScreen | /pets/:id/weight | PetProvider |

## ApiClient — Endpoints Consumidos

```dart
// auth
POST /auth/register, /auth/login, /auth/refresh, /auth/logout

// pets
POST /pets, GET /pets, PATCH /pets/{id}, POST /pets/{id}/weight

// plans
POST /plans/generate, GET /plans/jobs/{id}, GET /plans/{id}, POST /plans/{id}/export

// agent chat
POST /agent/chat (SSE stream)

// scanner
POST /scanner/scan (multipart), GET /scanner/scans/{id}
```
