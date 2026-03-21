/// Drawer lateral (menú hamburguesa) de NutriVet.IA.
///
/// Accesos rápidos: Mis mascotas, Mis planes, Generar plan,
/// Mi veterinario, Vincular mascota clínica, Cerrar sesión.
///
/// Para secciones que requieren petId (planes, generar plan, chat)
/// muestra un selector de mascota si el usuario tiene más de una.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../features/auth/data/auth_repository.dart';
import '../../features/pet/data/pet_repository.dart';
import '../../features/pet/presentation/dashboard_screen.dart';
import '../../features/vet_dashboard/data/vet_repository.dart';

part 'app_drawer.g.dart';

@riverpod
Future<UserProfile> _myProfile(Ref ref) =>
    ref.read(authRepositoryProvider).getMe();

class AppDrawer extends ConsumerWidget {
  const AppDrawer({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final profileAsync = ref.watch(_myProfileProvider);
    final profile = profileAsync.valueOrNull;
    final isVet = profile?.role == 'vet';

    // Carga síncrona: owners usan petsProvider, vets usan vetPatientsProvider
    final pets = isVet
        ? <PetModel>[]
        : (ref.watch(petsProvider).valueOrNull ?? []);
    final vetPets = isVet
        ? (ref.watch(vetPatientsProvider).valueOrNull ?? <PetModel>[])
        : <PetModel>[];

    return Drawer(
      child: Column(
        children: [
          // ── Header con branding ───────────────────────────────────────────
          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: theme.colorScheme.primary,
            ),
            padding: const EdgeInsets.fromLTRB(16, 44, 16, 18),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Image.asset(
                  'assets/images/Logo.png',
                  height: 140,
                ),
                const SizedBox(height: 10),
                Text(
                  'NutriVet.IA',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.primaryContainer,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(height: 3),
                const Text(
                  'Nutrición inteligente para tus mascotas',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.white70,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (profile?.fullName != null) ...[
                  const SizedBox(height: 8),
                  Text(
                    profile!.fullName!,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: Colors.white,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ],
            ),
          ),

          // ── Ítems de navegación ──────────────────────────────────────────
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                const SizedBox(height: 8),

                if (isVet) ...[
                  // ── Menú veterinario ────────────────────────────────────
                  _DrawerItem(
                    icon: Icons.pending_actions_outlined,
                    title: 'Planes pendientes',
                    onTap: () {
                      Navigator.pop(context);
                      context.go('/vet/dashboard');
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.pets_outlined,
                    title: 'Mis pacientes',
                    onTap: () {
                      Navigator.pop(context);
                      context.go('/vet/dashboard');
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.person_add_outlined,
                    title: 'Agregar paciente',
                    onTap: () {
                      Navigator.pop(context);
                      context.push('/vet/patients/new');
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.auto_awesome_outlined,
                    title: 'Generar plan',
                    onTap: () {
                      Navigator.pop(context);
                      if (vetPets.isEmpty) {
                        _snackNoMascota(context);
                        return;
                      }
                      if (vetPets.length == 1) {
                        context.push(
                          '/plan/generate?petId=${vetPets.first.petId}'
                          '&petName=${Uri.encodeComponent(vetPets.first.name)}',
                        );
                        return;
                      }
                      showPetPickerSheet(
                        context: context,
                        pets: vetPets,
                        title: 'Generar plan para...',
                        onPick: (pet) => context.push(
                          '/plan/generate?petId=${pet.petId}'
                          '&petName=${Uri.encodeComponent(pet.name)}',
                        ),
                      );
                    },
                  ),
                  _DrawerItem(
                    icon: Icons.chat_bubble_outline,
                    title: 'Consultar al agente',
                    onTap: () {
                      Navigator.pop(context);
                      if (vetPets.isEmpty) {
                        _snackNoMascota(context);
                        return;
                      }
                      if (vetPets.length == 1) {
                        context.push('/chat?petId=${vetPets.first.petId}');
                        return;
                      }
                      showPetPickerSheet(
                        context: context,
                        pets: vetPets,
                        title: 'Consultar sobre...',
                        onPick: (pet) =>
                            context.push('/chat?petId=${pet.petId}'),
                      );
                    },
                  ),
                ] else ...[
                  // ── Menú propietario ─────────────────────────────────────
                  _DrawerItem(
                    icon: Icons.pets_outlined,
                    title: 'Mis mascotas',
                    onTap: () {
                      Navigator.pop(context);
                      context.go('/dashboard');
                    },
                  ),

                  _DrawerItem(
                    icon: Icons.description_outlined,
                    title: 'Mis planes',
                    onTap: () {
                      Navigator.pop(context);
                      if (pets.isEmpty) {
                        _snackNoMascota(context);
                        return;
                      }
                      if (pets.length == 1) {
                        context.push('/plans?petId=${pets.first.petId}');
                        return;
                      }
                      showPetPickerSheet(
                        context: context,
                        pets: pets,
                        title: 'Ver planes de...',
                        onPick: (pet) =>
                            context.push('/plans?petId=${pet.petId}'),
                      );
                    },
                  ),

                  _DrawerItem(
                    icon: Icons.auto_awesome_outlined,
                    title: 'Generar plan',
                    onTap: () {
                      Navigator.pop(context);
                      if (pets.isEmpty) {
                        _snackNoMascota(context);
                        return;
                      }
                      if (pets.length == 1) {
                        context.push(
                          '/plan/generate?petId=${pets.first.petId}'
                          '&petName=${Uri.encodeComponent(pets.first.name)}',
                        );
                        return;
                      }
                      showPetPickerSheet(
                        context: context,
                        pets: pets,
                        title: 'Generar plan para...',
                        onPick: (pet) => context.push(
                          '/plan/generate?petId=${pet.petId}'
                          '&petName=${Uri.encodeComponent(pet.name)}',
                        ),
                      );
                    },
                  ),

                  _DrawerItem(
                    icon: Icons.medical_services_outlined,
                    title: 'Mi veterinario',
                    onTap: () {
                      Navigator.pop(context);
                      _showVetInfoSheet(context, ref, pets);
                    },
                  ),
                ],

                const Divider(height: 24),

                _DrawerItem(
                  icon: Icons.account_circle_outlined,
                  title: 'Mi perfil',
                  subtitle: profile?.email,
                  onTap: () {
                    Navigator.pop(context);
                    context.push('/profile');
                  },
                ),

                if (!isVet) ...[
                  _DrawerItem(
                    icon: Icons.qr_code_scanner_outlined,
                    title: 'Vincular mascota clínica',
                    subtitle: 'Código del veterinario',
                    onTap: () {
                      Navigator.pop(context);
                      context.push('/pets/claim');
                    },
                  ),

                  _DrawerItem(
                    icon: Icons.document_scanner_outlined,
                    title: 'Escanear alimento',
                    onTap: () {
                      Navigator.pop(context);
                      if (pets.isEmpty) {
                        _snackNoMascota(context);
                        return;
                      }
                      if (pets.length == 1) {
                        context.push('/scanner?petId=${pets.first.petId}');
                        return;
                      }
                      showPetPickerSheet(
                        context: context,
                        pets: pets,
                        title: 'Escanear para...',
                        onPick: (pet) =>
                            context.push('/scanner?petId=${pet.petId}'),
                      );
                    },
                  ),
                ],
              ],
            ),
          ),

          // ── Cerrar sesión al fondo ────────────────────────────────────────
          const Divider(height: 1),
          _DrawerItem(
            icon: Icons.logout,
            title: 'Cerrar sesión',
            iconColor: Theme.of(context).colorScheme.error,
            onTap: () async {
              Navigator.pop(context);
              await ref.read(authRepositoryProvider).logout();
              if (context.mounted) context.go('/login');
            },
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  void _snackNoMascota(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Primero registra una mascota'),
      ),
    );
  }
}

/// Muestra un bottom sheet para seleccionar una mascota.
/// Reutilizable desde cualquier pantalla.
void showPetPickerSheet({
  required BuildContext context,
  required List<PetModel> pets,
  required String title,
  required void Function(PetModel pet) onPick,
}) {
  showModalBottomSheet<void>(
    context: context,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (ctx) {
      final theme = Theme.of(ctx);
      return SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle
            Container(
              margin: const EdgeInsets.only(top: 12),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: theme.colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
              child: Text(
                title,
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
            ),
            const Divider(height: 1),
            ...pets.map(
              (pet) => ListTile(
                leading: CircleAvatar(
                  backgroundColor: theme.colorScheme.primaryContainer,
                  child: Text(
                    pet.species == 'perro' ? '🐕' : '🐈',
                    style: const TextStyle(fontSize: 20),
                  ),
                ),
                title: Text(pet.name,
                    style: const TextStyle(fontWeight: FontWeight.w600)),
                subtitle: Text('${pet.breed} · ${pet.weightKg} kg'),
                onTap: () {
                  Navigator.pop(ctx);
                  onPick(pet);
                },
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      );
    },
  );
}

// ── Pantalla informativa "Mi veterinario" ────────────────────────────────────

void _showVetInfoSheet(BuildContext context, WidgetRef ref, List<PetModel> pets) {
  final pending = pets.where((p) => p.medicalConditions.isNotEmpty).toList();
  // Buscar vet_id en las mascotas clínicas que tengan uno
  final vetId = pets
      .map((p) => p.vetId)
      .where((id) => id != null)
      .firstOrNull;

  showModalBottomSheet<void>(
    context: context,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    isScrollControlled: true,
    builder: (ctx) {
      final theme = Theme.of(ctx);
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.outlineVariant,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              Row(
                children: [
                  Icon(Icons.medical_services,
                      color: theme.colorScheme.primary, size: 28),
                  const SizedBox(width: 12),
                  Text(
                    'Mi veterinario',
                    style: theme.textTheme.titleLarge
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Vet info card (if linked)
              if (vetId != null)
                FutureBuilder<UserProfile>(
                  future: ref.read(authRepositoryProvider).getVetProfile(vetId),
                  builder: (ctx2, snap) {
                    if (snap.connectionState == ConnectionState.waiting) {
                      return const Center(
                          child: CircularProgressIndicator());
                    }
                    final vet = snap.data;
                    return Container(
                      padding: const EdgeInsets.all(14),
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primaryContainer
                            .withAlpha(120),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          CircleAvatar(
                            backgroundColor: theme.colorScheme.primary,
                            child: const Icon(Icons.local_hospital,
                                color: Colors.white, size: 18),
                          ),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                vet?.fullName ?? 'Veterinario certificado',
                                style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14),
                              ),
                              if (vet?.phone != null)
                                Text(vet!.phone!,
                                    style: TextStyle(
                                        fontSize: 12,
                                        color: theme.colorScheme.outline)),
                              Text(
                                'BAMPYSVET, Bogotá',
                                style: TextStyle(
                                    fontSize: 11,
                                    color: theme.colorScheme.outline),
                              ),
                            ],
                          ),
                        ],
                      ),
                    );
                  },
                ),

              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer.withAlpha(100),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline,
                        size: 18, color: theme.colorScheme.primary),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Cuando tu mascota tiene condiciones médicas, su plan '
                        'nutricional es revisado y aprobado por un veterinario '
                        'certificado antes de activarse.',
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              if (pending.isNotEmpty) ...[
                Text(
                  'Mascotas con condiciones médicas',
                  style: theme.textTheme.labelLarge
                      ?.copyWith(color: theme.colorScheme.outline),
                ),
                const SizedBox(height: 8),
                ...pending.map(
                  (pet) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: CircleAvatar(
                      backgroundColor:
                          theme.colorScheme.tertiaryContainer,
                      child: Text(
                        pet.species == 'perro' ? '🐕' : '🐈',
                        style: const TextStyle(fontSize: 18),
                      ),
                    ),
                    title: Text(pet.name),
                    subtitle: Text(
                      pet.medicalConditions.take(2).join(', ') +
                          (pet.medicalConditions.length > 2 ? '...' : ''),
                      style: TextStyle(
                          fontSize: 11,
                          color: theme.colorScheme.tertiary),
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {
                      Navigator.pop(ctx);
                      context.push('/pet/${pet.petId}');
                    },
                  ),
                ),
                const SizedBox(height: 8),
              ] else ...[
                Text(
                  'No tienes mascotas con condiciones médicas registradas.',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                ),
                const SizedBox(height: 16),
              ],

              Text(
                'Piloto clínico: BAMPYSVET, Bogotá',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
            ],
          ),
        ),
      );
    },
  );
}

// ── Widget auxiliar para ítems del drawer ────────────────────────────────────

class _DrawerItem extends StatelessWidget {
  const _DrawerItem({
    required this.icon,
    required this.title,
    required this.onTap,
    this.subtitle,
    this.iconColor,
  });

  final IconData icon;
  final String title;
  final String? subtitle;
  final VoidCallback onTap;
  final Color? iconColor;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListTile(
      leading: Icon(icon, color: iconColor ?? theme.colorScheme.primary),
      title: Text(title),
      subtitle: subtitle != null
          ? Text(subtitle!,
              style: theme.textTheme.bodySmall
                  ?.copyWith(color: theme.colorScheme.outline))
          : null,
      onTap: onTap,
      minVerticalPadding: 8,
    );
  }
}
