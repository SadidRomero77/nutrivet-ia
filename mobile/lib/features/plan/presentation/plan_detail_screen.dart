/// Pantalla de detalle del plan nutricional.
///
/// REGLA 8: Disclaimer visible en todas las vistas del plan.
/// Solo planes ACTIVE muestran el botón de exportar.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/plan_repository.dart';

part 'plan_detail_screen.g.dart';

@riverpod
Future<PlanDetail> _planDetail(Ref ref, String planId) =>
    ref.read(planRepositoryProvider).getPlan(planId);

class PlanDetailScreen extends ConsumerWidget {
  const PlanDetailScreen({super.key, required this.planId});

  final String planId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final planAsync = ref.watch(_planDetailProvider(planId));

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Plan nutricional'),
        actions: [
          planAsync.whenOrNull(
            data: (plan) => plan.isActive
                ? IconButton(
                    key: const ValueKey('share_button'),
                    icon: const Icon(Icons.share),
                    tooltip: 'Exportar y compartir',
                    onPressed: () => _export(context, ref, planId),
                  )
                : null,
          ) ??
              const SizedBox.shrink(),
        ],
      ),
      bottomNavigationBar: const AppFooter(),
      body: planAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) =>
            Center(child: Text('Error al cargar el plan: $err')),
        data: (plan) => _PlanContent(plan: plan),
      ),
    );
  }

  Future<void> _export(
    BuildContext context,
    WidgetRef ref,
    String planId,
  ) async {
    try {
      await ref.read(planRepositoryProvider).exportAndShare(planId);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Error al exportar el plan. Intenta de nuevo.'),
          ),
        );
      }
    }
  }
}

class _PlanContent extends StatelessWidget {
  const _PlanContent({required this.plan});

  final PlanDetail plan;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
        child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Estado
        _StatusBanner(status: plan.status),
        const SizedBox(height: 16),

        // Sección 1 — Perfil nutricional
        _PlanSection(
          title: '1. Requerimiento calórico',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _InfoRow('RER', '${plan.perfilNutricional.rerKcal.toStringAsFixed(1)} kcal/día'),
              _InfoRow('DER', '${plan.perfilNutricional.derKcal.toStringAsFixed(1)} kcal/día'),
              _InfoRow('Fase', plan.perfilNutricional.weightPhase),
              if (plan.perfilNutricional.proteinPct != null)
                _InfoRow('Proteína', '${plan.perfilNutricional.proteinPct!.toStringAsFixed(1)}%'),
              if (plan.perfilNutricional.fatPct != null)
                _InfoRow('Grasa', '${plan.perfilNutricional.fatPct!.toStringAsFixed(1)}%'),
            ],
          ),
        ),

        // Sección 2 — Ingredientes
        if (plan.ingredientes.isNotEmpty)
          _PlanSection(
            title: '2. Ingredientes diarios',
            child: Column(
              children: plan.ingredientes.map((ing) {
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(child: Text(ing.nombre)),
                      Text(
                        ing.cantidadGramos != null
                            ? '${ing.cantidadGramos!.toStringAsFixed(0)} g'
                            : '—',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),

        // Sección 3 — Porciones
        _PlanSection(
          title: '3. Distribución diaria',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _InfoRow('Comidas por día', '${plan.porciones.comidasPorDia}'),
              if (plan.porciones.porcionPorComidaGramos != null)
                _InfoRow(
                  'Por comida',
                  '${plan.porciones.porcionPorComidaGramos!.toStringAsFixed(0)} g',
                ),
              if (plan.porciones.notas != null)
                Text(plan.porciones.notas!, style: theme.textTheme.bodySmall),
            ],
          ),
        ),

        // Sección 4 — Instrucciones de preparación
        if (plan.instruccionesPreparacion.pasos.isNotEmpty)
          _PlanSection(
            title: '4. Preparación',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (plan.instruccionesPreparacion.tiempoEstimadoMinutos != null)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      'Tiempo estimado: ${plan.instruccionesPreparacion.tiempoEstimadoMinutos} min',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                ...plan.instruccionesPreparacion.pasos.asMap().entries.map(
                  (entry) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${entry.key + 1}. ',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        Expanded(child: Text(entry.value)),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

        // Sección 5 — Protocolo de transición (si aplica)
        if (plan.transicionDieta != null)
          _PlanSection(
            title: '5. Transición de dieta (${plan.transicionDieta!.duracionDias} días)',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _InfoRow('Semana 1', '${plan.transicionDieta!.semana1PctNuevo}% nuevo'),
                _InfoRow('Semana 2', '${plan.transicionDieta!.semana2PctNuevo}% nuevo'),
                _InfoRow('Semana 3', '${plan.transicionDieta!.semana3PctNuevo}% nuevo'),
                _InfoRow('Semana 4', '${plan.transicionDieta!.semana4PctNuevo}% nuevo'),
                if (plan.transicionDieta!.notas != null)
                  Text(plan.transicionDieta!.notas!, style: theme.textTheme.bodySmall),
              ],
            ),
          ),

        // Comentario del vet
        if (plan.vetComment != null) ...[
          const SizedBox(height: 8),
          Card(
            color: theme.colorScheme.tertiaryContainer,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Nota del veterinario', style: theme.textTheme.labelLarge),
                  const SizedBox(height: 4),
                  Text(plan.vetComment!),
                ],
              ),
            ),
          ),
        ],

        // REGLA 8 — Disclaimer obligatorio
        const SizedBox(height: 24),
        Container(
          key: const ValueKey('disclaimer_banner'),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: theme.colorScheme.errorContainer.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: theme.colorScheme.outline.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.info_outline, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(plan.disclaimer, style: theme.textTheme.bodySmall),
              ),
            ],
          ),
        ),
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
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.black54)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  const _StatusBanner({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final (color, label, icon) = switch (status) {
      'ACTIVE' => (Colors.green, 'Activo — listo para usar', Icons.check_circle),
      'PENDING_VET' => (Colors.orange, 'Pendiente revisión veterinaria', Icons.pending),
      'UNDER_REVIEW' => (Colors.blue, 'En revisión', Icons.rate_review),
      'ARCHIVED' => (Colors.grey, 'Archivado', Icons.archive),
      _ => (Colors.grey, status, Icons.info),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(width: 8),
          Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _PlanSection extends StatelessWidget {
  const _PlanSection({required this.title, required this.child});

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
              style: Theme.of(context)
                  .textTheme
                  .titleSmall
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            child,
          ],
        ),
      ),
    );
  }
}

