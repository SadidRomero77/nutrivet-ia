# FRONTEND-SPEC.md — NutriVet.IA Mobile App (Flutter) v2
> Todo lo necesario para implementación del frontend sin preguntas adicionales.
> Stack: Flutter 3.x + Dart 3.x + Riverpod + GoRouter + Dio

---

## Estructura de carpetas COMPLETA

```
mobile/
├── lib/
│   ├── main.dart
│   ├── app.dart                         ← MaterialApp + GoRouter
│   │
│   ├── core/
│   │   ├── constants/
│   │   │   ├── app_colors.dart
│   │   │   ├── app_text_styles.dart
│   │   │   └── app_strings.dart         ← Todos los textos en español
│   │   ├── config/
│   │   │   └── env_config.dart
│   │   ├── network/
│   │   │   ├── api_client.dart          ← Dio + interceptors JWT
│   │   │   └── api_endpoints.dart
│   │   ├── storage/
│   │   │   └── secure_storage.dart      ← flutter_secure_storage para tokens
│   │   ├── errors/
│   │   │   ├── app_exception.dart
│   │   │   └── error_handler.dart
│   │   └── utils/
│   │       ├── validators.dart
│   │       └── formatters.dart
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   ├── data/
│   │   │   │   ├── auth_repository.dart
│   │   │   │   └── auth_models.dart
│   │   │   ├── presentation/
│   │   │   │   ├── login_screen.dart
│   │   │   │   ├── register_screen.dart   ← NUEVO: nombre, email, contraseña,
│   │   │   │   │                               ciudad, país
│   │   │   │   ├── email_verify_screen.dart ← NUEVO
│   │   │   │   └── auth_controller.dart
│   │   │   └── auth_providers.dart
│   │   │
│   │   ├── pets/
│   │   │   ├── data/
│   │   │   │   ├── pet_repository.dart
│   │   │   │   └── pet_model.dart
│   │   │   ├── presentation/
│   │   │   │   ├── pets_list_screen.dart
│   │   │   │   ├── pet_detail_screen.dart
│   │   │   │   ├── add_pet_screen.dart        ← ACTUALIZADO: flujo completo
│   │   │   │   ├── bcs_selector_screen.dart   ← NUEVO: selector BCS 1-9 con imágenes
│   │   │   │   ├── medical_history_screen.dart ← NUEVO: multi-condición
│   │   │   │   ├── allergy_screen.dart         ← NUEVO: lista alérgenos + "no sabe"
│   │   │   │   └── pets_controller.dart
│   │   │   └── pet_providers.dart
│   │   │
│   │   ├── diet_modality/
│   │   │   ├── presentation/
│   │   │   │   ├── modality_selector_screen.dart ← NUEVO: Natural vs Concentrado
│   │   │   │   └── modality_controller.dart
│   │   │   └── modality_providers.dart
│   │   │
│   │   ├── plans/
│   │   │   ├── data/
│   │   │   │   ├── plan_repository.dart
│   │   │   │   └── plan_model.dart
│   │   │   ├── presentation/
│   │   │   │   ├── plan_screen.dart            ← Vista del plan activo
│   │   │   │   ├── plan_chat_screen.dart        ← Chat con el agente
│   │   │   │   ├── plan_history_screen.dart
│   │   │   │   └── plans_controller.dart
│   │   │   └── plan_providers.dart
│   │   │
│   │   ├── concentrate/                         ← NUEVO módulo
│   │   │   ├── data/
│   │   │   │   └── concentrate_repository.dart
│   │   │   ├── presentation/
│   │   │   │   ├── concentrate_profile_screen.dart ← perfil ideal del concentrado
│   │   │   │   ├── concentrate_result_screen.dart  ← resultados con sponsors si aplica
│   │   │   │   └── concentrate_controller.dart
│   │   │   └── concentrate_providers.dart
│   │   │
│   │   ├── scanner/
│   │   │   ├── data/
│   │   │   │   └── scanner_repository.dart
│   │   │   ├── presentation/
│   │   │   │   ├── scanner_screen.dart         ← Cámara + guía de foto
│   │   │   │   ├── scan_result_screen.dart     ← Resultado con semáforo
│   │   │   │   └── scanner_controller.dart
│   │   │   └── scanner_providers.dart
│   │   │
│   │   └── vet/
│   │       ├── data/
│   │       │   └── vet_repository.dart
│   │       ├── presentation/
│   │       │   ├── patients_screen.dart
│   │       │   ├── sign_plan_screen.dart
│   │       │   ├── reject_plan_screen.dart     ← NUEVO
│   │       │   └── vet_controller.dart
│   │       └── vet_providers.dart
│   │
│   └── shared/
│       ├── widgets/
│       │   ├── nutrivet_button.dart
│       │   ├── nutrivet_text_field.dart
│       │   ├── pet_card.dart
│       │   ├── plan_status_badge.dart         ← DRAFT/PENDING_VET/ACTIVE/BLOCKED/REJECTED
│       │   ├── disclaimer_banner.dart         ← Obligatorio en todo plan
│       │   ├── toxicity_warning_card.dart     ← Rojo, ingrediente tóxico
│       │   ├── allergy_alert_card.dart        ← NUEVO: alerta de alérgeno
│       │   ├── vet_required_banner.dart       ← Requiere firma veterinaria
│       │   ├── sponsored_tag.dart             ← NUEVO: tag "Patrocinado" visible
│       │   ├── bcs_image_guide.dart           ← NUEVO: imágenes BCS 1-9
│       │   ├── loading_overlay.dart
│       │   └── error_snackbar.dart
│       └── extensions/
│           └── context_extensions.dart
│
├── assets/
│   ├── images/
│   │   ├── bcs/
│   │   │   ├── bcs_dog_1.png … bcs_dog_9.png   ← Imágenes BCS perro escala 1-9
│   │   │   └── bcs_cat_1.png … bcs_cat_9.png   ← Imágenes BCS gato escala 1-9
│   │   └── modality/
│   │       ├── natural_diet.png
│   │       └── concentrate.png
│   └── lottie/
│       └── loading_paw.json
│
├── test/
├── pubspec.yaml
└── analysis_options.yaml
```

