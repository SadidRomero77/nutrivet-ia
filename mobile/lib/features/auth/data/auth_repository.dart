/// Repositorio de autenticación — login, registro, refresh, logout.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../core/utils/jwt_utils.dart';

part 'auth_repository.g.dart';

/// Modelo de respuesta del login/refresh.
class AuthTokens {
  AuthTokens({required this.accessToken, required this.refreshToken});

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
        accessToken: json['access_token'] as String,
        refreshToken: json['refresh_token'] as String,
      );

  final String accessToken;
  final String refreshToken;
}

@riverpod
AuthRepository authRepository(Ref ref) => AuthRepository(
      dio: ref.watch(apiClientProvider),
      storage: ref.read(secureStorageProvider),
    );

class AuthRepository {
  AuthRepository({required this.dio, required this.storage});

  final Dio dio;
  final SecureStorageService storage;

  /// Login con email/contraseña → guarda tokens en secure storage.
  /// Retorna el role del usuario ('owner' o 'vet').
  Future<String> login({
    required String email,
    required String password,
  }) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/auth/login',
      data: {'email': email, 'password': password},
    );
    final tokens = AuthTokens.fromJson(response.data!);
    final role = JwtUtils.getRole(tokens.accessToken);
    await storage.writeTokens(
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      role: role,
    );
    return role;
  }

  /// Registro de nuevo usuario (owner o vet).
  /// Retorna el role del usuario creado.
  Future<String> register({
    required String email,
    required String password,
    required String fullName,
    String role = 'owner',
  }) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/auth/register',
      data: {
        'email': email,
        'password': password,
        'full_name': fullName,
        'role': role,
      },
    );
    final tokens = AuthTokens.fromJson(response.data!);
    final decodedRole = JwtUtils.getRole(tokens.accessToken);
    await storage.writeTokens(
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      role: decodedRole,
    );
    return decodedRole;
  }

  /// Cierra sesión y elimina tokens locales.
  Future<void> logout() async {
    try {
      await dio.post('/v1/auth/logout');
    } catch (_) {
      // Ignorar errores de red al hacer logout
    } finally {
      await storage.deleteTokens();
    }
  }
}
