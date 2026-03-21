/// Repositorio de autenticación — login, registro, refresh, logout, perfil.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';
import '../../../core/storage/secure_storage.dart';
import '../../../core/utils/jwt_utils.dart';

part 'auth_repository.g.dart';

/// Modelo del perfil del usuario autenticado.
class UserProfile {
  UserProfile({
    required this.userId,
    required this.email,
    required this.role,
    required this.tier,
    this.fullName,
    this.phone,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        userId: json['user_id'] as String,
        email: json['email'] as String,
        role: json['role'] as String,
        tier: json['tier'] as String,
        fullName: json['full_name'] as String?,
        phone: json['phone'] as String?,
      );

  final String userId;
  final String email;
  final String role;
  final String tier;
  final String? fullName;
  final String? phone;
}

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
    String? phone,
    String role = 'owner',
  }) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/auth/register',
      data: {
        'email': email,
        'password': password,
        'full_name': fullName,
        'role': role,
        if (phone != null && phone.isNotEmpty) 'phone': phone,
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

  /// Obtiene el perfil del usuario autenticado.
  Future<UserProfile> getMe() async {
    final response = await dio.get<Map<String, dynamic>>('/v1/auth/me');
    return UserProfile.fromJson(response.data!);
  }

  /// Obtiene el perfil público de un veterinario.
  Future<UserProfile> getVetProfile(String vetId) async {
    final response =
        await dio.get<Map<String, dynamic>>('/v1/auth/vet/$vetId/profile');
    return UserProfile.fromJson(response.data!);
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
