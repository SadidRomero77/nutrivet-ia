/// Cliente HTTP centralizado con Dio + interceptor JWT.
///
/// Adjunta el access token en cada request.
/// Si recibe 401 → intenta refresh rotativo → si falla, logout.
library;

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
class _JwtInterceptor extends Interceptor {
  _JwtInterceptor(this._ref);

  final Ref _ref;

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
    if (err.response?.statusCode == 401) {
      final storage = _ref.read(secureStorageProvider);
      final refreshToken = await storage.readRefreshToken();
      if (refreshToken != null) {
        try {
          final dio = Dio(BaseOptions(baseUrl: _baseUrl));
          final response = await dio.post(
            '/v1/auth/refresh',
            data: {'refresh_token': refreshToken},
          );
          final newAccess = response.data['access_token'] as String;
          final newRefresh = response.data['refresh_token'] as String;
          await storage.writeTokens(
            accessToken: newAccess,
            refreshToken: newRefresh,
          );
          err.requestOptions.headers['Authorization'] = 'Bearer $newAccess';
          final retried = await _ref.read(apiClientProvider).fetch(
                err.requestOptions,
              );
          return handler.resolve(retried);
        } catch (_) {
          await storage.deleteTokens();
        }
      }
    }
    handler.next(err);
  }
}
