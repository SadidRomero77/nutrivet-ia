# Deployment Architecture — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Deployment del Mobile App

```
App Stores
├── Apple App Store (iOS 15+)
│   └── Flutter release build (IPA) → App Store Connect → TestFlight (beta) → Public
└── Google Play Store (Android API 26+)
    └── Flutter release build (AAB) → Play Console → Internal track (beta) → Production
```

## Arquitectura de la App (Flutter)

```
lib/
├── main.dart                  ← entry point, ProviderScope, GoRouter init
├── app/
│   ├── router.dart            ← GoRouter con rutas y guards de auth
│   └── theme.dart             ← Material 3 theme
├── core/
│   ├── api/
│   │   ├── api_client.dart    ← Dio instance + interceptors
│   │   └── sse_client.dart    ← SSE streaming con Dio
│   ├── storage/
│   │   ├── hive_service.dart  ← Hive boxes
│   │   └── secure_storage.dart ← flutter_secure_storage
│   └── errors/
│       └── app_exception.dart
├── features/
│   ├── auth/
│   │   ├── providers/auth_provider.dart
│   │   └── screens/auth_screen.dart
│   ├── pets/
│   │   ├── providers/pet_provider.dart
│   │   ├── providers/wizard_draft_provider.dart
│   │   └── screens/
│   │       ├── pet_list_screen.dart
│   │       ├── wizard_screen.dart
│   │       └── bcs_selector_screen.dart
│   ├── plans/
│   │   ├── providers/plan_provider.dart
│   │   └── screens/
│   │       ├── plan_selector_screen.dart
│   │       ├── plan_loading_screen.dart
│   │       └── plan_screen.dart
│   ├── chat/
│   │   ├── providers/chat_provider.dart
│   │   └── screens/chat_screen.dart
│   └── scanner/
│       ├── providers/scan_provider.dart
│       └── screens/scanner_screen.dart
└── shared/
    └── widgets/               ← componentes reutilizables
```

## Backend API URL

```dart
// core/api/api_client.dart
const String kBackendUrl = String.fromEnvironment(
  'BACKEND_URL',
  defaultValue: 'https://api.nutrivetia.com',
);
// Build: flutter build apk --dart-define=BACKEND_URL=https://api.nutrivetia.com
```

## CI/CD Mobile

```yaml
# GitHub Actions
- flutter test
- flutter analyze
- flutter build apk --release (Android)
- flutter build ipa --release (iOS, en macOS runner)
```