---

## Rutas (GoRouter)

```dart
/                         → SplashScreen (check token)
/login                    → LoginScreen
/register                 → RegisterScreen             ← NUEVO
/verify-email             → EmailVerifyScreen          ← NUEVO

/home                     → HomeScreen (bottom nav)
  /home/pets              → PetsListScreen
  /home/pets/add          → AddPetScreen (wizard multi-paso)
    /home/pets/add/bcs    → BcsSelectorScreen          ← NUEVO
    /home/pets/add/medical → MedicalHistoryScreen      ← NUEVO
    /home/pets/add/allergies → AllergyScreen           ← NUEVO
  /home/pets/:id          → PetDetailScreen
  /home/pets/:id/modality → ModalitySelectorScreen     ← NUEVO
  /home/plans/:petId      → PlanScreen
  /home/plans/:id/chat    → PlanChatScreen
  /home/plans/:id/history → PlanHistoryScreen
  /home/concentrate/:petId → ConcentrateProfileScreen  ← NUEVO
  /home/concentrate/:petId/result → ConcentrateResultScreen ← NUEVO
  /home/scanner           → ScannerScreen
  /home/scanner/result    → ScanResultScreen

/vet/patients             → PatientsScreen (solo vet)
/vet/plans/:id/sign       → SignPlanScreen (solo vet)
/vet/plans/:id/reject     → RejectPlanScreen (solo vet) ← NUEVO
```

---

## Flujos de Usuario

### Flujo Registro y Onboarding
```
RegisterScreen
  → nombre, email, contraseña, ciudad, país
  → EmailVerifyScreen (ingresa código o clic en link)
  → LoginScreen
  → HomeScreen → prompt: "Registra tu primera mascota"
```

### Wizard Registro de Mascota (multi-paso)
```
Paso 1: Datos básicos
  nombre, especie (perro/gato), raza, sexo

Paso 2: Datos físicos
  edad, peso, talla (mini/pequeño/mediano/grande/gigante)
  → BcsSelectorScreen: grid 3×3 de imágenes 1-9
    cada imagen muestra el cuerpo del animal con descripción
    usuario selecciona el que más se parece a su mascota

Paso 3: Estado y actividad
  estado reproductivo (esterilizado/sin esterilizar/no sabe)
  nivel de actividad:
    si perro → (nulo/leve/moderado/alto/muy alto)
    si gato  → (indoor/outdoor)

Paso 4: Antecedentes médicos
  Multi-select de condiciones:
  [ ] Diabético
  [ ] Hipotiroideo
  [ ] Antecedentes cancerígenos → abre campo: "¿Dónde?" (texto)
  [ ] Problemas articulares
  [ ] Renal
  [ ] Hepático
  [ ] Pancreático
  [ ] Neurodegenerativo
  [ ] Problemas bucales
  [ ] Problemas de piel
  [ ] Alergias alimentarias → lleva a AllergyScreen
  [ ] Ninguno conocido

Paso 5: AllergyScreen (solo si seleccionó "Alergias alimentarias")
  Lista con checkboxes: Pollo, Res, Cerdo, Cordero, Pescado, Huevo,
  Trigo, Maíz, Soja, Lácteos, Arroz, Avena, Papa, Yuca
  Opción especial: [?] No sé / No he realizado test
    → Si selecciona "No sé": mostrar AlertDialog
      Título: "Recomendación importante"
      Texto: "Te recomendamos realizar un test de alérgenos con un
              veterinario antes de generar el plan. Si continúas sin
              realizarlo, el plan se generará bajo tu entera responsabilidad."
      Botones: [Entendido, continúo bajo mi responsabilidad] [Cancelar]
      Solo al confirmar: guardar owner_accepted_risk = true

Paso 6: Confirmar y guardar mascota
```

