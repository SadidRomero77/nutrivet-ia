/// Pantalla de perfil del usuario autenticado.
/// Muestra nombre, teléfono, email, rol, tier, datos clínicos (vet) y estadísticas.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/auth_repository.dart';

part 'profile_screen.g.dart';

@riverpod
Future<UserProfile> _profile(Ref ref) =>
    ref.read(authRepositoryProvider).getMe();

@riverpod
Future<UserStats> _stats(Ref ref) =>
    ref.read(authRepositoryProvider).getMyStats();

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(_profileProvider);
    final statsAsync = ref.watch(_statsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Mi perfil'),
        actions: [
          profileAsync.whenOrNull(
            data: (p) => IconButton(
              icon: const Icon(Icons.edit_outlined),
              tooltip: 'Editar perfil',
              onPressed: () async {
                await context.push('/profile/edit');
                ref.invalidate(_profileProvider);
                ref.invalidate(_statsProvider);
              },
            ),
          ) ?? const SizedBox.shrink(),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () => _confirmLogout(context, ref),
          ),
        ],
      ),
      bottomNavigationBar: const AppFooter(),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (profile) => ListView(
          padding: const EdgeInsets.all(24),
          children: [
            // Avatar
            Center(
              child: CircleAvatar(
                radius: 40,
                backgroundColor: theme.colorScheme.primaryContainer,
                child: Text(
                  profile.role == 'vet' ? '🩺' : '🐾',
                  style: const TextStyle(fontSize: 36),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Center(
              child: Text(
                profile.fullName ?? profile.email,
                style: theme.textTheme.titleLarge
                    ?.copyWith(fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
            ),
            Center(
              child: Chip(
                label: Text(
                  profile.role == 'vet' ? 'Veterinario' : 'Propietario',
                  style: const TextStyle(fontSize: 12),
                ),
                backgroundColor: theme.colorScheme.primaryContainer,
              ),
            ),
            const SizedBox(height: 24),

            // -- Estadísticas --
            statsAsync.whenOrNull(
              data: (stats) => _StatsCard(profile: profile, stats: stats),
            ) ?? const SizedBox.shrink(),

            const SizedBox(height: 12),

            // -- Información de contacto --
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Información de contacto',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    _InfoRow(
                      icon: Icons.email_outlined,
                      label: 'Email',
                      value: profile.email,
                    ),
                    if (profile.phone != null && profile.phone!.isNotEmpty)
                      _InfoRow(
                        icon: Icons.phone_outlined,
                        label: 'Teléfono',
                        value: profile.phone!,
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // -- Datos clínicos (solo vet) --
            if (profile.role == 'vet') ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Datos clínicos',
                          style: theme.textTheme.titleSmall
                              ?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      if (profile.clinicName != null &&
                          profile.clinicName!.isNotEmpty)
                        _InfoRow(
                          icon: Icons.local_hospital_outlined,
                          label: 'Clínica',
                          value: profile.clinicName!,
                        ),
                      if (profile.specialization != null &&
                          profile.specialization!.isNotEmpty)
                        _InfoRow(
                          icon: Icons.school_outlined,
                          label: 'Especialización',
                          value: profile.specialization!,
                        ),
                      if (profile.licenseNumber != null &&
                          profile.licenseNumber!.isNotEmpty)
                        _InfoRow(
                          icon: Icons.badge_outlined,
                          label: 'Cédula profesional',
                          value: profile.licenseNumber!,
                        ),
                      if ((profile.clinicName == null ||
                              profile.clinicName!.isEmpty) &&
                          (profile.specialization == null ||
                              profile.specialization!.isEmpty) &&
                          (profile.licenseNumber == null ||
                              profile.licenseNumber!.isEmpty))
                        TextButton.icon(
                          onPressed: () => context.push('/profile/edit'),
                          icon: const Icon(Icons.add, size: 16),
                          label: const Text('Agregar datos clínicos'),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
            ],

            // -- Suscripción --
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Suscripción',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    _InfoRow(
                      icon: Icons.workspace_premium_outlined,
                      label: 'Plan',
                      value: _tierLabel(profile.tier),
                    ),
                    if (_canUpgrade(profile)) ...[
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => context.push('/subscription'),
                          icon: const Icon(Icons.upgrade, size: 18),
                          label: Text(_upgradeLabel(profile.tier)),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // -- Seguridad --
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Seguridad',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.lock_outline),
                      title: const Text('Cambiar contraseña'),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push('/profile/change-password'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // -- Cerrar sesión --
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: () => _confirmLogout(context, ref),
                icon: Icon(Icons.logout,
                    size: 18, color: theme.colorScheme.error),
                label: Text('Cerrar sesión',
                    style: TextStyle(color: theme.colorScheme.error)),
                style: OutlinedButton.styleFrom(
                  side: BorderSide(color: theme.colorScheme.error),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  bool _canUpgrade(UserProfile p) =>
      p.role != 'vet' && (p.tier == 'free' || p.tier == 'basico');

  String _upgradeLabel(String tier) =>
      tier == 'free' ? 'Actualizar plan' : 'Subir a Premium';

  String _tierLabel(String tier) {
    switch (tier) {
      case 'free':
        return 'Free';
      case 'basico':
        return 'Básico — \$29.900 COP/mes';
      case 'premium':
        return 'Premium — \$59.900 COP/mes';
      case 'vet':
        return 'Veterinario — \$89.000 COP/mes';
      default:
        return tier;
    }
  }
}

Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
  final confirmed = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('Cerrar sesión'),
      content: const Text('¿Seguro que quieres cerrar sesión?'),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          child: const Text('Cancelar'),
        ),
        ElevatedButton(
          onPressed: () => Navigator.pop(ctx, true),
          child: const Text('Cerrar sesión'),
        ),
      ],
    ),
  );
  if (confirmed == true && context.mounted) {
    await ref.read(authRepositoryProvider).logout();
    if (context.mounted) context.go('/login');
  }
}

// -- Tarjeta de estadísticas --

class _StatsCard extends StatelessWidget {
  const _StatsCard({required this.profile, required this.stats});

  final UserProfile profile;
  final UserStats stats;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isVet = profile.role == 'vet';

    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 24),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: isVet
              ? [
                  _StatItem(
                    value: stats.patientsCount,
                    label: 'Pacientes',
                    icon: Icons.pets,
                    color: theme.colorScheme.primary,
                  ),
                  _StatItem(
                    value: stats.pendingPlansCount,
                    label: 'Pendientes',
                    icon: Icons.pending_actions,
                    color: Colors.orange,
                  ),
                ]
              : [
                  _StatItem(
                    value: stats.petsCount,
                    label: 'Mascotas',
                    icon: Icons.pets,
                    color: theme.colorScheme.primary,
                  ),
                  _StatItem(
                    value: stats.activePlansCount,
                    label: 'Planes activos',
                    icon: Icons.check_circle_outline,
                    color: Colors.green,
                  ),
                ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  const _StatItem({
    required this.value,
    required this.label,
    required this.icon,
    required this.color,
  });

  final int value;
  final String label;
  final IconData icon;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 6),
        Text(
          '$value',
          style: TextStyle(
              fontSize: 22, fontWeight: FontWeight.bold, color: color),
        ),
        Text(label,
            style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }
}

// -- Fila de información --

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: theme.colorScheme.primary),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: TextStyle(
                      fontSize: 11, color: theme.colorScheme.outline)),
              Text(value,
                  style: const TextStyle(
                      fontSize: 14, fontWeight: FontWeight.w500)),
            ],
          ),
        ],
      ),
    );
  }
}
