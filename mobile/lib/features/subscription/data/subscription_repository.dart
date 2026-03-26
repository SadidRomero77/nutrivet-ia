/// Repositorio de suscripciones — checkout PayU y estado de tier.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';

part 'subscription_repository.g.dart';

/// Estado de suscripción del usuario.
class SubscriptionStatus {
  final String tier;
  final String tierLabel;

  const SubscriptionStatus({required this.tier, required this.tierLabel});

  factory SubscriptionStatus.fromJson(Map<String, dynamic> json) =>
      SubscriptionStatus(
        tier: json['tier'] as String,
        tierLabel: json['tier_label'] as String,
      );
}

/// Resultado del checkout — URL de PayU para redirigir al usuario.
class CheckoutResult {
  final String redirectUrl;
  final String referenceCode;
  final double amountCop;
  final String tier;

  const CheckoutResult({
    required this.redirectUrl,
    required this.referenceCode,
    required this.amountCop,
    required this.tier,
  });

  factory CheckoutResult.fromJson(Map<String, dynamic> json) => CheckoutResult(
        redirectUrl: json['redirect_url'] as String,
        referenceCode: json['reference_code'] as String,
        amountCop: (json['amount_cop'] as num).toDouble(),
        tier: json['tier'] as String,
      );

  bool get hasRedirectUrl => redirectUrl.isNotEmpty;
}

class SubscriptionRepository {
  final Dio _dio;

  SubscriptionRepository(this._dio);

  /// Obtiene el estado de suscripción actual del usuario autenticado.
  Future<SubscriptionStatus> getStatus() async {
    final response =
        await _dio.get<Map<String, dynamic>>('/v1/subscriptions/status');
    return SubscriptionStatus.fromJson(response.data!);
  }

  /// Inicia un checkout de suscripción en PayU.
  ///
  /// Retorna la URL de pago para abrir en el browser del dispositivo.
  Future<CheckoutResult> createCheckout(String tier) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/v1/subscriptions/checkout',
      data: {'tier': tier},
    );
    return CheckoutResult.fromJson(response.data!);
  }
}

@riverpod
SubscriptionRepository subscriptionRepository(Ref ref) =>
    SubscriptionRepository(ref.watch(apiClientProvider));

@riverpod
Future<SubscriptionStatus> subscriptionStatus(Ref ref) =>
    ref.watch(subscriptionRepositoryProvider).getStatus();
