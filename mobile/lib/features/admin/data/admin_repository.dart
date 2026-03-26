/// Repositorio de administración — operaciones exclusivas del rol admin.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';

part 'admin_repository.g.dart';

/// Modelo de usuario para el panel admin.
class AdminUser {
  AdminUser({
    required this.userId,
    required this.email,
    required this.role,
    required this.tier,
    required this.isActive,
    this.fullName,
    this.phone,
    this.clinicName,
    this.specialization,
    this.licenseNumber,
    this.vetStatus,
    this.createdAt,
  });

  factory AdminUser.fromJson(Map<String, dynamic> json) => AdminUser(
        userId: json['user_id'] as String,
        email: json['email'] as String,
        role: json['role'] as String,
        tier: json['tier'] as String,
        isActive: json['is_active'] as bool,
        fullName: json['full_name'] as String?,
        phone: json['phone'] as String?,
        clinicName: json['clinic_name'] as String?,
        specialization: json['specialization'] as String?,
        licenseNumber: json['license_number'] as String?,
        vetStatus: json['vet_status'] as String?,
        createdAt: json['created_at'] as String?,
      );

  final String userId;
  final String email;
  final String role;
  final String tier;
  final bool isActive;
  final String? fullName;
  final String? phone;
  final String? clinicName;
  final String? specialization;
  final String? licenseNumber;
  final String? vetStatus;
  final String? createdAt;

  String get displayName => fullName ?? email;
}

/// Estadísticas globales del sistema.
class AdminStats {
  AdminStats({
    required this.totalUsers,
    required this.ownersCount,
    required this.vetsCount,
    required this.vetsPending,
    required this.activeSubscriptions,
    required this.totalPayments,
    required this.totalRevenueCop,
  });

  factory AdminStats.fromJson(Map<String, dynamic> json) => AdminStats(
        totalUsers: (json['total_users'] as int?) ?? 0,
        ownersCount: (json['owners_count'] as int?) ?? 0,
        vetsCount: (json['vets_count'] as int?) ?? 0,
        vetsPending: (json['vets_pending'] as int?) ?? 0,
        activeSubscriptions: (json['active_subscriptions'] as int?) ?? 0,
        totalPayments: (json['total_payments'] as int?) ?? 0,
        totalRevenueCop: (json['total_revenue_cop'] as num?)?.toDouble() ?? 0,
      );

  final int totalUsers;
  final int ownersCount;
  final int vetsCount;
  final int vetsPending;
  final int activeSubscriptions;
  final int totalPayments;
  final double totalRevenueCop;
}

/// Un pago registrado en el sistema.
class PaymentRecord {
  PaymentRecord({
    required this.paymentId,
    required this.tier,
    required this.amountCop,
    required this.status,
    this.createdAt,
  });

  factory PaymentRecord.fromJson(Map<String, dynamic> json) => PaymentRecord(
        paymentId: json['payment_id'] as String,
        tier: json['tier'] as String,
        amountCop: (json['amount_cop'] as num).toDouble(),
        status: json['status'] as String,
        createdAt: json['created_at'] as String?,
      );

  final String paymentId;
  final String tier;
  final double amountCop;
  final String status;
  final String? createdAt;
}

@riverpod
AdminRepository adminRepository(Ref ref) =>
    AdminRepository(dio: ref.watch(apiClientProvider));

class AdminRepository {
  AdminRepository({required this.dio});

  final Dio dio;

  /// Estadísticas globales.
  Future<AdminStats> getStats() async {
    final response =
        await dio.get<Map<String, dynamic>>('/v1/admin/stats');
    return AdminStats.fromJson(response.data!);
  }

  /// Detalle de un usuario por ID.
  Future<AdminUser> getUserDetail(String userId) async {
    final response = await dio.get<Map<String, dynamic>>(
      '/v1/admin/users/$userId',
    );
    return AdminUser.fromJson(response.data!);
  }

  /// Lista usuarios con filtros opcionales.
  Future<List<AdminUser>> listUsers({
    String? role,
    String? tier,
    String? q,
    int limit = 50,
    int offset = 0,
  }) async {
    final response = await dio.get<List<dynamic>>(
      '/v1/admin/users',
      queryParameters: {
        if (role != null) 'role': role,
        if (tier != null) 'tier': tier,
        if (q != null && q.isNotEmpty) 'q': q,
        'limit': limit,
        'offset': offset,
      },
    );
    return (response.data ?? [])
        .map((e) => AdminUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Cambia el tier de un usuario.
  Future<AdminUser> changeUserTier(String userId, String tier) async {
    final response = await dio.patch<Map<String, dynamic>>(
      '/v1/admin/users/$userId/tier',
      data: {'tier': tier},
    );
    return AdminUser.fromJson(response.data!);
  }

  /// Alterna el estado activo/inactivo de un usuario.
  Future<AdminUser> toggleUserStatus(String userId) async {
    final response = await dio.patch<Map<String, dynamic>>(
      '/v1/admin/users/$userId/status',
    );
    return AdminUser.fromJson(response.data!);
  }

  /// Crea una cuenta de veterinario verificada.
  Future<AdminUser> createVet({
    required String email,
    required String password,
    String? fullName,
    String? phone,
    String? clinicName,
    String? specialization,
    String? licenseNumber,
  }) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/admin/users/create-vet',
      data: {
        'email': email,
        'password': password,
        if (fullName != null && fullName.isNotEmpty) 'full_name': fullName,
        if (phone != null && phone.isNotEmpty) 'phone': phone,
        if (clinicName != null && clinicName.isNotEmpty) 'clinic_name': clinicName,
        if (specialization != null && specialization.isNotEmpty) 'specialization': specialization,
        if (licenseNumber != null && licenseNumber.isNotEmpty) 'license_number': licenseNumber,
      },
    );
    return AdminUser.fromJson(response.data!);
  }

  /// Lista vets pendientes de aprobación.
  Future<List<AdminUser>> listPendingVets() async {
    final response = await dio.get<List<dynamic>>('/v1/admin/vets/pending');
    return (response.data ?? [])
        .map((e) => AdminUser.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Aprueba un veterinario.
  Future<AdminUser> approveVet(String userId) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/admin/vets/$userId/approve',
    );
    return AdminUser.fromJson(response.data!);
  }

  /// Rechaza un veterinario.
  Future<AdminUser> rejectVet(String userId, {String comment = ''}) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/admin/vets/$userId/reject',
      data: {'comment': comment},
    );
    return AdminUser.fromJson(response.data!);
  }

  /// Lista todos los pagos del sistema.
  Future<List<PaymentRecord>> listPayments({
    String? userId,
    String? paymentStatus,
    int limit = 50,
  }) async {
    final response = await dio.get<List<dynamic>>(
      '/v1/admin/payments',
      queryParameters: {
        if (userId != null) 'user_id': userId,
        if (paymentStatus != null) 'status': paymentStatus,
        'limit': limit,
      },
    );
    return (response.data ?? [])
        .map((e) => PaymentRecord.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Historial de pagos del usuario autenticado.
  Future<List<PaymentRecord>> getMyPaymentHistory() async {
    final response =
        await dio.get<List<dynamic>>('/v1/subscriptions/history');
    return (response.data ?? [])
        .map((e) => PaymentRecord.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