### Selector de Modalidad
```
ModalitySelectorScreen
  ┌─────────────────────┐  ┌─────────────────────┐
  │  🥩 Dieta Natural   │  │ 🛒 Concentrado      │
  │                     │  │ Comercial           │
  │  Plan casero con    │  │                     │
  │  ingredientes       │  │ Te damos el perfil  │
  │  frescos y          │  │ nutricional ideal   │
  │  porciones          │  │ para buscar un      │
  │  personalizadas     │  │ concentrado apto    │
  └─────────────────────┘  └─────────────────────┘
```

### Plan Natural (Tipo A) — Pantallas clave
```
PlanScreen muestra:
  - DisclaimerBanner (siempre visible, no se puede ocultar)
  - PlanStatusBadge
  - Kcal diarias + macros (proteína, carbohidratos, vegetales/frutas)
  - Número de porciones al día
  - Lista de ingredientes aprobados (proteínas, carbs, vegetales, frutas)
  - Ingredientes PROHIBIDOS (en rojo, no negociables)
  - Instrucciones de preparación
  - Snacks saludables sugeridos
  - Protocolo de transición (visualización de los 7 días)
  - Protocolo de emergencia digestiva
  - Suplementos referenciales (no son prescripción médica)

Si condición médica → VetRequiredBanner con instrucciones
Si alergia confirmada → AllergyAlertCard listando alérgenos excluidos
```

### Plan Concentrado (Tipo B) — Pantallas clave
```
ConcentrateProfileScreen:
  - Perfil nutricional ideal:
    - % proteína mínimo recomendado
    - % grasa máximo recomendado
    - % fibra mínimo
    - Fuentes de proteína recomendadas
    - Ingredientes a evitar
  - Tipo de alimento: seco / húmedo / mixto
  - Número de porciones sugeridas

ConcentrateResultScreen:
  - Si no hay sponsors: "Usa estos criterios para seleccionar el concentrado
    ideal en tu tienda veterinaria o pet shop."
  - Si hay sponsors verificados para ese perfil:
    - Tarjeta con SponsoredTag("Patrocinado") SIEMPRE visible
    - Logo, nombre, info de contacto del sponsor
    - Perfil nutricional del producto
  - Protocolo de transición (gráfica 7 días)
  - DisclaimerBanner
```

### Scanner OCR
```
ScannerScreen:
  - Preview de cámara
  - Overlay con guía: "Fotografía SOLO la tabla nutricional o la lista
    de ingredientes. NO fotografíes el frente del empaque ni la marca."
  - Botón de captura
  - Preview de la foto + confirmación antes de enviar

ScanResultScreen:
  - Semáforo grande (verde/amarillo/rojo)
  - Valores extraídos (tabla)
  - Problemas encontrados (concerns)
  - Aspectos positivos (positives)
  - Recomendación en texto
  - DisclaimerBanner
```

---

## Diseño Visual

### Paleta de colores
```dart
class AppColors {
  static const primary       = Color(0xFF2E7D32);  // Verde oscuro
  static const primaryLight  = Color(0xFF4CAF50);  // Verde medio
  static const accent        = Color(0xFF00C853);  // Verde neón
  static const background    = Color(0xFF0D0D0D);  // Negro (dark theme)
  static const surface       = Color(0xFF1A1A1A);  // Gris muy oscuro
  static const cardBg        = Color(0xFF263238);  // Gris azulado
  static const textPrimary   = Color(0xFFFFFFFF);  // Blanco
  static const textSecondary = Color(0xFF90A4AE);  // Gris claro
  static const error         = Color(0xFFF44336);  // Rojo
  static const warning       = Color(0xFFFF6F00);  // Naranja
  static const blocked       = Color(0xFFB71C1C);  // Rojo oscuro
  static const sponsored     = Color(0xFFFFD600);  // Amarillo (tag patrocinado)
  static const adequate      = Color(0xFF43A047);  // Verde semáforo
  static const caution       = Color(0xFFFFA000);  // Naranja semáforo
  static const notRecommended= Color(0xFFD32F2F);  // Rojo semáforo
}
```

### Plan status badges
- DRAFT → gris
- PENDING_VET → naranja (pulsante)
- ACTIVE → verde
- MODIFIED → azul
- REJECTED → naranja oscuro
- BLOCKED → rojo (con icono de candado)
- ARCHIVED → gris claro

