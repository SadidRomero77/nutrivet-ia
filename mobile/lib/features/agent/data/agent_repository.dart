/// Repositorio del agente conversacional — streaming SSE + historial.
///
/// POST /v1/agent/chat devuelve Server-Sent Events.
/// GET /v1/agent/conversations/{pet_id} devuelve historial para visualización.
library;

import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';
import '../../../core/storage/secure_storage.dart';

part 'agent_repository.g.dart';

const _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

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
      storage: ref.read(secureStorageProvider),
      dio: ref.watch(apiClientProvider),
    );

class AgentRepository {
  AgentRepository({required this.storage, required this.dio});

  final SecureStorageService storage;
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
  /// El último evento `[DONE]` cierra el stream.
  Stream<String> sendMessage({
    required String petId,
    required String message,
    required String conversationId,
  }) async* {
    final token = await storage.readAccessToken();
    final uri = Uri.parse('$_baseUrl/v1/agent/chat');

    final request = http.Request('POST', uri)
      ..headers['Authorization'] = 'Bearer ${token ?? ''}'
      ..headers['Content-Type'] = 'application/json'
      ..headers['Accept'] = 'text/event-stream'
      ..body = jsonEncode({
        'pet_id': petId,
        'message': message,
        'conversation_id': conversationId,
      });

    final response = await http.Client().send(request);

    if (response.statusCode != 200) {
      throw Exception('Error ${response.statusCode} del agente');
    }

    await for (final chunk in response.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter())) {
      if (chunk.startsWith('data: ')) {
        final data = chunk.substring(6);
        if (data == '[DONE]') break;

        // Detectar eventos de error del backend antes de emitir al UI
        try {
          final decoded = jsonDecode(data);
          if (decoded is Map && decoded.containsKey('error')) {
            final msg = decoded['message'] as String? ??
                decoded['error'] as String? ??
                'Error del agente';
            throw Exception(msg);
          }
          if (decoded is Map && decoded.containsKey('chunk')) {
            yield decoded['chunk'] as String;
            continue;
          }
        } catch (e) {
          if (e is Exception) rethrow;
          // No es JSON — emitir como texto plano
        }

        yield data;
      }
    }
  }
}
