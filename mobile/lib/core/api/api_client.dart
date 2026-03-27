/// Cliente HTTP centralizado con Dio + interceptor JWT.
///
/// Adjunta el access token en cada request (excepto endpoints públicos de auth).
/// Si recibe 401 → intenta refresh rotativo → si falla, limpia tokens.
/// Refresh serializado con flag estático para evitar race conditions.
library;

import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../storage/secure_storage.dart';
import '../utils/jwt_utils.dart';

part 'api_client.g.dart';

const _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

/// Endpoints que NO necesitan el header Authorization y NO deben disparar refresh.
/// Son rutas públicas: autentican por credenciales, no por token.
const _noAuthPaths = {
  '/v1/auth/login',
  '/v1/auth/register',
  '/v1/auth/refresh',
  '/v1/auth/forgot-password',
  '/v1/auth/reset-password',
  '/v1/auth/logout', // 401 aquí = sesión ya inválida, no tiene sentido refrescar
};

/// Proveedor del Dio configurado con interceptors JWT.
@riverpod
Dio apiClient(Ref ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ),
  );

  dio.interceptors.add(_JwtInterceptor(ref));

  return dio;
}

/// Interceptor que añade el Authorization header y gestiona refresh 401.
///
/// El refresh está serializado con un flag estático para evitar race conditions:
/// si dos requests fallan con 401 simultáneamente, solo uno ejecuta el refresh;
/// el otro espera hasta que el primero complete y luego reintenta con el nuevo token.
class _JwtInterceptor extends Interceptor {
  _JwtInterceptor(this._ref);

  final Ref _ref;

  // Serialización de refresh — evita múltiples refreshes concurrentes
  static bool _isRefreshing = false;
  static final List<Completer<String?>> _pendingRefreshCompleters = [];

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // No añadir token en endpoints públicos de auth (login, register, etc.)
    // Usamos uri.path (path relativo sin host) para comparación robusta,
    // independientemente de si Dio resolvió el path completo o relativo.
    if (!_noAuthPaths.contains(options.uri.path)) {
      final storage = _ref.read(secureStorageProvider);
      final token = await storage.readAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    // Endpoints públicos: el 401 es por credenciales inválidas, no token expirado.
    // No intentar refresh — pasarlo directo al caller.
    if (_noAuthPaths.contains(err.requestOptions.uri.path)) {
      return handler.next(err);
    }

    final storage = _ref.read(secureStorageProvider);
    final refreshToken = await storage.readRefreshToken();
    if (refreshToken == null) {
      return handler.next(err);
    }

    // Si ya hay un refresh en curso, esperar su resultado
    if (_isRefreshing) {
      final completer = Completer<String?>();
      _pendingRefreshCompleters.add(completer);
      final newToken = await completer.future;
      if (newToken != null) {
        err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
        try {
          final retried = await _ref.read(apiClientProvider).fetch(err.requestOptions);
          return handler.resolve(retried);
        } catch (_) {}
      }
      return handler.next(err);
    }

    // Este request ejecuta el refresh
    _isRefreshing = true;
    try {
      final dio = Dio(BaseOptions(baseUrl: _baseUrl));
      final response = await dio.post(
        '/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final newAccess = response.data['access_token'] as String;
      final newRefresh = response.data['refresh_token'] as String;
      // Extraer el role del nuevo access token para preservarlo en storage.
      // Sin esto, writeTokens usaría 'owner' por defecto y un vet quedaría
      // con role='owner' en storage, rompiendo el routing tras el primer refresh.
      final role = JwtUtils.getRole(newAccess);
      await storage.writeTokens(accessToken: newAccess, refreshToken: newRefresh, role: role);

      // Notificar a todos los requests pendientes
      for (final c in _pendingRefreshCompleters) {
        c.complete(newAccess);
      }
      _pendingRefreshCompleters.clear();

      err.requestOptions.headers['Authorization'] = 'Bearer $newAccess';
      try {
        final retried = await _ref.read(apiClientProvider).fetch(err.requestOptions);
        return handler.resolve(retried);
      } catch (_) {}
    } catch (_) {
      // Refresh falló — notificar a pendientes y limpiar tokens
      for (final c in _pendingRefreshCompleters) {
        c.complete(null);
      }
      _pendingRefreshCompleters.clear();
      await storage.deleteTokens();
    } finally {
      _isRefreshing = false;
    }

    handler.next(err);
  }
}
