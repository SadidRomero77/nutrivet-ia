/// Pantalla que lista todos los planes de una mascota.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/plan_repository.dart';

part 'plan_list_screen.g.dart';

@riverpod
Future<List<PlanSummary>> _planList(Ref ref, String petId) async {
  final all = await ref.read(planRepositoryProvider).listPlans();
  return all.where((p) => p.petId == petId).toList();
}

class PlanListScreen extends ConsumerStatefulWidget {
  const PlanListScreen({super.key, required this.petId});

  final String petId;

  @override
  ConsumerState<PlanListScreen> createState() => _PlanListScreenState();
}

class _PlanListScreenState extends ConsumerState<PlanListScreen>
    with SingleTickerProviderStateMixin {
  String? _activeJobId;
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _checkActiveJob();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _checkActiveJob() async {
    final jobId = await ref
        .read(planRepositoryProvider)
        .getActiveJob(widget.petId);
    if (mounted) setState(() => _activeJobId = jobId);
  }

  @override
  Widget build(BuildContext context) {
    final plansAsync = ref.watch(_planListProvider(widget.petId));

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Planes nutricionales'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Todos'),
            Tab(text: 'Activos'),
            Tab(text: 'Archivados'),
          ],
        ),
      ),
      bottomNavigationBar: const AppFooter(),
      body: plansAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (allPlans) {
          final hasJob = _activeJobId != null;

          return TabBarView(
            controller: _tabController,
            children: [
              _PlanListView(
                plans: allPlans,
                hasJob: hasJob,
                petId: widget.petId,
                onRefresh: () async {
                  ref.invalidate(_planListProvider(widget.petId));
                  await _checkActiveJob();
                },
              ),
              _PlanListView(
                plans: allPlans
                    .where((p) => p.status == 'ACTIVE' || p.status == 'PENDING_VET' || p.status == 'UNDER_REVIEW')
                    .toList(),
                hasJob: hasJob,
                petId: widget.petId,
                onRefresh: () async {
                  ref.invalidate(_planListProvider(widget.petId));
                  await _checkActiveJob();
                },
              ),
              _PlanListView(
                plans: allPlans
                    .where((p) => p.status == 'ARCHIVED')
                    .toList(),
                hasJob: false,
                petId: widget.petId,
                onRefresh: () async {
                  ref.invalidate(_planListProvider(widget.petId));
                },
              ),
            ],
          );
        },
      ),
    );
  }
}

/// Vista de lista de planes con soporte de filtro por tab.
class _PlanListView extends StatelessWidget {
  const _PlanListView({
    required this.plans,
    required this.hasJob,
    required this.petId,
    required this.onRefresh,
  });

  final List<PlanSummary> plans;
  final bool hasJob;
  final String petId;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final isEmpty = plans.isEmpty && !hasJob;

    if (isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.description_outlined,
                  size: 48, color: Colors.grey.shade400),
              const SizedBox(height: 12),
              const Text(
                'No hay planes generados para esta mascota.',
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () =>
                    context.push('/plan/generate?petId=$petId'),
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Generar primer plan'),
              ),
            ],
          ),
        ),
      );
    }

    return Center(
      child: ConstrainedBox(
        constraints:
            const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
        child: RefreshIndicator(
          onRefresh: onRefresh,
          child: ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            itemCount: (hasJob ? 1 : 0) + plans.length + 1,
            itemBuilder: (context, i) {
              if (hasJob && i == 0) {
                return _InProgressJobCard(
                  onTap: () =>
                      context.push('/plan/generate?petId=$petId'),
                );
              }
              final planIdx = hasJob ? i - 1 : i;
              if (planIdx == plans.length) {
                return const Padding(
                  padding: EdgeInsets.only(top: 8, bottom: 16),
                  child: Text(
                    'NutriVet.IA es asesoría nutricional digital — '
                    'no reemplaza el diagnóstico médico veterinario.',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 11,
                      color: Colors.grey,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                );
              }
              return _PlanSummaryCard(plan: plans[planIdx]);
            },
          ),
        ),
      ),
    );
  }
}

/// Tarjeta que indica que hay un plan siendo generado en este momento.
class _InProgressJobCard extends StatelessWidget {
  const _InProgressJobCard({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.colorScheme.primary.withOpacity(0.4)),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: theme.colorScheme.primary,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Generando plan nutricional...',
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Toca para ver el progreso',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.outline,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right, color: theme.colorScheme.primary),
            ],
          ),
        ),
      ),
    );
  }
}

class _PlanSummaryCard extends StatelessWidget {
  const _PlanSummaryCard({required this.plan});

  final PlanSummary plan;

  @override
  Widget build(BuildContext context) {
    final (color, label) = switch (plan.status) {
      'ACTIVE' => (Colors.green, 'Activo'),
      'PENDING_VET' => (Colors.orange, 'Pendiente vet'),
      'UNDER_REVIEW' => (Colors.blue, 'En revisión'),
      'ARCHIVED' => (Colors.grey, 'Archivado'),
      _ => (Colors.grey, plan.status),
    };

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.15),
          child: Icon(
            plan.isActive ? Icons.check_circle : Icons.pending,
            color: color,
          ),
        ),
        title: Text(
          plan.modality == 'natural' ? 'Dieta Natural' : 'Concentrado',
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          '${plan.rerKcal.toStringAsFixed(0)} kcal RER · '
          '${plan.derKcal.toStringAsFixed(0)} kcal DER · $label',
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.push('/plan/${plan.planId}'),
      ),
    );
  }
}
