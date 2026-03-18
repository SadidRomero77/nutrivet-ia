# Tech Stack Decisions — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Decisiones de Stack para Mobile App

### Flutter 3.22+ con Dart 3
**Decisión**: Flutter 3.22+ con Dart 3 (null safety estricto).
**Razón**: Un solo codebase para iOS y Android. Performance nativa con Skia/Impeller. Dart 3 con null safety elimina una clase entera de runtime errors. Riverpod y go_router están optimizados para Flutter 3.x.
**Alternativas rechazadas**: React Native (puentes JS, menor performance en listas largas), Kotlin Multiplatform (menos maduro para UI compartida), nativo (doble codebase — sin equipo suficiente).

### Riverpod 2.x para State Management
**Decisión**: `flutter_riverpod==2.5.x` para gestión de estado global.
**Razón**: Type-safe, testeable, sin BuildContext en providers. Mejor que BLoC para equipos pequeños (menos boilerplate). Mejor que Provider (más potente, manejo de async nativo con `AsyncValue`).
**Alternativas rechazadas**: BLoC (demasiado boilerplate para MVP), GetX (acoplamiento excesivo), MobX (reactividad implícita difícil de debuggear).

### Dio 5.x para HTTP
**Decisión**: `dio==5.4.x` como cliente HTTP.
**Razón**: Soporte nativo para interceptors (JWT refresh automático), streaming (SSE para chat), multipart (scanner), y cancel tokens. Más ergonómico que `http` package para estos casos de uso.

### GoRouter 13.x para Routing
**Decisión**: `go_router==13.x` para routing declarativo.
**Razón**: Deep linking nativo, guards de autenticación declarativos, URLs web-compatible (útil si se agrega web app en el futuro). Mantenido por el equipo de Flutter.
**Alternativas rechazadas**: Navigator 1.0 (imperativo — más difícil de testear), AutoRoute (más complejo de configurar).

### Hive para Offline Cache
**Decisión**: `hive_flutter==1.1.x` para almacenamiento local.
**Razón**: Performance extrema (NoSQL key-value en Dart puro). Sin I/O async bloqueante. `TypeAdapters` generados por `hive_generator`. Ideal para cachear planes y conversaciones.
**Alternativas rechazadas**: `sqflite` (overhead de SQL para datos simples), `drift` (más complejo), `SharedPreferences` (solo tipos primitivos).

### flutter_secure_storage para JWT
**Decisión**: `flutter_secure_storage==9.x` para tokens JWT.
**Razón**: iOS Keychain + Android Keystore. El estándar de facto para datos sensibles en Flutter. Los tokens JWT no deben estar en Hive (encriptación no garantizada).

### freezed para State Classes
**Decisión**: `freezed` + `freezed_annotation` para clases de estado immutables.
**Razón**: Genera `copyWith`, `==`, `hashCode`, y `toString` automáticamente. Evita mutaciones accidentales de estado. Compatible con Riverpod y json_serializable.

### share_plus para Compartir PDFs
**Decisión**: `share_plus==7.x` para el share sheet nativo al compartir el plan.
**Razón**: Un paquete para iOS y Android. API simple. No requiere permisos especiales para compartir URLs.

### fl_chart para Gráfica de Peso
**Decisión**: `fl_chart==0.67.x` para el weight journey chart.
**Razón**: Gráficas customizables en Flutter puro. LineChart para historial de peso. Ligero comparado con alternativas.

### Dependencias en pubspec.yaml

```yaml
dependencies:
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5
  dio: ^5.4.1
  go_router: ^13.2.0
  hive_flutter: ^1.1.0
  flutter_secure_storage: ^9.0.0
  fl_chart: ^0.67.0
  share_plus: ^7.2.2
  image_picker: ^1.0.7
  flutter_image_compress: ^2.1.0
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1
  cached_network_image: ^3.3.1

dev_dependencies:
  hive_generator: ^2.0.1
  build_runner: ^2.4.8
  freezed: ^2.4.7
  json_serializable: ^6.7.1
  riverpod_generator: ^2.3.9
  flutter_lints: ^3.0.0
  mocktail: ^1.0.1
```