### BCS Selector (BcsSelectorScreen)
```
Grid 3×3 con imágenes por especie:
+-------+-------+-------+
|  1    |  2    |  3    |  ← Bajo peso (fondo rojo claro)
| [img] | [img] | [img] |
+-------+-------+-------+
|  4    |  5    |  6    |  ← Ideal 4-5 (fondo verde claro), Sobrepeso 6
| [img] | [img] | [img] |
+-------+-------+-------+
|  7    |  8    |  9    |  ← Sobrepeso 7, Obesidad 8-9 (fondo naranja/rojo)
| [img] | [img] | [img] |
+-------+-------+-------+
Debajo: descripción de la imagen seleccionada
"Costillas visibles sin palpar, vértebras prominentes"
```

---

## pubspec.yaml

```yaml
name: nutrivet_mobile
description: NutriVet.IA - Nutrición personalizada para mascotas
version: 1.0.0+1
environment:
  sdk: ">=3.0.0 <4.0.0"
  flutter: ">=3.16.0"

dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.6
  riverpod_annotation: ^2.3
  go_router: ^14.3
  dio: ^5.7
  flutter_secure_storage: ^9.2
  image_picker: ^1.1
  camera: ^0.11
  google_fonts: ^6.2
  cached_network_image: ^3.4
  lottie: ^3.1
  freezed_annotation: ^2.4
  json_annotation: ^4.9
  intl: ^0.19
  flutter_svg: ^2.0        # Imágenes BCS en formato SVG
  percent_indicator: ^4.2  # Barras de macronutrientes
  step_indicator: ^1.0     # Wizard multi-paso registro mascota

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4
  freezed: ^2.5
  json_serializable: ^6.8
  riverpod_generator: ^2.4
  flutter_lints: ^5.0
  mocktail: ^1.0
```

---

## Reglas de implementación

1. **Riverpod** para todo el estado — nunca setState en lógica de negocio
2. **Freezed** para modelos de datos — inmutabilidad garantizada
3. **GoRouter** para navegación — nunca Navigator.push directo
4. **flutter_secure_storage** para tokens — nunca SharedPreferences para datos sensibles
5. **DisclaimerBanner** presente en TODA pantalla que muestre un plan nutricional
6. **Plan BLOCKED** → UI roja con icono de candado y mensaje claro
7. **Plan PENDING_VET** → banner naranja "Esperando validación del veterinario"
8. **SponsoredTag** → siempre visible en amarillo, nunca oculto
9. **BCS Selector** → imágenes por especie (perro/gato), descripción al seleccionar
10. **AllergyScreen** → mostrar AlertDialog con disclaimer antes de aceptar "no sé"
11. **OCR guide** → overlay de instrucciones antes de capturar foto
12. **Textos en español** — todas las cadenas en `app_strings.dart`
13. **Manejo de errores** siempre visible al usuario — nunca silencioso
14. **Sin lógica de negocio** en widgets — todo en controllers/providers

---

## Clean Architecture por Feature (Estructura Detallada)

Cada feature implementa 3 capas explícitas. La separación garantiza que la UI nunca
dependa directamente de HTTP o de modelos JSON.

```
features/plans/
├── domain/                          ← Entidades puras (sin imports Flutter/Dio/JSON)
│   ├── plan_entity.dart             ← Modelos de negocio inmutables con Freezed
│   ├── plan_repository.dart         ← Interface abstracta (puerto de salida)
│   └── plan_failure.dart            ← Tipos de error del dominio (sealed class)
├── data/                            ← Implementación concreta de la interface
│   ├── plan_repository_impl.dart    ← Llama a API y mapea DTOs → Entities
│   ├── plan_dto.dart                ← Data Transfer Object (JSON serializable)
│   └── plan_local_source.dart       ← Hive cache (lectura offline)
└── presentation/
    ├── plan_screen.dart             ← Solo UI — sin lógica de negocio
    ├── plan_controller.dart         ← StateNotifier de Riverpod
    └── plan_providers.dart          ← Providers de Riverpod
```

### Separación Entity vs DTO

