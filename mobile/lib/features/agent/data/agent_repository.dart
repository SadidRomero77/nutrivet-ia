/// Repositorio del agente conversacional — streaming SSE + historial.
///
/// POST /v1/agent/chat devuelve Server-Sent Events.
/// GET /v1/agent/conversations/{pet_id} devuelve historial para visualización.
library;

import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';

part 'agent_repository.g.dart';

/// Estado de cuota del agente conversacional para el tier Free.
class AgentQuota {
  const AgentQuota({
    required this.isFreeTier,
    required this.canAsk,
    this.dailyCount,
    this.dailyLimit,
    this.totalCount,
    this.totalLimit,
  });

  factory AgentQuota.fromJson(Map<String, dynamic> json) => AgentQuota(
        isFreeTier: json['is_free_tier'] as bool,
        canAsk: json['can_ask'] as bool,
        dailyCount: json['daily_count'] as int?,
        dailyLimit: json['daily_limit'] as int?,
        totalCount: json['total_count'] as int?,
        totalLimit: json['total_limit'] as int?,
      );

  /// Cuota ilimitada — usado como valor por defecto antes de cargar o en tiers pagados.
  factory AgentQuota.unlimited() => const AgentQuota(
        isFreeTier: false,
        canAsk: true,
      );

  final bool isFreeTier;
  final bool canAsk;
  final int? dailyCount;
  final int? dailyLimit;
  final int? totalCount;
  final int? totalLimit;

  /// Texto del badge "2/3 hoy" — null si el tier es pagado (no mostrar).
  String? get badgeText {
    if (!isFreeTier || dailyCount == null || dailyLimit == null) return null;
    return '${dailyCount}/${dailyLimit} hoy';
  }
}

/// Mensaje del historial de chat para visualización en UI.
class ChatHistoryMessage {
  const ChatHistoryMessage({
    required this.role,
    required this.content,
    this.createdAt,
  });

  factory ChatHistoryMessage.fromJson(Map<String, dynamic> json) =>
      ChatHistoryMessage(
        role: json['role'] as String,
        content: json['content'] as String,
        createdAt: json['created_at'] != null
            ? DateTime.tryParse(json['created_at'] as String)
            : null,
      );

  final String role; // 'user' | 'agent'
  final String content;
  final DateTime? createdAt;

  bool get isUser => role == 'user';
}

@riverpod
AgentRepository agentRepository(Ref ref) => AgentRepository(
      dio: ref.watch(apiClientProvider),
    );

class AgentRepository {
  AgentRepository({required this.dio});

  final Dio dio;

  /// Obtiene el estado de cuota del agente para el usuario actual.
  Future<AgentQuota> getQuota() async {
    try {
      final response =
          await dio.get<Map<String, dynamic>>('/v1/agent/quota');
      return AgentQuota.fromJson(response.data!);
    } on DioException {
      return AgentQuota.unlimited(); // Si falla → no bloquear el chat
    }
  }

  /// Carga el historial de conversaciones de una mascota para mostrar en UI.
  Future<List<ChatHistoryMessage>> loadHistory(String petId) async {
    try {
      final response = await dio.get<List<dynamic>>(
        '/v1/agent/conversations/$petId',
        queryParameters: {'limit': 30},
      );
      return (response.data ?? [])
          .map((e) => ChatHistoryMessage.fromJson(e as Map<String, dynamic>))
          .toList();
    } on DioException {
      return []; // Si falla historial → chat arranca vacío, no bloquea
    }
  }

  /// Envía un mensaje al agente y devuelve un Stream de tokens SSE.
  ///
  /// El stream emite cada chunk de texto a medida que llega del servidor.
  /// Usa Dio para pasar por el interceptor de auth (refresco automático de token).
  Stream<String> sendMessage({
    required String petId,
    required String message,
  }) async* {
    final Response<ResponseBody> response;
    try {
      response = await dio.post<ResponseBody>(
        '/v1/agent/chat',
        data: jsonEncode({'pet_id': petId, 'message': message}),
        options: Options(
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
          },
          responseType: ResponseType.stream,
        ),
      );
    } on DioException catch (e) {
      throw Exception('Error ${e.response?.statusCode ?? 'desconocido'} del agente');
    }

    final stream = response.data!.stream;
    await for (final chunk in stream
        .cast<List<int>>()
        .transform(utf8.decoder)
        .transform(const LineSplitter())) {
      if (chunk.startsWith('data: ')) {
        final data = chunk.substring(6);
        if (data == '[DONE]') break;

        // Detectar eventos de error del backend antes de emitir al UI
        try {
          final decoded = jsonDecode(data);
          if (decoded is Map && decoded.containsKey('error')) {
            final msg = decoded['error'] as String? ??
                decoded['message'] as String? ??
                'Error del agente';
            throw Exception(msg);
          }
          if (decoded is Map && decoded.containsKey('chunk')) {
            yield decoded['chunk'] as String;
          }
        } catch (e) {
          if (e is Exception) rethrow;
          // No es JSON — ignorar línea
        }
      }
    }
  }
}
