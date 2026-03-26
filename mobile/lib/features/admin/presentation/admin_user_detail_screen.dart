/// Panel admin — detalle y gestión de un usuario.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/admin_repository.dart';

part 'admin_user_detail_screen.g.dart';

@riverpod
Future<AdminUser> _adminUserDetail(Ref ref, String userId) =>
    ref.read(adminRepositoryProvider).getUserDetail(userId);

class AdminUserDetailScreen extends ConsumerWidget {
  const AdminUserDetailScreen({super.key, required this.userId});

  final String userId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final userAsync =
        ref.watch(_adminUserDetailProvider(userId));

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Detalle de usuario')),
      bottomNavigationBar: const AppFooter(),
      body: userAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (user) => _UserDetailBody(
          user: user,
          onChanged: () =>
              ref.invalidate(_adminUserDetailProvider(userId)),
        ),
      ),
    );
  }
}

class _UserDetailBody extends ConsumerWidget {
  const _UserDetailBody({required this.user, required this.onChanged});

  final AdminUser user;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // ── Encabezado ───────────────────────────────────────────────────────
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      radius: 28,
                      backgroundColor:
                          theme.colorScheme.primaryContainer,
                      child: Text(
                        user.role == 'vet'
                            ? '🩺'
                            : user.role == 'admin'
                                ? '⚙️'
                                : '🐾',
                        style: const TextStyle(fontSize: 28),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            user.displayName,
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: user.isActive
                                  ? null
                                  : theme.colorScheme.outline,
                            ),
                          ),
                          Text(
                            user.email,
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.outline,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    _Chip('Rol: ${user.role}', Colors.blue),
                    _Chip('Tier: ${user.tier}', Colors.deepPurple),
                    if (!user.isActive) _Chip('Inactivo', Colors.red),
                    if (user.vetStatus != null)
                      _Chip(
                        'Vet: ${user.vetStatus}',
                        user.vetStatus == 'approved'
                            ? Colors.green
                            : user.vetStatus == 'pending'
                                ? Colors.orange
                                : Colors.red,
                      ),
                  ],
                ),
                if (user.createdAt != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Registrado: ${_formatDate(user.createdAt!)}',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // ── Datos veterinarios ───────────────────────────────────────────────
        if (user.role == 'vet') ...[
          _SectionCard(
            title: 'Datos clínicos',
            children: [
              if (user.clinicName != null)
                _InfoRow('Clínica', user.clinicName!),
              if (user.specialization != null)
                _InfoRow('Especialización', user.specialization!),
              if (user.licenseNumber != null)
                _InfoRow('Matrícula', user.licenseNumber!),
              if (user.phone != null) _InfoRow('Teléfono', user.phone!),
            ],
          ),
          const SizedBox(height: 12),
        ],

        // ── Acciones ─────────────────────────────────────────────────────────
        _SectionCard(
          title: 'Cambiar tier',
          children: [
            _TierSelector(user: user, onChanged: onChanged),
          ],
        ),
        const SizedBox(height: 12),

        _SectionCard(
          title: 'Estado de cuenta',
          children: [
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                user.isActive
                    ? Icons.check_circle_outline
                    : Icons.block_outlined,
                color: user.isActive ? Colors.green : Colors.red,
              ),
              title: Text(
                user.isActive ? 'Cuenta activa' : 'Cuenta inactiva',
              ),
              subtitle: Text(
                user.isActive
                    ? 'El usuario puede acceder a la plataforma'
                    : 'El usuario no puede iniciar sesión',
                style: const TextStyle(fontSize: 12),
              ),
              trailing: OutlinedButton(
                onPressed: () =>
                    _toggleStatus(context, ref, user),
                style: OutlinedButton.styleFrom(
                  foregroundColor:
                      user.isActive ? Colors.red : Colors.green,
                ),
                child: Text(
                    user.isActive ? 'Desactivar' : 'Activar'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _toggleStatus(
      BuildContext context, WidgetRef ref, AdminUser user) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(user.isActive ? 'Desactivar usuario' : 'Activar usuario'),
        content: Text(
          user.isActive
              ? '¿Desactivar la cuenta de ${user.displayName}? No podrá iniciar sesión.'
              : '¿Activar la cuenta de ${user.displayName}?',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: user.isActive
                ? FilledButton.styleFrom(
                    backgroundColor: Colors.red)
                : null,
            child: Text(user.isActive ? 'Desactivar' : 'Activar'),
          ),
        ],
      ),
    );
    if (confirm != true) return;
    try {
      await ref
          .read(adminRepositoryProvider)
          .toggleUserStatus(user.userId);
      onChanged();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(user.isActive
                ? 'Usuario desactivado'
                : 'Usuario activado'),
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    }
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return iso;
    }
  }
}

class _TierSelector extends ConsumerStatefulWidget {
  const _TierSelector({required this.user, required this.onChanged});

  final AdminUser user;
  final VoidCallback onChanged;

  @override
  ConsumerState<_TierSelector> createState() => _TierSelectorState();
}

class _TierSelectorState extends ConsumerState<_TierSelector> {
  static const _tiers = ['free', 'basico', 'premium', 'vet'];
  late String _selected;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _selected = widget.user.tier;
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: DropdownButtonFormField<String>(
            value: _selected,
            items: _tiers
                .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                .toList(),
            onChanged: (v) {
              if (v != null) setState(() => _selected = v);
            },
            decoration: const InputDecoration(
              labelText: 'Tier',
              isDense: true,
            ),
          ),
        ),
        const SizedBox(width: 12),
        FilledButton(
          onPressed: _selected == widget.user.tier || _saving
              ? null
              : _save,
          child: _saving
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Guardar'),
        ),
      ],
    );
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      await ref
          .read(adminRepositoryProvider)
          .changeUserTier(widget.user.userId, _selected);
      widget.onChanged();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Tier actualizado a $_selected')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: $e')));
        setState(() => _selected = widget.user.tier);
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }
}

// ── Widgets auxiliares ────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...children,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value);

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: const TextStyle(
                  fontSize: 12, color: Colors.grey),
            ),
          ),
          Expanded(
            child: Text(value, style: const TextStyle(fontSize: 12)),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.label, this.color);

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
            fontSize: 11, color: color, fontWeight: FontWeight.w600),
      ),
    );
  }
}