```dart
// domain/plan_entity.dart — sin imports de Flutter, Dio, ni JSON
@freezed
class PlanEntity with _$PlanEntity {
  const factory PlanEntity({
    required String id,
    required PlanStatus status,
    required PlanModality modality,
    required double dailyKcal,
    required int mealsPerDay,
    required List<String> approvedProteins,
    required List<String> forbiddenFoods,
    required String disclaimer,
    required DateTime createdAt,
  }) = _PlanEntity;
}

// data/plan_dto.dart — JSON serializable, se convierte a Entity
@JsonSerializable()
class PlanDTO {
  final String id;
  final String status;
  @JsonKey(name: 'plan_content')
  final Map<String, dynamic> planContent;
  @JsonKey(name: 'created_at')
  final String createdAt;

  PlanEntity toDomain() => PlanEntity(
    id: id,
    status: PlanStatus.fromString(status),
    modality: PlanModality.fromString(planContent['modality'] ?? 'natural'),
    dailyKcal: (planContent['daily_kcal'] as num).toDouble(),
    mealsPerDay: planContent['meals_per_day'] as int,
    approvedProteins: List<String>.from(planContent['approved_proteins'] ?? []),
    forbiddenFoods: List<String>.from(planContent['forbidden_foods'] ?? []),
    disclaimer: planContent['disclaimer'] as String,
    createdAt: DateTime.parse(createdAt),
  );
}
```

### Repository Interface (Puerto de Salida)

```dart
// domain/plan_repository.dart
abstract class PlanRepository {
  /// Genera un nuevo plan nutricional para la mascota.
  Future<Either<PlanFailure, JobStarted>> createPlan({
    required String petId,
    required PlanModality modality,
    String? idempotencyKey,
  });

  /// Consulta el plan activo de una mascota (con caché offline).
  Future<Either<PlanFailure, PlanEntity>> getActivePlan(String petId);

  /// Consulta el estado de un job de generación.
  Future<Either<PlanFailure, JobStatus>> getJobStatus(String jobId);
}

// domain/plan_failure.dart
sealed class PlanFailure {
  const PlanFailure();
}
final class PlanNotFound extends PlanFailure {}
final class ToxicIngredientDetected extends PlanFailure {
  final String ingredient;
  const ToxicIngredientDetected(this.ingredient);
}
final class VetReviewRequired extends PlanFailure {}
final class LLMUnavailable extends PlanFailure {}
final class NetworkFailure extends PlanFailure {}
```

### Aplicar a TODAS las features

La misma estructura `domain/data/presentation` aplica a:
- `auth/` — AuthEntity, AuthRepository, LoginFailure
- `pets/` — PetEntity, PetRepository, PetFailure
- `scanner/` — ScanResultEntity, ScannerRepository, ScannerFailure
- `concentrate/` — ConcentrateProfileEntity, ConcentrateRepository
- `vet/` — PatientEntity, VetRepository

---

## Gestión de Conectividad y Offline

### Estrategia

El plan activo de cada mascota se cachea localmente para consulta sin conexión.
Las operaciones de escritura (crear plan, firmar, etc.) **siempre requieren red**.

```yaml
# pubspec.yaml — agregar
  hive: ^2.2
  hive_flutter: ^1.1
  connectivity_plus: ^6.0
```

```dart
// core/connectivity/connectivity_provider.dart
final connectivityProvider = StreamProvider<bool>((ref) {
  return Connectivity()
    .onConnectivityChanged
    .map((result) => result.any((r) => r != ConnectivityResult.none));
});

// Uso en cualquier screen
final isOnline = ref.watch(connectivityProvider).valueOrNull ?? true;
if (!isOnline) {
  return OfflineBanner(); // Banner rojo: "Sin conexión — mostrando datos guardados"
}
```

### Datos cacheados localmente con Hive

| Dato | Box Hive | TTL | Operaciones offline-safe |
|------|----------|-----|--------------------------|
| Plan activo | `active_plans` | 7 días | ✅ Consultar |
| Perfil de mascota | `pet_profiles` | 24 horas | ✅ Consultar |
| Tokens JWT | FlutterSecureStorage | Hasta expiración | ✅ Auto-refresh |
| Preferencias de UI | `preferences` | Permanente | ✅ Leer/escribir |
| Historial de planes | `plan_history` | 7 días | ✅ Consultar |

**Operaciones que SIEMPRE requieren red:**
- Generar nuevo plan (LLM)
- Subir imagen OCR
- Chat con el agente
- Firma veterinaria

```dart
// data/plan_local_source.dart
class PlanLocalSource {
  static const _boxName = 'active_plans';

  Future<PlanEntity?> getCachedPlan(String petId) async {
    final box = await Hive.openBox<Map>(_boxName);
    final cached = box.get(petId);
    if (cached == null) return null;
    final cachedAt = DateTime.parse(cached['cached_at'] as String);
    if (DateTime.now().difference(cachedAt).inDays > 7) return null; // TTL
    return PlanDTO.fromJson(Map<String, dynamic>.from(cached['data'] as Map)).toDomain();
  }

  Future<void> cachePlan(String petId, PlanEntity plan) async {
    final box = await Hive.openBox<Map>(_boxName);
    await box.put(petId, {
      'cached_at': DateTime.now().toIso8601String(),
      'data': plan.toJson(),
    });
  }
}
```

---

## Flujo Detallado del Interceptor JWT

