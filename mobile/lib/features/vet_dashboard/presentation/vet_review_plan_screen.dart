/// Pantalla de revisión de plan nutricional para el veterinario.
///
/// Muestra el plan completo y permite Aprobar o Devolver con comentario.
/// REGLA 8: Disclaimer visible.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../../plan/data/plan_repository.dart';
import '../data/vet_repository.dart';

part 'vet_review_plan_screen.g.dart';

@riverpod
Future<PlanDetail> _reviewPlan(Ref ref, String planId) =>
    ref.read(planRepositoryProvider).getPlan(planId);

class VetReviewPlanScreen extends ConsumerWidget {
  const VetReviewPlanScreen({super.key, required this.planId});

  final String planId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final planAsync = ref.watch(_reviewPlanProvider(planId));

    return Scaffold(
      appBar: AppBar(title: const Text('Revisión veterinaria')),
      body: planAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) =>
            Center(child: Text('Error al cargar el plan: $err')),
        data: (plan) => _ReviewContent(plan: plan, planId: planId),
      ),
    );
  }
}

class _ReviewContent extends ConsumerStatefulWidget {
  const _ReviewContent({required this.plan, required this.planId});

  final PlanDetail plan;
  final String planId;

  @override
  ConsumerState<_ReviewContent> createState() => _ReviewContentState();
}

class _ReviewContentState extends ConsumerState<_ReviewContent> {
  bool _loading = false;

  Future<void> _approve() async {
    setState(() => _loading = true);
    try {
      await ref.read(vetRepositoryProvider).approvePlan(widget.planId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Plan aprobado correctamente'),
            backgroundColor: Colors.green,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al aprobar: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _return() async {
    final commentCtrl = TextEditingController();
    final comment = await showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Devolver plan'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ingresa un comentario obligatorio para el propietario:',
            ),
            const SizedBox(height: 12),
            TextField(
              controller: commentCtrl,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: 'Ej: Ajustar la cantidad de proteína por condición renal...',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              if (commentCtrl.text.trim().isNotEmpty) {
                Navigator.pop(context, commentCtrl.text.trim());
              }
            },
            child: const Text('Devolver'),
          ),
        ],
      ),
    );

    if (comment == null || !mounted) return;

    setState(() => _loading = true);
    try {
      await ref.read(vetRepositoryProvider).returnPlan(widget.planId, comment);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Plan devuelto al propietario')),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al devolver: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final plan = widget.plan;
    final isPending = plan.status == 'PENDING_VET';

    return Column(
      children: [
        // Disclaimer REGLA 8
        Container(
          width: double.infinity,
          color: theme.colorScheme.secondaryContainer,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Text(
            'NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario.',
            style: TextStyle(
              fontSize: 11,
              color: theme.colorScheme.onSecondaryContainer,
            ),
            textAlign: TextAlign.center,
          ),
        ),

        // Plan content
        Expanded(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
              child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Perfil calórico
              _Section(
                title: 'Perfil calórico',
                child: Wrap(
                  spacing: 12,
                  children: [
                    _KcalChip(
                        label: 'RER',
                        value: plan.perfilNutricional.rerKcal.toStringAsFixed(1)),
                    _KcalChip(
                        label: 'DER',
                        value: plan.perfilNutricional.derKcal.toStringAsFixed(1)),
                    _KcalChip(
                        label: 'Fase',
                        value: plan.perfilNutricional.weightPhase),
                  ],
                ),
              ),

              // Ingredientes
              if (plan.ingredientes.isNotEmpty)
                _Section(
                  title: 'Ingredientes',
                  child: Column(
                    children: plan.ingredientes
                        .map(
                          (i) => ListTile(
                            dense: true,
                            contentPadding: EdgeInsets.zero,
                            leading: const Icon(Icons.eco, size: 18),
                            title: Text(i.nombre),
                            trailing: i.cantidadG != null
                                ? Text(
                                    '${i.cantidadG!.toStringAsFixed(0)} g',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.bold),
                                  )
                                : null,
                          ),
                        )
                        .toList(),
                  ),
                ),

              // Porciones
              _Section(
                title: 'Porciones',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Comidas por día: ${plan.porciones.comidasPorDia}'),
                    if (plan.porciones.gPorComida != null)
                      Text(
                          'Por comida: ${plan.porciones.gPorComida!.toStringAsFixed(0)} g'),
                  ],
                ),
              ),

              // Pasos de preparación
              if (plan.instruccionesPreparacion.pasos.isNotEmpty)
                _Section(
                  title: 'Preparación',
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: plan.instruccionesPreparacion.pasos
                        .asMap()
                        .entries
                        .map(
                          (e) => Padding(
                            padding: const EdgeInsets.only(bottom: 4),
                            child: Text('${e.key + 1}. ${e.value}'),
                          ),
                        )
                        .toList(),
                  ),
                ),

              const SizedBox(height: 8),

              // Trazabilidad del agente (C4 — visible solo para vet)
              _AgentTraceSection(plan: plan),

              const SizedBox(height: 8),

              // Estado
              if (!isPending)
                Card(
                  color: Colors.green.shade50,
                  child: const ListTile(
                    leading: Icon(Icons.check_circle, color: Colors.green),
                    title: Text('Este plan ya fue aprobado'),
                  ),
                ),
              const AppFooter(),
            ],
          ),
            ),
          ),
        ),

        // Botones de acción (solo si está pendiente)
        if (isPending)
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _loading ? null : _return,
                      icon: const Icon(Icons.reply),
                      label: const Text('Devolver'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor:
                            Theme.of(context).colorScheme.error,
                        side: BorderSide(
                          color: Theme.of(context).colorScheme.error,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton.icon(
                      key: const ValueKey('approve_plan_button'),
                      onPressed: _loading ? null : _approve,
                      icon: _loading
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.check),
                      label: const Text('Aprobar plan'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.green,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 8),
            child,
          ],
        ),
      ),
    );
  }
}

