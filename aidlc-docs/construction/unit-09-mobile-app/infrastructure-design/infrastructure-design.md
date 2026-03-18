# Infrastructure Design — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura del Mobile App

### ApiClient (Dio)

```dart
// core/api/api_client.dart
class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: kBackendUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
    ));
    _dio.interceptors.addAll([
      AuthInterceptor(),     // JWT refresh automático
      LoggingInterceptor(),  // Sin PII en logs
      RetryInterceptor(),    // Retry × 2 en errores de red
    ]);
  }
}
```

### AuthInterceptor (JWT Refresh Automático)

```dart
// core/api/auth_interceptor.dart
class AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await SecureStorage.getAccessToken();
    final expiresAt = await SecureStorage.getTokenExpiresAt();

    if (expiresAt != null && expiresAt.isBefore(DateTime.now().add(Duration(seconds: 60)))) {
      // Token expira en < 60s → refresh antes del request
      await _refreshToken();
    }

    options.headers['Authorization'] = 'Bearer $token';
    return handler.next(options);
  }

  Future<void> _refreshToken() async {
    final refresh = await SecureStorage.getRefreshToken();
    final response = await Dio().post('$kBackendUrl/auth/refresh',
        data: {'refresh_token': refresh});
    await SecureStorage.saveTokens(response.data);
  }
}
```

### HiveService (Offline Cache)

```dart
// core/storage/hive_service.dart
class HiveService {
  static const String _petBox = 'pets';
  static const String _planBox = 'plans';
  static const String _chatBox = 'conversations';
  static const String _draftBox = 'wizard_drafts';

  Future<void> savePet(PetModel pet) async {
    final box = await Hive.openBox<PetModel>(_petBox);
    await box.put(pet.petId, pet);
  }

  Future<void> saveDraft(String draftId, PetWizardDraft draft) async {
    final box = await Hive.openBox<PetWizardDraft>(_draftBox);
    await box.put(draftId, draft);
  }

  Future<PetWizardDraft?> getDraft(String draftId) async {
    final box = await Hive.openBox<PetWizardDraft>(_draftBox);
    return box.get(draftId);
  }
}
```

### SSEClient (Streaming Chat)

```dart
// core/api/sse_client.dart
class SSEClient {
  Stream<String> streamChat(String petId, String message, String accessToken) {
    return _dio.get(
      '/agent/chat',
      data: {'pet_id': petId, 'message': message},
      options: Options(
        responseType: ResponseType.stream,
        headers: {'Authorization': 'Bearer $accessToken'},
      ),
    ).asStream()
     .asyncExpand((response) => response.data.stream)
     .map((chunk) => utf8.decode(chunk))
     .where((line) => line.startsWith('data: '))
     .map((line) => jsonDecode(line.substring(6))['chunk'] ?? '');
  }
}
```

## Flutter Packages Clave

```yaml
# pubspec.yaml
dependencies:
  flutter_riverpod: ^2.5.x    # state management
  dio: ^5.4.x                 # HTTP client + streaming
  go_router: ^13.x            # declarative routing
  hive_flutter: ^1.1.x        # local storage + offline cache
  flutter_secure_storage: ^9.x # JWT tokens en keychain/keystore
  fl_chart: ^0.67.x           # gráfica de peso (weight journey)
  share_plus: ^7.x            # compartir PDF (export service)
  image_picker: ^1.x          # cámara y galería (scanner)
  flutter_image_compress: ^2.x # comprimir imágenes antes de upload
  freezed_annotation: ^2.x    # immutable state classes
  json_serializable: ^6.x     # JSON serialization
  cached_network_image: ^3.x  # cache de imágenes del plan

dev_dependencies:
  hive_generator: ^2.x
  build_runner: ^2.x
  freezed: ^2.x
  flutter_test:
    sdk: flutter
  mocktail: ^1.x              # mocking en tests
```
