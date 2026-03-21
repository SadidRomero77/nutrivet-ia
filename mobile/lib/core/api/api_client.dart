/// Cliente HTTP centralizado con Dio + interceptor JWT.
///
/// Adjunta el access token en cada request.
/// Si recibe 401 → intenta refresh rotativo → si falla, logout.
/// Refresh serializado con flag estático para evitar race conditions.
library;

import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../storage/secure_storage.dart';

part 'api_client.g.dart';

const _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

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
    final storage = _ref.read(secureStorageProvider);
    final token = await storage.readAccessToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
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
      await storage.writeTokens(accessToken: newAccess, refreshToken: newRefresh);

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
      // Refresh falló — notificar a pendientes y hacer logout
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
