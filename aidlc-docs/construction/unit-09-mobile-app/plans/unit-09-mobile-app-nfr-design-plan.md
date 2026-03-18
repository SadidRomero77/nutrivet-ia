# Plan: NFR Design — Unit 09: mobile-app

**Unidad**: unit-09-mobile-app
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a mobile-app

### Patrón: Token Refresh Interceptor (Dio)

**Contexto**: El access token expira cada 15 minutos. El refresh debe ser transparente
para el usuario — sin logout ni pantalla de error visible.

**Diseño**:
```dart
// lib/core/api_client.dart
class JwtRefreshInterceptor extends Interceptor {
  bool _isRefreshing = false;
  final List<RequestOptions> _pendingRequests = [];

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401 && !_isRefreshing) {
      _isRefreshing = true;
      try {
        final newTokens = await authDataSource.refreshToken();
        await secureStorage.write(key: 'access_token', value: newTokens.accessToken);
        await secureStorage.write(key: 'refresh_token', value: newTokens.refreshToken);

        // Reintentar request original con nuevo token
        final retryOptions = err.requestOptions;
        retryOptions.headers['Authorization'] = 'Bearer ${newTokens.accessToken}';
        final response = await dio.fetch(retryOptions);
        handler.resolve(response);
      } catch (e) {
        // Refresh falló → logout
        await secureStorage.deleteAll();
        ref.read(authNotifierProvider.notifier).logout();
      } finally {
        _isRefreshing = false;
      }
    } else {
      handler.next(err);
    }
  }
}
```

### Patrón: Offline-First Cache (Hive como Primary)

**Contexto**: El plan y el chat deben ser legibles sin red.

**Diseño**:
```dart
// lib/features/plan/application/plan_notifier.dart
class PlanNotifier extends AsyncNotifier<PlanState> {
  @override
  Future<PlanState> build() async {
    // 1. Servir desde Hive (rápido, offline)
    final cached = hiveService.getPlan(petId);
    if (cached != null) {
      state = AsyncData(PlanState(plan: cached, fromCache: true));
    }

    // 2. Actualizar desde backend (si hay red)
    try {
      final fresh = await planDataSource.getPlan(petId);
      await hiveService.savePlan(petId, fresh);
      return PlanState(plan: fresh, fromCache: false);
    } on DioException catch (e) {
      if (cached != null) return PlanState(plan: cached, fromCache: true);
      rethrow;
    }
  }
}
```

### Patrón: SSE Streaming (StreamBuilder + fade-in)

**Contexto**: El usuario debe ver los tokens aparecer progresivamente con animación suave.

**Diseño**:
```dart
// lib/features/agent/presentation/chat_screen.dart
StreamBuilder<String>(
  stream: chatNotifier.responseStream,
  builder: (context, snapshot) {
    if (snapshot.connectionState == ConnectionState.waiting) {
      return TypingIndicator();  // Tres puntos animados
    }
    return AnimatedBuilder(
      animation: _fadeController,
      builder: (ctx, _) => FadeTransition(
        opacity: _fadeController,
        child: Text(snapshot.data ?? ''),
      ),
    );
  },
)
```

### Patrón: Plan Polling (PlanNotifier con timeout)

**Contexto**: El usuario espera hasta 60s para la generación del plan. Debe ver progreso.

**Diseño**:
```dart
// lib/features/plan/application/plan_notifier.dart
Future<void> pollJobUntilReady(String jobId) async {
  const maxAttempts = 20;
  const interval = Duration(seconds: 3);

  for (int attempt = 0; attempt < maxAttempts; attempt++) {
    final job = await planDataSource.getJobStatus(jobId);

    if (job.status == 'READY' && job.planId != null) {
      await loadPlan(job.planId!);
      return;
    }

    if (job.status == 'FAILED') {
      throw PlanGenerationFailedError(job.errorMessage);
    }

    // Actualizar progreso en UI: attempt / maxAttempts
    state = AsyncData(PlanState(
      loading: true,
      progress: (attempt + 1) / maxAttempts,
    ));

    await Future.delayed(interval);
  }
  throw PlanPollingTimeoutError('Timeout después de 60 segundos');
}
```

## Cobertura de Tests Requerida (Widget Tests)

| Test | Descripción | Tipo |
|------|-------------|------|
| `wizard_talla_oculta_gato` | Especie gato → talla no visible | Widget test |
| `wizard_draft_hive` | Draft persiste entre sesiones | Widget test |
| `plan_polling_shows_plan` | Job READY → PlanScreen visible | Widget test |
| `chat_quota_free` | 3 preguntas → 4ta deshabilitada | Widget test |
| `chat_upgrade_gate` | Cuota agotada → modal visible | Widget test |
| `ocr_semaforo_rojo` | Resultado rojo → UI rojo + razón | Widget test |
| `vet_pending_vet_primero` | PENDING_VET al tope de lista | Widget test |
| Integration | Registro → wizard → plan → chat | Integration test |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- Unit spec: `inception/units/unit-09-mobile-app.md`
- ADR-021: SSE streaming
