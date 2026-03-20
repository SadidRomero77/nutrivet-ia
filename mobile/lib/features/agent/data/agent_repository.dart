/// Repositorio del agente conversacional — streaming SSE.
///
/// POST /v1/agent/chat devuelve Server-Sent Events.
/// El cliente consume el stream línea a línea y expone un Stream<String>.
library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/storage/secure_storage.dart';

part 'agent_repository.g.dart';

const _baseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

@riverpod
AgentRepository agentRepository(Ref ref) => AgentRepository(
      storage: ref.read(secureStorageProvider),
    );

class AgentRepository {
  AgentRepository({required this.storage});

  final SecureStorageService storage;

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
        yield data;
      }
    }
  }
}