/// Pantalla para generar un plan con polling automático.
class GeneratePlanScreen extends ConsumerStatefulWidget {
  const GeneratePlanScreen({super.key, required this.petId, required this.petName});

  final String petId;
  final String petName;

  @override
  ConsumerState<GeneratePlanScreen> createState() => _GeneratePlanScreenState();
}

class _GeneratePlanScreenState extends ConsumerState<GeneratePlanScreen> {
  String _modality = 'natural';
  bool _loading = false;
  String? _jobId;
  String? _statusMsg;

  Future<void> _generate() async {
    setState(() {
      _loading = true;
      _statusMsg = 'Encolando generación del plan...';
    });
    try {
      final repo = ref.read(planRepositoryProvider);
      final job = await repo.generatePlan(
        petId: widget.petId,
        modality: _modality,
      );
      _jobId = job.jobId;
      await _pollUntilReady(repo);
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _statusMsg = 'Error: $e';
        });
      }
    }
  }

  Future<void> _pollUntilReady(PlanRepository repo) async {
    if (_jobId == null) return;
    for (var i = 0; i < 60; i++) {
      await Future<void>.delayed(const Duration(seconds: 3));
      if (!mounted) return;
      final job = await repo.getJobStatus(_jobId!);
      setState(() => _statusMsg = _jobStatusLabel(job.status));
      if (job.isReady && job.planId != null) {
        if (mounted) context.go('/plan/${job.planId}');
        return;
      }
      if (job.isFailed) {
        setState(() {
          _loading = false;
          _statusMsg = 'No fue posible generar el plan. Intenta de nuevo o contacta soporte.';
        });
        return;
      }
    }
    setState(() {
      _loading = false;
      _statusMsg = 'Tiempo de espera agotado. Intenta de nuevo.';
    });
  }

  String _jobStatusLabel(String status) => switch (status) {
        'QUEUED' => 'En cola...',
        'PROCESSING' => 'Generando plan con IA...',
        'READY' => '¡Plan listo!',
        'FAILED' => 'Error en la generación',
        _ => status,
      };

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: NutrivetTitle('Generar plan — ${widget.petName}')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Modalidad del plan', style: theme.textTheme.titleMedium),
            const SizedBox(height: 16),
            RadioListTile<String>(
              key: const ValueKey('modality_natural'),
              title: const Text('Dieta Natural (BARF/casera)'),
              subtitle: const Text('Ingredientes frescos con porciones en gramos'),
              value: 'natural',
              groupValue: _modality,
              onChanged: _loading ? null : (v) => setState(() => _modality = v!),
            ),
            RadioListTile<String>(
              key: const ValueKey('modality_concentrado'),
              title: const Text('Concentrado comercial'),
              subtitle: const Text('Criterios de selección del alimento ideal'),
              value: 'concentrado',
              groupValue: _modality,
              onChanged: _loading ? null : (v) => setState(() => _modality = v!),
            ),
            const SizedBox(height: 32),
            if (_statusMsg != null) ...[
              Row(
                children: [
                  if (_loading) ...[
                    const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 12),
                  ],
                  Expanded(
                    child: Text(
                      _statusMsg!,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: _statusMsg!.startsWith('Error')
                            ? theme.colorScheme.error
                            : null,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
            ],
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                key: const ValueKey('generate_button'),
                onPressed: _loading ? null : _generate,
                icon: const Icon(Icons.auto_awesome),
                label: Text(_loading ? 'Generando...' : 'Generar plan nutricional'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
