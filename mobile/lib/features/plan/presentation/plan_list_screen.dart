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

class PlanListScreen extends ConsumerWidget {
  const PlanListScreen({super.key, required this.petId});

  final String petId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plansAsync = ref.watch(_planListProvider(petId));

    return Scaffold(
      appBar: AppBar(title: const Text('Planes nutricionales')),
      body: plansAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (plans) => plans.isEmpty
            ? const Center(
                child: Text('No hay planes generados para esta mascota.'),
              )
            : Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: plans.length + 1,
                    itemBuilder: (context, i) {
                      if (i == plans.length) return const AppFooter();
                      return _PlanSummaryCard(plan: plans[i]);
                    },
                  ),
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
