# NFR Design Patterns — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Mobile App

### Patrón 1: Offline-First con Hive
El plan activo y el historial de chat se cachean en Hive inmediatamente al cargarlos.
```dart
// plan_provider.dart
Future<void> loadPlan(String planId) async {
  // 1. Mostrar caché inmediatamente (si existe)
  final cached = await hiveService.getPlan(planId);
  if (cached != null) state = PlanState(plan: cached, isLoading: false);

  // 2. Fetch fresco del backend
  try {
    final fresh = await apiClient.get('/plans/$planId');
    await hiveService.savePlan(fresh);
    state = PlanState(plan: fresh, isLoading: false);
  } catch (e) {
    // Si falla y hay caché → quedarse con el caché
    if (cached == null) state = PlanState(error: e.toString());
  }
}
```

### Patrón 2: Optimistic UI para Chat
El mensaje del usuario se muestra ANTES de recibir respuesta del servidor:
```dart
void sendMessage(String text) {
  // 1. Agregar mensaje del usuario inmediatamente (optimistic)
  state = state.copyWith(messages: [...state.messages, UserMessage(text)]);

  // 2. Iniciar stream SSE
  _startStream(text);
}
```
Mejora la percepción de velocidad — el usuario no espera para ver su propio mensaje.

### Patrón 3: Wizard Draft Persistente (Hive)
El borrador del wizard se guarda en Hive en cada cambio de campo:
```dart
void updateField(String field, dynamic value) {
  state = state.copyWith(/* actualizar campo */);
  hiveService.saveDraft('current_draft', state);  // inmediato
}
```
Si la app se cierra → el borrador se restaura al abrir la pantalla del wizard.
El borrador se limpia solo cuando el wizard completa exitosamente.

### Patrón 4: JWT Refresh Transparente
El `AuthInterceptor` de Dio maneja el refresh sin que el usuario lo note:
- Si el token expira durante el uso → refresh automático.
- Si el refresh falla → redirect a login screen con mensaje.
- El usuario nunca ve un error 401 inesperado en producción.

### Patrón 5: Polling con Timer Cancelable
El polling del job de plan usa un `Timer` que se cancela cuando el job termina:
```dart
Timer? _pollingTimer;
void startPolling(String jobId) {
  _pollingTimer = Timer.periodic(Duration(seconds: 3), (_) async {
    final job = await apiClient.get('/plans/jobs/$jobId');
    if (job.status == 'completed' || job.status == 'failed') {
      _pollingTimer?.cancel();
      _handleJobResult(job);
    }
  });
  // Auto-cancel después de 60s
  Future.delayed(Duration(seconds: 60), () => _pollingTimer?.cancel());
}
```

### Patrón 6: Immutable State con Freezed
Todos los estados de Riverpod son clases `@freezed` — inmutables con `copyWith`:
```dart
@freezed
class ChatState with _$ChatState {
  const factory ChatState({...}) = _ChatState;
}
// Actualizar: state = state.copyWith(messages: [...state.messages, newMsg])
```
Previene mutación accidental del estado y facilita debugging (cada estado es un snapshot).

### Patrón 7: Compresión de Imagen antes de Upload
Imágenes del scanner pueden ser muy grandes (fotos de cámara 12MP = 5-15MB):
```dart
final compressed = await FlutterImageCompress.compressWithFile(
  imagePath,
  quality: 80,
  minWidth: 1024,
  minHeight: 1024,
);
// Verificar que esté dentro del límite de 10MB
if (compressed.length > 10 * 1024 * 1024) {
  throw AppException("Imagen demasiado grande, intenta con otra imagen");
}
```
