/// Repositorio de autenticación — login, registro, refresh, logout, perfil.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';
import '../../../core/services/push_notification_service.dart';
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
    this.clinicName,
    this.specialization,
    this.licenseNumber,
    this.vetStatus,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        userId: json['user_id'] as String,
        email: json['email'] as String,
        role: json['role'] as String,
        tier: json['tier'] as String,
        fullName: json['full_name'] as String?,
        phone: json['phone'] as String?,
        clinicName: json['clinic_name'] as String?,
        specialization: json['specialization'] as String?,
        licenseNumber: json['license_number'] as String?,
        vetStatus: json['vet_status'] as String?,
      );

  final String userId;
  final String email;
  final String role;
  final String tier;
  final String? fullName;
  final String? phone;
  final String? clinicName;
  final String? specialization;
  final String? licenseNumber;
  /// Estado de verificación del veterinario: pending | approved | null
  final String? vetStatus;
}

/// Estadísticas de actividad del usuario autenticado.
class UserStats {
  UserStats({
    this.petsCount = 0,
    this.activePlansCount = 0,
    this.patientsCount = 0,
    this.pendingPlansCount = 0,
  });

  factory UserStats.fromJson(Map<String, dynamic> json) => UserStats(
        petsCount: (json['pets_count'] as int?) ?? 0,
        activePlansCount: (json['active_plans_count'] as int?) ?? 0,
        patientsCount: (json['patients_count'] as int?) ?? 0,
        pendingPlansCount: (json['pending_plans_count'] as int?) ?? 0,
      );

  final int petsCount;
  final int activePlansCount;
  final int patientsCount;
  final int pendingPlansCount;
}

/// Cuota de uso del tier actual del usuario.
class TierUsage {
  TierUsage({
    required this.tier,
    this.plansTotal = 0,
    this.plansLimit,
    this.plansRemaining,
    this.canGeneratePlan = true,
  });

  factory TierUsage.fromJson(Map<String, dynamic> json) => TierUsage(
        tier: json['tier'] as String,
        plansTotal: (json['plans_total'] as int?) ?? 0,
        plansLimit: json['plans_limit'] as int?,
        plansRemaining: json['plans_remaining'] as int?,
        canGeneratePlan: (json['can_generate_plan'] as bool?) ?? true,
      );

  final String tier;
  final int plansTotal;
  final int? plansLimit;
  final int? plansRemaining;
  final bool canGeneratePlan;

  bool get isUnlimited => plansLimit == null;
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
    // Registrar token FCM — fire-and-forget, nunca debe abortar el login.
    // try/catch adicional por si Firebase no está inicializado (lanza sincrónicamente).
    try {
      PushNotificationService.instance.registerCurrentToken().ignore();
    } catch (_) {}
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

  /// Actualiza nombre, teléfono y/o datos clínicos del usuario.
  Future<UserProfile> updateProfile({
    String? fullName,
    String? phone,
    String? clinicName,
    String? specialization,
    String? licenseNumber,
  }) async {
    final response = await dio.patch<Map<String, dynamic>>(
      '/v1/auth/me',
      data: {
        if (fullName != null) 'full_name': fullName,
        if (phone != null) 'phone': phone,
        if (clinicName != null) 'clinic_name': clinicName,
        if (specialization != null) 'specialization': specialization,
        if (licenseNumber != null) 'license_number': licenseNumber,
      },
    );
    return UserProfile.fromJson(response.data!);
  }

  /// Cambia la contraseña del usuario autenticado.
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await dio.patch<void>(
      '/v1/auth/me/password',
      data: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
  }

  /// Estadísticas de actividad del usuario autenticado.
  Future<UserStats> getMyStats() async {
    final response = await dio.get<Map<String, dynamic>>('/v1/auth/me/stats');
    return UserStats.fromJson(response.data!);
  }

  /// Solicita recuperación de contraseña por email.
  Future<void> forgotPassword(String email) async {
    await dio.post<void>(
      '/v1/auth/forgot-password',
      data: {'email': email},
    );
  }

  /// Restablece contraseña con token de recuperación.
  Future<void> resetPassword({
    required String token,
    required String newPassword,
  }) async {
    await dio.post<void>(
      '/v1/auth/reset-password',
      data: {'token': token, 'new_password': newPassword},
    );
  }

  /// Cuota de uso del tier actual.
  Future<TierUsage> getTierUsage() async {
    final response =
        await dio.get<Map<String, dynamic>>('/v1/auth/me/tier-usage');
    return TierUsage.fromJson(response.data!);
  }

  /// Cierra sesión y elimina tokens locales.
  Future<void> logout() async {
    try {
      // FCM cleanup dentro del try — si Firebase no está inicializado no rompe
      // el flujo y deleteTokens() en finally siempre se ejecuta.
      PushNotificationService.instance.unregisterCurrentToken().ignore();
      final refreshToken = await storage.readRefreshToken();
      await dio.post(
        '/v1/auth/logout',
        data: {'refresh_token': refreshToken ?? ''},
        options: Options(
          sendTimeout: const Duration(seconds: 3),
          receiveTimeout: const Duration(seconds: 3),
        ),
      );
    } catch (_) {
      // Ignorar errores de red al hacer logout
    } finally {
      await storage.deleteTokens();
    }
  }
}