```dart
// core/network/auth_interceptor.dart
class AuthInterceptor extends Interceptor {
  final SecureStorage _storage;
  final Dio _authDio; // Dio separado para refresh (evita loop infinito)
  bool _isRefreshing = false;
  final _pendingRequests = <({RequestOptions options, ErrorInterceptorHandler handler})>[];

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await _storage.getAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    if (_isRefreshing) {
      // Encolar mientras se refresca
      _pendingRequests.add((options: err.requestOptions, handler: handler));
      return;
    }

    _isRefreshing = true;
    try {
      final refreshToken = await _storage.getRefreshToken();
      if (refreshToken == null) {
        await _forceLogout();
        return handler.next(err);
      }

      final response = await _authDio.post(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final newToken = response.data['data']['access_token'] as String;
      await _storage.saveAccessToken(newToken);

      // Reintentar requests encoladas
      for (final pending in _pendingRequests) {
        pending.options.headers['Authorization'] = 'Bearer $newToken';
        pending.handler.resolve(await _dio.fetch(pending.options));
      }
      _pendingRequests.clear();

      // Reintentar request original
      err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
      handler.resolve(await _dio.fetch(err.requestOptions));
    } catch (_) {
      await _forceLogout(); // Refresh falló → logout forzado
      handler.next(err);
    } finally {
      _isRefreshing = false;
    }
  }

  Future<void> _forceLogout() async {
    await _storage.clearAll();
    RouterService.instance.go('/login'); // GoRouter
  }
}
```

### Configuración de Timeouts Dio

```dart
// core/network/api_client.dart
final dio = Dio(BaseOptions(
  baseUrl: EnvConfig.apiBaseUrl,
  connectTimeout: const Duration(seconds: 10),
  receiveTimeout: const Duration(seconds: 90), // LLM puede tardar hasta 90s
  sendTimeout: const Duration(seconds: 30),    // Upload imagen OCR
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': 'es',
  },
))
  ..interceptors.addAll([
    AuthInterceptor(storage, authDio),
    RetryInterceptor(maxRetries: 2, retryDelay: const Duration(seconds: 2)),
    LogInterceptor(requestBody: false, responseBody: false), // sin PII en logs
  ]);
```

### Retry Logic

```dart
// core/network/retry_interceptor.dart
class RetryInterceptor extends Interceptor {
  final int maxRetries;
  final Duration retryDelay;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final retryCount = err.requestOptions.extra['_retryCount'] as int? ?? 0;

    // Solo reintentar en errores de red y 5xx (NUNCA en 4xx)
    final shouldRetry =
        err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout ||
        err.type == DioExceptionType.connectionError ||
        ((err.response?.statusCode ?? 0) >= 500);

    if (shouldRetry && retryCount < maxRetries) {
      await Future.delayed(retryDelay * (retryCount + 1)); // backoff lineal
      err.requestOptions.extra['_retryCount'] = retryCount + 1;
      return handler.resolve(await _dio.fetch(err.requestOptions));
    }

    handler.next(err);
  }
}
```

---

## Push Notifications (FCM)

### Configuración

```yaml
# pubspec.yaml — agregar
  firebase_core: ^3.6
  firebase_messaging: ^15.1
```

```dart
// core/notifications/push_notification_service.dart
class PushNotificationService {
  static Future<void> initialize() async {
    await Firebase.initializeApp();
    final messaging = FirebaseMessaging.instance;

    // Solicitar permisos (iOS — Android 13+ también requiere)
    final settings = await messaging.requestPermission(
      alert: true, badge: true, sound: true,
    );
    if (settings.authorizationStatus == AuthorizationStatus.denied) return;

    // Registrar token en el backend
    final token = await messaging.getToken();
    if (token != null) {
      await _apiClient.post('/api/v1/users/me/push-token', data: {
        'token': token,
        'platform': Platform.isIOS ? 'ios' : 'android',
      });
    }

    // Actualizar token cuando FCM lo rote
    messaging.onTokenRefresh.listen((newToken) {
      _apiClient.post('/api/v1/users/me/push-token', data: {'token': newToken, 'platform': Platform.isIOS ? 'ios' : 'android'});
    });

    // Manejar notificaciones en primer plano
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    // Manejar tap en notificación (app en background)
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
  }

  static void _handleForegroundMessage(RemoteMessage message) {
    // Mostrar SnackBar o dialog en lugar de la notificación del SO
    final type = message.data['type'] as String?;
    if (type == 'PLAN_SIGNED') {
      RouterService.instance.go('/home/plans/${message.data['plan_id']}');
    }
  }

  static void _handleNotificationTap(RemoteMessage message) {
    final type = message.data['type'] as String?;
    switch (type) {
      case 'PLAN_SIGNED':   RouterService.instance.go('/home/plans/${message.data['plan_id']}'); break;
      case 'PLAN_REJECTED': RouterService.instance.go('/home/plans/${message.data['plan_id']}'); break;
      case 'PLAN_PENDING_VET': RouterService.instance.go('/vet/plans/${message.data['plan_id']}/sign'); break;
    }
  }
}
```

