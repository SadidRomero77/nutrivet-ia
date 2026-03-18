# Domain Entities — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Mobile App (Flutter)

### AuthState (Riverpod State)
Estado de autenticación global de la app.
```dart
@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    required bool isAuthenticated,
    String? accessToken,        // JWT 15min
    String? refreshToken,       // rotativo
    String? userId,             // UUID
    String? role,               // owner / vet
    String? tier,               // free / basico / premium / vet
    DateTime? tokenExpiresAt,
  }) = _AuthState;
}
```

### PetWizardDraft (Hive Local Storage)
Borrador del wizard de mascota almacenado localmente. NO se envía al backend hasta tener los 13 campos completos.
```dart
@HiveType(typeId: 1)
class PetWizardDraft extends HiveObject {
  @HiveField(0) String? nombre;
  @HiveField(1) String? especie;         // perro / gato
  @HiveField(2) String? raza;
  @HiveField(3) String? sexo;
  @HiveField(4) int? edadValor;
  @HiveField(5) String? edadUnidad;      // meses / años
  @HiveField(6) double? pesoKg;
  @HiveField(7) String? talla;           // solo perros
  @HiveField(8) String? estadoReproductivo;
  @HiveField(9) String? nivelActividad;
  @HiveField(10) int? bcs;              // 1-9
  @HiveField(11) List<String>? condicionesMedicas;
  @HiveField(12) List<String>? alergias;
  @HiveField(13) String? alimentacionActual;

  bool get isComplete => [nombre, especie, raza, sexo, edadValor, edadUnidad,
    pesoKg, estadoReproductivo, nivelActividad, bcs, condicionesMedicas,
    alergias, alimentacionActual].every((f) => f != null);
}
```

### PlanState (Riverpod State)
Estado del plan nutricional activo.
```dart
@freezed
class PlanState with _$PlanState {
  const factory PlanState({
    String? jobId,             // polling del job
    String? planId,
    String? status,            // PENDING_VET | ACTIVE | queued | processing
    NutritionPlanModel? plan,
    bool isLoading = false,
    String? error,
  }) = _PlanState;
}
```

### ChatState (Riverpod State)
Estado del chat con el agente conversacional.
```dart
@freezed
class ChatState with _$ChatState {
  const factory ChatState({
    @Default([]) List<ChatMessage> messages,
    bool isStreaming = false,
    String streamingBuffer = '',
    QuotaStatus? quotaStatus,
    bool isUpgradeRequired = false,
  }) = _ChatState;
}
```

### ScanState (Riverpod State)
Estado del scanner de etiquetas.
```dart
@freezed
class ScanState with _$ScanState {
  const factory ScanState({
    File? selectedImage,
    String? imageType,           // nutrition_table / ingredients_list
    String? scanId,
    ScanResult? result,          // semaphore + findings
    bool isProcessing = false,
    String? error,
  }) = _ScanState;
}
```
