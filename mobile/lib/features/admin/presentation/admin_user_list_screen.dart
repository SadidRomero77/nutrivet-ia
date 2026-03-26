/// Panel admin — listado y búsqueda de usuarios.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/admin_repository.dart';

class AdminUserListScreen extends ConsumerStatefulWidget {
  const AdminUserListScreen({super.key});

  @override
  ConsumerState<AdminUserListScreen> createState() =>
      _AdminUserListScreenState();
}

class _AdminUserListScreenState extends ConsumerState<AdminUserListScreen> {
  final _searchCtrl = TextEditingController();
  String? _filterRole;
  String? _filterTier;
  List<AdminUser> _users = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final users = await ref.read(adminRepositoryProvider).listUsers(
            role: _filterRole,
            tier: _filterTier,
            q: _searchCtrl.text.trim().isEmpty ? null : _searchCtrl.text.trim(),
          );
      if (mounted) setState(() => _users = users);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Usuarios')),
      bottomNavigationBar: const AppFooter(),
      body: Column(
        children: [
          // Barra de búsqueda y filtros
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Column(
              children: [
                TextField(
                  controller: _searchCtrl,
                  decoration: InputDecoration(
                    hintText: 'Buscar por email o nombre...',
                    prefixIcon: const Icon(Icons.search, size: 20),
                    suffixIcon: _searchCtrl.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _searchCtrl.clear();
                              _load();
                            },
                          )
                        : null,
                    isDense: true,
                  ),
                  onSubmitted: (_) => _load(),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _FilterChip(
                      label: 'Rol',
                      value: _filterRole,
                      options: const ['owner', 'vet', 'admin'],
                      onChanged: (v) {
                        setState(() => _filterRole = v);
                        _load();
                      },
                    ),
                    const SizedBox(width: 8),
                    _FilterChip(
                      label: 'Tier',
                      value: _filterTier,
                      options: const ['free', 'basico', 'premium', 'vet'],
                      onChanged: (v) {
                        setState(() => _filterTier = v);
                        _load();
                      },
                    ),
                    const Spacer(),
                    TextButton.icon(
                      onPressed: _load,
                      icon: const Icon(Icons.refresh, size: 16),
                      label: const Text('Actualizar'),
                    ),
                  ],
                ),
              ],
            ),
          ),
          // Contador de resultados
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Row(
              children: [
                Text(
                  '${_users.length} usuario${_users.length != 1 ? 's' : ''}',
                  style: TextStyle(
                      fontSize: 12, color: theme.colorScheme.outline),
                ),
              ],
            ),
          ),
          // Lista
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _users.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.people_outline,
                                size: 48,
                                color: Colors.grey.shade300),
                            const SizedBox(height: 12),
                            const Text('Sin resultados',
                                style: TextStyle(color: Colors.grey)),
                          ],
                        ),
                      )
                    : ListView.separated(
                        padding: const EdgeInsets.all(16),
                        itemCount: _users.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 4),
                        itemBuilder: (_, i) =>
                            _UserTile(user: _users[i], onChanged: _load),
                      ),
          ),
        ],
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.value,
    required this.options,
    required this.onChanged,
  });

  final String label;
  final String? value;
  final List<String> options;
  final void Function(String?) onChanged;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () async {
        final selected = await showModalBottomSheet<String?>(
          context: context,
          builder: (ctx) => SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  title: Text('Filtrar por $label'),
                  trailing: TextButton(
                    onPressed: () => Navigator.pop(ctx, null),
                    child: const Text('Todos'),
                  ),
                ),
                ...options.map(
                  (o) => ListTile(
                    title: Text(o),
                    trailing: value == o
                        ? const Icon(Icons.check, color: Colors.green)
                        : null,
                    onTap: () => Navigator.pop(ctx, o),
                  ),
                ),
              ],
            ),
          ),
        );
        onChanged(selected);
      },
      child: Chip(
        label: Text(value != null ? '$label: $value' : label,
            style: const TextStyle(fontSize: 12)),
        avatar: const Icon(Icons.filter_list, size: 14),
        backgroundColor: value != null
            ? Theme.of(context).colorScheme.primaryContainer
            : null,
      ),
    );
  }
}

class _UserTile extends StatelessWidget {
  const _UserTile({required this.user, required this.onChanged});

  final AdminUser user;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final roleColor = switch (user.role) {
      'admin' => Colors.red,
      'vet' => Colors.teal,
      _ => Colors.blue,
    };
    final tierColor = switch (user.tier) {
      'vet' || 'premium' => Colors.deepPurple,
      'basico' => Colors.green,
      _ => Colors.grey,
    };

    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: roleColor.withOpacity(0.12),
          child: Text(
            user.role == 'vet'
                ? '🩺'
                : user.role == 'admin'
                    ? '⚙️'
                    : '🐾',
            style: const TextStyle(fontSize: 18),
          ),
        ),
        title: Text(
          user.displayName,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: user.isActive ? null : theme.colorScheme.outline,
          ),
        ),
        subtitle: Text(
          user.email,
          style: const TextStyle(fontSize: 12),
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            _Badge(user.role, roleColor),
            const SizedBox(height: 4),
            _Badge(user.tier, tierColor),
            if (!user.isActive)
              const Text('inactivo',
                  style: TextStyle(fontSize: 10, color: Colors.grey)),
            if (user.vetStatus == 'pending')
              const Text('pendiente',
                  style: TextStyle(
                      fontSize: 10,
                      color: Colors.orange,
                      fontWeight: FontWeight.bold)),
          ],
        ),
        onTap: () async {
          await context.push('/admin/users/${user.userId}');
          onChanged();
        },
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge(this.label, this.color);

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(
            fontSize: 10, color: color, fontWeight: FontWeight.w600),
      ),
    );
  }
}