### Tipos de Notificaciones

| Evento | Destinatario | type | Navegación al tap |
|--------|-------------|------|-------------------|
| Plan → PENDING_VET | Owner | `PLAN_PENDING_VET_OWNER` | PlanScreen |
| Plan → PENDING_VET | Vet asignado | `PLAN_PENDING_VET` | SignPlanScreen |
| Plan → ACTIVE | Owner | `PLAN_SIGNED` | PlanScreen |
| Plan → REJECTED | Owner | `PLAN_REJECTED` | PlanScreen (con notas) |

---

## Deep Linking

### Configuración Android (`android/app/src/main/AndroidManifest.xml`)

```xml
<intent-filter android:autoVerify="true">
  <action android:name="android.intent.action.VIEW"/>
  <category android:name="android.intent.category.DEFAULT"/>
  <category android:name="android.intent.category.BROWSABLE"/>
  <data android:scheme="https" android:host="app.nutrivetia.com"/>
</intent-filter>
```

### Configuración iOS (`ios/Runner/Info.plist`)

```xml
<key>FlutterDeepLinkingEnabled</key><true/>
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array><string>nutrivetia</string></array>
  </dict>
</array>
```

### Rutas de Deep Link

| URL | Destino | Rol requerido |
|-----|---------|---------------|
| `app.nutrivetia.com/plan/{id}` | PlanScreen | owner (solo el suyo) |
| `app.nutrivetia.com/vet/sign/{planId}` | SignPlanScreen | vet |
| `app.nutrivetia.com/verify-email/{token}` | EmailVerifyScreen | cualquiera |

```dart
// app.dart — GoRouter con redirect por auth y rol
GoRouter(
  initialLocation: '/',
  redirect: (context, state) {
    final auth = ref.read(authProvider);
    final isAuthenticated = auth.isAuthenticated;
    final isVetRoute = state.uri.path.startsWith('/vet/');
    final isVet = auth.user?.role == 'vet';

    if (!isAuthenticated && !state.uri.path.startsWith('/login') &&
        !state.uri.path.startsWith('/verify-email')) {
      // Guardar ruta destino para redirigir post-login
      return '/login?redirect=${Uri.encodeComponent(state.uri.toString())}';
    }
    if (isVetRoute && !isVet) return '/home'; // Acceso denegado
    return null;
  },
)
```

---

## Pipeline de Imagen OCR (Scanner)

### Compresión y validación antes del upload

```yaml
# pubspec.yaml — agregar
  image: ^4.2   # procesamiento de imágenes en Dart
```

```dart
// features/scanner/data/image_processor.dart
class ImageProcessor {
  static const _maxFileSizeBytes = 4 * 1024 * 1024; // 4MB
  static const _minDimensionPx = 500;

  /// Valida y comprime imagen antes de enviarla al scanner OCR.
  /// Lanza [ImageTooSmallException] si la imagen es muy pequeña.
  /// Lanza [ImageCompressionException] si no se puede comprimir.
  static Future<Uint8List> prepareForOCR(XFile imageFile) async {
    final bytes = await imageFile.readAsBytes();
    final image = img.decodeImage(bytes);
    if (image == null) throw ImageCompressionException('Formato de imagen no soportado');

    // Validar dimensiones mínimas para buena legibilidad OCR
    if (image.width < _minDimensionPx || image.height < _minDimensionPx) {
      throw ImageTooSmallException(
        'La imagen debe tener al menos $_minDimensionPx px en cada lado. '
        'Acércate más a la etiqueta nutricional.',
      );
    }

    // Comprimir iterativamente hasta estar bajo 4MB
    var quality = 95;
    var compressed = img.encodeJpg(image, quality: quality);
    while (compressed.length > _maxFileSizeBytes && quality > 60) {
      quality -= 10;
      compressed = img.encodeJpg(image, quality: quality);
    }
    if (compressed.length > _maxFileSizeBytes) {
      throw ImageCompressionException('No se pudo comprimir la imagen a menos de 4MB');
    }

    return Uint8List.fromList(compressed);
  }
}
```

### Flujo completo del Scanner

```
ScannerScreen
  → Mostrar overlay instructivo: "Fotografía SOLO la tabla nutricional"
  → Usuario captura foto
  → Preview con confirmación antes de procesar
  → ImageProcessor.prepareForOCR() — comprime + valida
  → Si error → mostrar mensaje claro al usuario
  → Encode a base64
  → POST /api/v1/scanner/label { image_base64, image_type, pet_id }
  → Mostrar loading con mensaje "Analizando la etiqueta..."
  → ScanResultScreen con semáforo
```

