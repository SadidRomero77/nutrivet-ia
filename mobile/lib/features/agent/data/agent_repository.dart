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
    required String conversationId,
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
