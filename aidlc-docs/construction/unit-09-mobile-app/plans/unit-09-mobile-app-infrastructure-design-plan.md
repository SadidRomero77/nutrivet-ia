# Plan: Infrastructure Design — Unit 09: mobile-app

**Unidad**: unit-09-mobile-app
**Fase AI-DLC**: C3 — Infrastructure Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Mapeo Lógico → Físico

### Compute — Dispositivo del Usuario

| Componente Lógico | Componente Físico |
|-------------------|-------------------|
| Flutter app | iOS (iPhone 12+) + Android (API 26+) |
| Riverpod providers | In-memory state por feature |
| GoRouter | Navegación declarativa por rol |
| Hive boxes | SQLite-based local storage en dispositivo |
| Dio HTTP client | HTTP/HTTPS + interceptores |

### Backend — Hetzner CPX31

Todos los APIs residen en el mismo servidor Hetzner CPX31 (Ashburn VA):

```
https://api.nutrivet.ia/v1/       (producción)
https://staging.api.nutrivet.ia/v1/  (staging)
```

**Reverse proxy**: Caddy con HTTPS automático (Let's Encrypt).
**SSE**: Caddy debe tener `flush_interval` deshabilitado para SSE fluido.

### JWT y Autenticación

```
flutter_secure_storage:
  - "access_token"  → JWT access (15 min)
  - "refresh_token" → JWT refresh (30 días)

Dio interceptor:
  - RequestInterceptor: agrega "Authorization: Bearer {access_token}"
  - ResponseInterceptor: si 401 → llama POST /v1/auth/refresh → retry
  - Si refresh falla → clear storage → GoRouter redirige a /auth
```

### Almacenamiento Local (Hive)

```dart
// lib/core/hive_service.dart
class HiveService {
  static const String AUTH_BOX = 'auth';       // tokens — EncryptedBox
  static const String WIZARD_BOX = 'wizard';   // draft wizard
  static const String PLAN_BOX = 'plan';       // active plan cache
  static const String CHAT_BOX = 'chat';       // last 50 messages per pet
  static const String WEIGHT_BOX = 'weight';   // 90 days weight history
}
```

**Encrypted box**: Usar `HiveAesCipher` con clave almacenada en `flutter_secure_storage`.

### SSE — http package para EventSource

```dart
// lib/features/agent/infrastructure/chat_data_source.dart
import 'package:http/http.dart' as http;

Stream<String> streamChat(ChatRequest request, String token) async* {
  final request_obj = http.Request('POST', Uri.parse('$baseUrl/v1/agent/chat'));
  request_obj.headers['Authorization'] = 'Bearer $token';
  request_obj.headers['Accept'] = 'text/event-stream';
  request_obj.body = jsonEncode(request.toJson());

  final response = await http.Client().send(request_obj);
  await for (final chunk in response.stream.transform(utf8.decoder)) {
    // Parsear eventos SSE: "data: {...}\n\n"
    yield chunk;
  }
}
```

### Imagen para OCR

```dart
// Multipart/form-data upload via Dio
FormData formData = FormData.fromMap({
  'pet_id': petId,
  'image': await MultipartFile.fromFile(imagePath, contentType: MediaType('image', 'jpeg'))
});
await dio.post('/v1/agent/scan', data: formData);
```

### PDF — share_plus con URL Pre-Signed

```dart
// Al exportar plan:
final response = await dio.post('/v1/plans/$planId/export');
final url = response.data['url'];
final expires_at = response.data['expires_at'];

// Compartir via share_plus (WhatsApp/Telegram/email)
await Share.shareUri(Uri.parse(url));
```

### Flavors (Staging vs Producción)

```
flutter --flavor staging -t lib/main_staging.dart
flutter --flavor prod -t lib/main_prod.dart

Env:
  staging: API_BASE_URL = "https://staging.api.nutrivet.ia"
  prod:    API_BASE_URL = "https://api.nutrivet.ia"
```

## Notas Arquitecturales

1. **GoRouter con roles**: La navegación protegida verifica el rol del usuario desde
   `AuthNotifier`. Rutas `/vet/**` solo accesibles con `role == "vet"`.

2. **Riverpod autoDispose**: Los providers de features específicos usan `autoDispose`
   para liberar memoria al salir de la pantalla.

3. **Hive vs Isar**: Hive fue seleccionado por su simplicidad. Si se necesitan queries
   complejas en el historial de peso, considerar migrar a Isar en una fase posterior.

## Referencias

- Global: `_shared/hetzner-infrastructure.md`
- Unit spec: `inception/units/unit-09-mobile-app.md`
- ADR-021: SSE streaming
