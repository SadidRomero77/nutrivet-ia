/// Dashboard principal del owner — lista de mascotas y acciones rápidas.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_drawer.dart';
import '../../../core/widgets/app_footer.dart';
import '../../auth/data/auth_repository.dart';
import '../data/pet_repository.dart';

part 'dashboard_screen.g.dart';

@riverpod
Future<List<PetModel>> pets(Ref ref) =>
    ref.read(petRepositoryProvider).listPets();

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final petsAsync = ref.watch(petsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Mis mascotas'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Cerrar sesión',
            onPressed: () async {
              try {
                await ref.read(authRepositoryProvider).logout();
              } catch (_) {}
              if (context.mounted) context.go('/login');
            },
          ),
        ],
      ),
      drawer: const AppDrawer(),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(petsProvider),
        child: petsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (err, _) =>
              Center(child: Text('Error al cargar mascotas: $err')),
          data: (pets) => pets.isEmpty
              ? _EmptyState(onAdd: () => context.push('/pet/new'))
              : _PetGrid(pets: pets),
        ),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      floatingActionButton: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Burbuja del agente conversacional — izquierda
            FloatingActionButton(
              key: const ValueKey('chat_fab'),
              heroTag: 'chat_fab',
              onPressed: () {
                final petsVal = ref.read(petsProvider).valueOrNull ?? [];
                if (petsVal.isEmpty) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Primero registra una mascota')),
                  );
                  return;
                }
                if (petsVal.length == 1) {
                  context.push('/chat?petId=${petsVal.first.petId}');
                  return;
                }
                showPetPickerSheet(
                  context: context,
                  pets: petsVal,
                  title: 'Consultar sobre...',
                  onPick: (pet) => context.push('/chat?petId=${pet.petId}'),
                );
              },
              backgroundColor: Theme.of(context).colorScheme.tertiary,
              foregroundColor: Colors.white,
              tooltip: 'Consultar al agente',
              child: const Icon(Icons.chat_bubble_outline),
            ),
            // Agregar mascota — derecha
            FloatingActionButton.extended(
              key: const ValueKey('add_pet_fab'),
              heroTag: 'add_pet_fab',
              onPressed: () => context.push('/pet/new'),
              icon: const Icon(Icons.add),
              label: const Text('Agregar mascota'),
            ),
          ],
        ),
      ),
      bottomNavigationBar: const AppFooter(),
    );
  }
}

/// Grid de mascotas — 1 columna en móvil, 2 columnas en tablet.
class _PetGrid extends StatelessWidget {
  const _PetGrid({required this.pets});

  final List<PetModel> pets;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= Breakpoints.tablet;
        return Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
            child: isWide
                ? GridView.builder(
                    padding: const EdgeInsets.all(16),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 2,
                      crossAxisSpacing: 12,
                      mainAxisSpacing: 12,
                      childAspectRatio: 2.8,
                    ),
                    itemCount: pets.length,
                    itemBuilder: (context, i) {
                      return _PetCard(pet: pets[i]);
                    },
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: pets.length,
                    itemBuilder: (context, i) {
                      return _PetCard(pet: pets[i]);
                    },
                  ),
          ),
        );
      },
    );
  }
}

class _PetCard extends StatelessWidget {
  const _PetCard({required this.pet});

  final PetModel pet;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Theme.of(context).colorScheme.primaryContainer,
          child: Text(
            pet.species == 'perro' ? '🐕' : '🐈',
            style: const TextStyle(fontSize: 24),
          ),
        ),
        title: Text(
          pet.name,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text('${pet.breed} · ${pet.weightKg} kg · BCS ${pet.bcs}/9'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/pet/${pet.petId}'),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onAdd});

  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: Breakpoints.maxFormWidth),
          child: Column(
            children: [
              const Text('🐾', style: TextStyle(fontSize: 56)),
              const SizedBox(height: 12),
              Text(
                '¡Bienvenido a NutriVet.IA!',
                style: theme.textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              Text(
                'Planes nutricionales personalizados para tu mascota,\nvalidados con estándares NRC/AAFCO.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.outline,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 28),
              // Guía de 3 pasos
              _OnboardingStep(
                step: 1,
                icon: Icons.pets,
                title: 'Registra tu mascota',
                description: 'Ingresa especie, raza, peso, condición corporal y antecedentes médicos.',
                color: theme.colorScheme.primary,
              ),
              _OnboardingStep(
                step: 2,
                icon: Icons.restaurant_menu,
                title: 'Genera su plan nutricional',
                description: 'El agente calcula sus requerimientos NRC y diseña un plan con ingredientes LATAM.',
                color: theme.colorScheme.secondary,
              ),
              _OnboardingStep(
                step: 3,
                icon: Icons.chat_bubble_outline,
                title: 'Consulta al agente',
                description: 'Resuelve dudas sobre nutrición en cualquier momento del plan.',
                color: theme.colorScheme.tertiary,
              ),
              const SizedBox(height: 28),
              const SizedBox.shrink(),
            ],
          ),
        ),
      ),
    );
  }
}

class _OnboardingStep extends StatelessWidget {
  const _OnboardingStep({
    required this.step,
    required this.icon,
    required this.title,
    required this.description,
    required this.color,
  });

  final int step;
  final IconData icon;
  final String title;
  final String description;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: color.withOpacity(0.12),
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$step. $title',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  description,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