/// Sección expandible con la trazabilidad del agente IA — visible solo para vet.
///
/// Muestra modelo LLM, RER/DER calculados, modalidad y restricciones aplicadas.
/// Permite al veterinario verificar que el agente tomó las decisiones correctas.
class _AgentTraceSection extends StatefulWidget {
  const _AgentTraceSection({required this.plan});

  final PlanDetail plan;

  @override
  State<_AgentTraceSection> createState() => _AgentTraceSectionState();
}

class _AgentTraceSectionState extends State<_AgentTraceSection> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final plan = widget.plan;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: theme.colorScheme.surfaceVariant.withOpacity(0.5),
      child: Column(
        children: [
          ListTile(
            leading: Icon(
              Icons.account_tree_outlined,
              color: theme.colorScheme.primary,
            ),
            title: Text(
              'Trazabilidad del agente IA',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              'Modelo: ${plan.llmModelUsed}',
              style: theme.textTheme.bodySmall,
            ),
            trailing: Icon(
              _expanded ? Icons.expand_less : Icons.expand_more,
            ),
            onTap: () => setState(() => _expanded = !_expanded),
          ),
          if (_expanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Divider(),
                  _TraceRow(
                    icon: Icons.smart_toy_outlined,
                    label: 'Modelo LLM',
                    value: plan.llmModelUsed,
                  ),
                  _TraceRow(
                    icon: Icons.local_fire_department_outlined,
                    label: 'RER calculado',
                    value:
                        '${plan.perfilNutricional.rerKcal.toStringAsFixed(1)} kcal/día (Python determinista)',
                  ),
                  _TraceRow(
                    icon: Icons.bolt_outlined,
                    label: 'DER calculado',
                    value:
                        '${plan.perfilNutricional.derKcal.toStringAsFixed(1)} kcal/día',
                  ),
                  _TraceRow(
                    icon: Icons.sync_alt,
                    label: 'Fase de peso',
                    value: plan.perfilNutricional.weightPhase,
                  ),
                  _TraceRow(
                    icon: Icons.restaurant_menu_outlined,
                    label: 'Modalidad',
                    value: plan.modality,
                  ),
                  if (plan.notasClincias.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Restricciones médicas aplicadas (hard-coded):',
                      style: theme.textTheme.labelMedium
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    ...plan.notasClincias.map(
                      (n) => Padding(
                        padding: const EdgeInsets.only(bottom: 2),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.check,
                                size: 14, color: Colors.green),
                            const SizedBox(width: 6),
                            Expanded(child: Text(n, style: theme.textTheme.bodySmall)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _TraceRow extends StatelessWidget {
  const _TraceRow({
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
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: theme.textTheme.bodySmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(value, style: theme.textTheme.bodySmall),
          ),
        ],
      ),
    );
  }
}

class _KcalChip extends StatelessWidget {
  const _KcalChip({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text('$label: $value'),
      backgroundColor: Theme.of(context).colorScheme.primaryContainer,
    );
  }
}
