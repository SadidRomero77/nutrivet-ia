/// Dashboard principal del veterinario.
///
/// Tabs:
///   - Revisión: planes PENDING_VET pendientes de aprobación.
///   - Pacientes: ClinicPets creados por el vet.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_drawer.dart';
import '../../../core/widgets/app_footer.dart';
import '../../auth/data/auth_repository.dart';
import '../../pet/data/pet_repository.dart';
import '../data/vet_repository.dart';

part 'vet_dashboard_screen.g.dart';

@riverpod
Future<List<VetPendingPlan>> _pendingPlans(Ref ref) =>
    ref.read(vetRepositoryProvider).listPendingPlans();

@riverpod
Future<List<PetModel>> _vetPatients(Ref ref) =>
    ref.read(vetRepositoryProvider).listPatients();

class VetDashboardScreen extends ConsumerWidget {
  const VetDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const NutrivetTitle('Dashboard Veterinario'),
          actions: [
            IconButton(
              icon: const Icon(Icons.logout),
              tooltip: 'Cerrar sesión',
              onPressed: () async {
                await ref.read(authRepositoryProvider).logout();
                if (context.mounted) context.go('/login');
              },
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.pending_actions), text: 'Revisión'),
              Tab(icon: Icon(Icons.pets), text: 'Pacientes'),
            ],
          ),
        ),
        drawer: const AppDrawer(),
        body: const TabBarView(
          children: [
            _PendingPlansTab(),
            _PatientsTab(),
          ],
        ),
        floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
        floatingActionButton: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Burbuja del agente para el vet
              FloatingActionButton(
                key: const ValueKey('vet_chat_fab'),
                heroTag: 'vet_chat_fab',
                onPressed: () {
                  final patients =
                      ref.read(_vetPatientsProvider).valueOrNull ?? [];
                  if (patients.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                          content: Text('Agrega un paciente primero')),
                    );
                    return;
                  }
                  if (patients.length == 1) {
                    context.push('/chat?petId=${patients.first.petId}');
                    return;
                  }
                  showPetPickerSheet(
                    context: context,
                    pets: patients,
                    title: 'Consultar sobre...',
                    onPick: (pet) =>
                        context.push('/chat?petId=${pet.petId}'),
                  );
                },
                backgroundColor: Theme.of(context).colorScheme.tertiary,
                foregroundColor: Colors.white,
                tooltip: 'Consultar al agente',
                child: const Icon(Icons.chat_bubble_outline),
              ),
              FloatingActionButton.extended(
                key: const ValueKey('create_clinic_pet_fab'),
                heroTag: 'create_clinic_pet_fab',
                onPressed: () async {
                  await context.push('/vet/patients/new');
                  ref.invalidate(_vetPatientsProvider);
                },
                icon: const Icon(Icons.add),
                label: const Text('Agregar paciente'),
              ),
            ],
          ),
        ),
        bottomNavigationBar: const AppFooter(),
      ),
    );
  }
}

// ─── Tab: Planes pendientes ───────────────────────────────────────────────────

class _PendingPlansTab extends ConsumerWidget {
  const _PendingPlansTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plansAsync = ref.watch(_pendingPlansProvider);

    return plansAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => _ErrorRetry(
        message: 'Error al cargar planes: $err',
        onRetry: () => ref.invalidate(_pendingPlansProvider),
      ),
      data: (plans) => plans.isEmpty
          ? const _EmptyState(
              icon: Icons.check_circle_outline,
              color: Colors.green,
              message: 'No hay planes pendientes de revisión',
            )
          : RefreshIndicator(
              onRefresh: () async => ref.invalidate(_pendingPlansProvider),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: plans.length,
                    itemBuilder: (context, i) {
                      return _PendingPlanCard(
                        plan: plans[i],
                        onTap: () => context.push('/vet/plan/${plans[i].planId}'),
                      );
                    },
                  ),
                ),
              ),
            ),
    );
  }
}

class _PendingPlanCard extends StatelessWidget {
  const _PendingPlanCard({required this.plan, required this.onTap});

  final VetPendingPlan plan;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isNatural = plan.modality == 'natural';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      'Plan ${plan.planType}',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  Chip(
                    label: const Text('PENDIENTE'),
                    backgroundColor: Colors.orange.withOpacity(0.15),
                    labelStyle: const TextStyle(
                      color: Colors.orange,
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                    ),
                    padding: EdgeInsets.zero,
                    visualDensity: VisualDensity.compact,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                children: [
                  _InfoChip(
                    icon: Icons.local_fire_department,
                    label: 'RER ${plan.rerKcal.toStringAsFixed(0)} kcal',
                  ),
                  _InfoChip(
                    icon: Icons.fitness_center,
                    label: 'DER ${plan.derKcal.toStringAsFixed(0)} kcal',
                  ),
                  _InfoChip(
                    icon: isNatural ? Icons.eco : Icons.inventory_2_outlined,
                    label: isNatural ? 'Natural/BARF' : 'Concentrado',
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                'Modelo: ${plan.llmModel}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Toca para revisar y aprobar →',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Tab: Pacientes ───────────────────────────────────────────────────────────

class _PatientsTab extends ConsumerWidget {
  const _PatientsTab();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final patientsAsync = ref.watch(_vetPatientsProvider);

    return patientsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, _) => _ErrorRetry(
        message: 'Error al cargar pacientes: $err',
        onRetry: () => ref.invalidate(_vetPatientsProvider),
      ),
      data: (patients) => patients.isEmpty
          ? const _EmptyState(
              icon: Icons.pets,
              color: Colors.blue,
              message: 'Aún no tienes pacientes registrados\n'
                  'Usa el botón + para agregar tu primer paciente clínico.',
            )
          : RefreshIndicator(
              onRefresh: () async => ref.invalidate(_vetPatientsProvider),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 80),
                    itemCount: patients.length,
                    itemBuilder: (context, i) {
                      return _PatientCard(
                        pet: patients[i],
                        onTap: () =>
                            context.push('/vet/patient/${patients[i].petId}'),
                      );
                    },
                  ),
                ),
              ),
            ),
    );
  }
}

class _PatientCard extends StatelessWidget {
  const _PatientCard({required this.pet, required this.onTap});

  final PetModel pet;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: theme.colorScheme.primaryContainer,
          child: Text(
            pet.species == 'perro' ? '🐕' : '🐈',
            style: const TextStyle(fontSize: 22),
          ),
        ),
        title: Text(
          pet.name,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          '${pet.breed} · ${pet.weightKg} kg · BCS ${pet.bcs}/9',
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}

// ─── Widgets auxiliares ───────────────────────────────────────────────────────

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: Icon(icon, size: 14),
      label: Text(label, style: const TextStyle(fontSize: 11)),
      padding: EdgeInsets.zero,
      visualDensity: VisualDensity.compact,
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.icon,
    required this.color,
    required this.message,
  });

  final IconData icon;
  final Color color;
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 64, color: color),
            const SizedBox(height: 16),
            Text(
              message,
              style: Theme.of(context).textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorRetry extends StatelessWidget {
  const _ErrorRetry({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Reintentar'),
          ),
        ],
      ),
    );
  }
}