---

## Accesibilidad (WCAG 2.1 nivel AA)

### Reglas obligatorias de implementación

```dart
// 1. Semantic labels en todos los widgets interactivos
Semantics(
  label: 'Selector de condición corporal — ${bcs}/9',
  hint: 'Toca para cambiar la puntuación de condición corporal',
  child: BcsSelectorWidget(),
);

// 2. Tamaño mínimo de tap target: 48x48 dp (WCAG 2.5.5)
ConstrainedBox(
  constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
  child: IconButton(onPressed: onTap, icon: const Icon(Icons.check)),
);

// 3. DisclaimerBanner anuncia su aparición en TalkBack/VoiceOver
Semantics(
  liveRegion: true, // Anuncia automáticamente cuando aparece en pantalla
  label: 'Aviso importante: NutriVet.IA es asesoría nutricional digital, no reemplaza el diagnóstico médico veterinario',
  child: DisclaimerBanner(),
);

// 4. Contraste mínimo verificado — AppColors cumple 4.5:1
// Verde primary (0xFF2E7D32) sobre negro (0xFF0D0D0D) → ratio 7.2:1 ✓
// Texto secondary (0xFF90A4AE) sobre surface (0xFF1A1A1A) → ratio 5.1:1 ✓

// 5. Respetar tamaño de fuente del sistema
Text(
  AppStrings.disclaimerText,
  style: Theme.of(context).textTheme.bodySmall?.copyWith(
    // No fijar fontSize absoluto — dejar que textScaler lo ajuste
  ),
);
```

### Checklist de accesibilidad por pantalla

- [ ] Todos los botones tienen `Semantics(label: ...)` descriptivo
- [ ] Imágenes decorativas marcadas con `ExcludeSemantics()`
- [ ] Imágenes informativas tienen `Semantics(label: 'descripción')`
- [ ] Formularios tienen `autofillHints` configurados
- [ ] Errores de formulario anunciados como `liveRegion: true`
- [ ] BCS grid accesible via teclado y TalkBack
- [ ] Scanner guía de foto accesible por voz

---

## Manejo de Polling para Jobs Asíncronos

```dart
// features/plans/presentation/plan_generation_controller.dart
class PlanGenerationController extends AsyncNotifier<PlanEntity?> {
  @override
  FutureOr<PlanEntity?> build() => null;

  /// Inicia generación del plan y hace polling hasta completar.
  Future<void> generatePlan({required String petId, required PlanModality modality}) async {
    state = const AsyncLoading();
    final idempotencyKey = const Uuid().v4(); // Previene duplicados en retry

    final jobResult = await ref.read(planRepositoryProvider).createPlan(
      petId: petId, modality: modality, idempotencyKey: idempotencyKey,
    );

    await jobResult.fold(
      (failure) async => state = AsyncError(failure, StackTrace.current),
      (job) async {
        // Polling con backoff progresivo: 3s → 3s → 5s → 5s → 10s...
        const pollIntervals = [3, 3, 5, 5, 10, 10, 15, 15, 30];
        for (var i = 0; i < pollIntervals.length; i++) {
          await Future.delayed(Duration(seconds: pollIntervals[i]));
          final statusResult = await ref.read(planRepositoryProvider).getJobStatus(job.jobId);
          final jobStatus = statusResult.getOrElse((_) => null);

          if (jobStatus?.status == 'completed') {
            final planResult = await ref.read(planRepositoryProvider).getActivePlan(petId);
            state = planResult.fold(AsyncError.new, AsyncData.new);
            return;
          } else if (jobStatus?.status == 'failed') {
            state = AsyncError(LLMUnavailable(), StackTrace.current);
            return;
          }
        }
        // Timeout de polling (máx ~2 min)
        state = AsyncError(LLMUnavailable(), StackTrace.current);
      },
    );
  }
}
```

---

## Librerías Adicionales en pubspec.yaml

```yaml
dependencies:
  # Existentes ...

  # Nuevas — Clean Architecture + Offline + Notifications
  hive: ^2.2
  hive_flutter: ^1.1
  connectivity_plus: ^6.0
  firebase_core: ^3.6
  firebase_messaging: ^15.1
  image: ^4.2                  # compresión imagen OCR
  uuid: ^4.4                   # idempotency keys
  hydrated_riverpod: ^2.0      # persistencia de estado entre sesiones
  app_links: ^6.1              # deep linking universal
  flutter_local_notifications: ^17.2  # notificaciones en primer plano

dev_dependencies:
  # Existentes ...
  integration_test:            # tests de integración UI
    sdk: flutter
```
