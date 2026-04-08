/// Pantalla de chat con el agente NutriVet.IA.
///
/// - Streaming SSE token a token.
/// - Disclaimer visible (REGLA 8).
/// - Mensajes de emergencia → referral al vet.
/// - Chips de inicio de conversación contextuales.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../pet/data/pet_repository.dart';
import '../data/agent_repository.dart';


const _disclaimer =
    'NutriVet.IA responde solo consultas nutricionales. '
    'Para consultas médicas, contacta a tu veterinario.';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key, required this.petId});

  final String petId;

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _msgCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _sending = false;
  bool _loadingHistory = true;
  PetModel? _pet;
  AgentQuota _quota = AgentQuota.unlimited();

  @override
  void initState() {
    super.initState();
    _loadHistory();
    _loadPet();
    _loadQuota();
  }

  Future<void> _loadQuota() async {
    try {
      final quota = await ref.read(agentRepositoryProvider).getQuota();
      if (mounted) setState(() => _quota = quota);
    } catch (_) {
      // Cuota no disponible — el chat funciona sin badge
    }
  }

  Future<void> _loadPet() async {
    try {
      final pet = await ref.read(petRepositoryProvider).getPet(widget.petId);
      if (mounted) setState(() => _pet = pet);
    } catch (_) {
      // Pet info opcional — no bloquea el chat
    }
  }

  Future<void> _loadHistory() async {
    try {
      final history = await ref
          .read(agentRepositoryProvider)
          .loadHistory(widget.petId);
      if (mounted && history.isNotEmpty) {
        setState(() {
          _messages.addAll(
            history.map(
              (m) => _ChatMessage(text: m.content, isUser: m.isUser),
            ),
          );
        });
        // Scroll al último mensaje después de cargar historial
        WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
      }
    } catch (_) {
      // Historial no disponible — el chat arranca vacío sin bloquear
    } finally {
      if (mounted) setState(() => _loadingHistory = false);
    }
  }

  @override
  void dispose() {
    _msgCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _msgCtrl.text.trim();
    if (text.isEmpty || _sending) return;

    setState(() {
      _messages.add(_ChatMessage(text: text, isUser: true));
      _sending = true;
    });
    _msgCtrl.clear();

    // Agregar mensaje del agente (streaming)
    _messages.add(_ChatMessage(text: '', isUser: false));
    final agentIdx = _messages.length - 1;

    try {
      final stream = ref.read(agentRepositoryProvider).sendMessage(
            petId: widget.petId,
            message: text,
          );

      await for (final chunk in stream) {
        setState(() {
          _messages[agentIdx] = _ChatMessage(
            text: _messages[agentIdx].text + chunk,
            isUser: false,
          );
        });
        _scrollToBottom();
      }
    } catch (e) {
      setState(() {
        _messages[agentIdx] = _ChatMessage(
          text: 'Error al conectar con el agente. Intenta de nuevo.',
          isUser: false,
          isError: true,
        );
      });
    } finally {
      if (mounted) setState(() => _sending = false);
      // Actualizar cuota después de cada mensaje (solo visible en Free tier)
      if (_quota.isFreeTier) _loadQuota();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final petName = _pet?.name;
    final petConditions = _pet?.medicalConditions ?? [];

    return Scaffold(
      appBar: AppBar(
        title: Text(petName != null ? 'Chat · $petName' : 'Agente NutriVet'),
        actions: [
          if (_quota.badgeText != null)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: _QuotaBadge(quota: _quota),
            ),
        ],
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(28),
          child: Padding(
            padding: EdgeInsets.only(bottom: 4, left: 12, right: 12),
            child: Text(
              _disclaimer,
              style: TextStyle(fontSize: 10, color: Colors.white70),
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
      body: Column(
        children: [
          if (_loadingHistory)
            const LinearProgressIndicator(minHeight: 2),
          Expanded(
            child: _messages.isEmpty && !_loadingHistory
                ? _EmptyStateWithChips(
                    petName: petName,
                    conditions: petConditions,
                    onChipTap: (text) {
                      _msgCtrl.text = text;
                      _send();
                    },
                  )
                : ListView.builder(
                    controller: _scrollCtrl,
                    padding: const EdgeInsets.all(16),
                    itemCount: _messages.length,
                    itemBuilder: (context, i) =>
                        _MessageBubble(message: _messages[i]),
                  ),
          ),
          _InputBar(
            controller: _msgCtrl,
            sending: _sending,
            onSend: _send,
          ),
        ],
      ),
    );
  }
}

/// Estado vacío con chips de inicio de conversación contextuales.
class _EmptyStateWithChips extends StatelessWidget {
  const _EmptyStateWithChips({
    required this.petName,
    required this.conditions,
    required this.onChipTap,
  });

  final String? petName;
  final List<String> conditions;
  final void Function(String) onChipTap;

  List<String> _buildSuggestions() {
    final name = petName ?? 'mi mascota';
    final suggestions = [
      '¿Cuánto debe comer $name al día?',
      '¿Puede $name comer zanahoria?',
      '¿Cuáles son los mejores alimentos para $name?',
      '¿Qué alimentos debo evitar darle a $name?',
    ];
    if (conditions.isNotEmpty) {
      final cond = conditions.first.replaceAll('_', ' ');
      suggestions.insert(1, '¿Qué alimentos debo evitar con $cond?');
    }
    return suggestions.take(4).toList();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final suggestions = _buildSuggestions();

    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.chat_bubble_outline,
                size: 48, color: theme.colorScheme.primary.withOpacity(0.4)),
            const SizedBox(height: 12),
            Text(
              petName != null
                  ? '¿Tienes dudas sobre la nutrición de $petName?'
                  : 'Consulta sobre nutrición de tu mascota',
              style: theme.textTheme.titleSmall?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: suggestions
                  .map(
                    (s) => ActionChip(
                      label: Text(s, style: const TextStyle(fontSize: 13)),
                      onPressed: () => onChipTap(s),
                    ),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChatMessage {
  _ChatMessage({
    required this.text,
    required this.isUser,
    this.isError = false,
  });

  final String text;
  final bool isUser;
  final bool isError;
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({required this.message});

  final _ChatMessage message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isUser = message.isUser;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: isUser
              ? theme.colorScheme.primary
              : message.isError
                  ? theme.colorScheme.errorContainer
                  : theme.colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: isUser ? Radius.zero : null,
            bottomLeft: isUser ? null : Radius.zero,
          ),
        ),
        child: message.text.isEmpty
            ? _TypingDots()
            : isUser
                ? Text(
                    message.text,
                    style: const TextStyle(color: Colors.white),
                  )
                : MarkdownBody(
                    data: message.text,
                    styleSheet: MarkdownStyleSheet(
                      p: TextStyle(
                        color: theme.colorScheme.onSurface,
                        fontSize: 14,
                        height: 1.45,
                      ),
                      strong: TextStyle(
                        color: theme.colorScheme.onSurface,
                        fontWeight: FontWeight.w700,
                      ),
                      em: TextStyle(
                        color: theme.colorScheme.onSurface,
                        fontStyle: FontStyle.italic,
                      ),
                      listBullet: TextStyle(
                        color: theme.colorScheme.primary,
                        fontSize: 14,
                      ),
                      horizontalRuleDecoration: BoxDecoration(
                        border: Border(
                          top: BorderSide(
                            color: theme.colorScheme.outlineVariant,
                            width: 1,
                          ),
                        ),
                      ),
                      blockquote: TextStyle(
                        color: theme.colorScheme.onSurfaceVariant,
                        fontSize: 13,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                    softLineBreak: true,
                  ),
      ),
    );
  }
}

/// Animación de "escribiendo..." mientras llega la respuesta del agente.
class _TypingDots extends StatefulWidget {
  @override
  State<_TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<_TypingDots>
    with SingleTickerProviderStateMixin {
  late AnimationController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) {
            final offset = math.sin((_ctrl.value * 2 * math.pi) + (i * 1.0));
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 2),
              child: Transform.translate(
                offset: Offset(0, -4 * offset),
                child: const CircleAvatar(radius: 4),
              ),
            );
          }),
        );
      },
    );
  }
}

class _InputBar extends StatelessWidget {
  const _InputBar({
    required this.controller,
    required this.sending,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool sending;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                key: const ValueKey('chat_input'),
                controller: controller,
                decoration: InputDecoration(
                  hintText: 'Pregunta sobre nutrición...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                ),
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => onSend(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton.filled(
              key: const ValueKey('send_button'),
              onPressed: sending ? null : onSend,
              icon: sending
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }
}

/// Badge de cuota diaria visible solo para el tier Free.
/// Muestra "2/3 hoy" y cambia a rojo cuando se agota.
class _QuotaBadge extends StatelessWidget {
  const _QuotaBadge({required this.quota});

  final AgentQuota quota;

  @override
  Widget build(BuildContext context) {
    final text = quota.badgeText;
    if (text == null) return const SizedBox.shrink();

    final exhausted = !quota.canAsk;
    final color = exhausted ? Colors.red.shade300 : Colors.amber.shade300;

    return Tooltip(
      message: exhausted
          ? 'Límite diario alcanzado. Actualiza para acceso ilimitado.'
          : 'Preguntas restantes hoy (plan Free)',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: color.withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color, width: 1),
        ),
        child: Text(
          text,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: color,
          ),
        ),
      ),
    );
  }
}
