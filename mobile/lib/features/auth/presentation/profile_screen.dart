/// Pantalla de perfil del usuario autenticado.
/// Muestra nombre, teléfono, email, rol y tier de suscripción.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/auth_repository.dart';

part 'profile_screen.g.dart';

@riverpod
Future<UserProfile> _profile(Ref ref) =>
    ref.read(authRepositoryProvider).getMe();

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(_profileProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Mi perfil')),
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
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

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
