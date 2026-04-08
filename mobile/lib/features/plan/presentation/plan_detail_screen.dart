/// Pantalla de detalle del plan nutricional.
///
/// REGLA 8: Disclaimer visible en todas las vistas del plan.
/// Solo planes ACTIVE muestran el botón de exportar.
/// Ingredientes: tap para solicitar sustitución via IA.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/plan_repository.dart';
import '../../auth/data/auth_repository.dart';

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
        // Siempre mostrar botón de volver — context.go reemplaza el stack
        // al terminar la generación, por lo que automaticallyImplyLeading
        // no lo muestra. Usamos canPop para decidir la acción.
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () =>
              context.canPop() ? context.pop() : context.go('/dashboard'),
        ),
        actions: [
          planAsync.whenOrNull(
            data: (plan) => plan.isActive
                ? IconButton(
                    key: const ValueKey('share_button'),
                    icon: const Icon(Icons.share),
                    tooltip: 'Compartir plan',
                    onPressed: () => _export(context, ref, plan),
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

  /// Comparte el plan como texto con información nutricional clave.
  /// Intenta exportar PDF desde el backend; si falla, comparte como texto.
  Future<void> _export(
      BuildContext context, WidgetRef ref, PlanDetail plan) async {
    try {
      await ref.read(planRepositoryProvider).exportAndShare(plan.planId);
    } catch (_) {
      // Backend export no disponible — compartir resumen en texto plano
      final sb = StringBuffer()
        ..writeln('🐾 Plan nutricional NutriVet.IA')
        ..writeln()
        ..writeln('Modalidad: ${plan.modality}')
        ..writeln(
            'Calorías: ${plan.perfilNutricional.derKcal.toStringAsFixed(0)} kcal/día')
        ..writeln(
            '  RER: ${plan.perfilNutricional.rerKcal.toStringAsFixed(0)} kcal')
        ..writeln();

      if (plan.ingredientes.isNotEmpty) {
        sb.writeln('Ingredientes principales:');
        for (final ing in plan.ingredientes.take(5)) {
          final qty = ing.cantidadG != null
              ? ' — ${ing.cantidadG!.toStringAsFixed(0)} g'
              : '';
          sb.writeln('  • ${ing.nombre}$qty');
        }
        if (plan.ingredientes.length > 5) {
          sb.writeln('  … y ${plan.ingredientes.length - 5} más');
        }
        sb.writeln();
      }

      sb.writeln(plan.disclaimer);

      if (context.mounted) {
        await Share.share(
          sb.toString(),
          subject: 'Plan nutricional NutriVet.IA',
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
            // Estado del plan
            _StatusBanner(status: plan.status, reviewDate: plan.reviewDate),
            // Comentario del vet si el plan fue devuelto (UNDER_REVIEW)
            if (plan.vetComment != null && plan.vetComment!.isNotEmpty) ...[
              const SizedBox(height: 8),
              _VetCommentBanner(comment: plan.vetComment!),
            ],
            const SizedBox(height: 16),

            // Objetivos clínicos
            if (plan.objetivosClinicos.isNotEmpty)
              _PlanSection(
                title: 'Objetivos del plan',
                icon: Icons.flag_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.objetivosClinicos
                      .map((obj) => _BulletItem(text: obj))
                      .toList(),
                ),
              ),

            // Perfil nutricional
            _PlanSection(
              title: 'Requerimiento calórico (NRC)',
              icon: Icons.local_fire_department_outlined,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: _CalorieBox(
                          label: 'RER',
                          value: '${plan.perfilNutricional.rerKcal.toStringAsFixed(1)} kcal',
                          subtitle: 'Requerimiento en reposo',
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: _CalorieBox(
                          label: 'DER',
                          value: '${plan.perfilNutricional.derKcal.toStringAsFixed(1)} kcal',
                          subtitle: 'Requerimiento diario',
                          highlight: true,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  _InfoRow('Fase', plan.perfilNutricional.weightPhase),
                  if (plan.perfilNutricional.racionTotalGDia != null)
                    _InfoRow(
                      'Ración total/día',
                      '${plan.perfilNutricional.racionTotalGDia!.toStringAsFixed(0)} g',
                    ),
                  if (plan.perfilNutricional.proteinPct != null)
                    _InfoRow(
                      'Proteína (MS)',
                      '${plan.perfilNutricional.proteinPct!.toStringAsFixed(1)}%',
                    ),
                  if (plan.perfilNutricional.fatPct != null)
                    _InfoRow(
                      'Grasa (MS)',
                      '${plan.perfilNutricional.fatPct!.toStringAsFixed(1)}%',
                    ),
                  if (plan.perfilNutricional.relacionCaP != null)
                    _InfoRow(
                      'Relación Ca:P',
                      plan.perfilNutricional.relacionCaP!.toStringAsFixed(2),
                    ),
                ],
              ),
            ),

            // Ingredientes prohibidos
            if (plan.ingredientesProhibidos.isNotEmpty)
              _PlanSection(
                title: 'Alimentos prohibidos para esta mascota',
                icon: Icons.block,
                iconColor: theme.colorScheme.error,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.ingredientesProhibidos
                      .map((item) => _BulletItem(
                            text: item,
                            color: theme.colorScheme.error,
                          ))
                      .toList(),
                ),
              ),

            // Ingredientes diarios — con botón de sustitución
            if (plan.ingredientes.isNotEmpty)
              _PlanSection(
                title: 'Ingredientes diarios',
                icon: Icons.restaurant_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Text(
                        'Toca un ingrediente para solicitar una alternativa',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.primary,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                    ...plan.ingredientes.map(
                      (ing) => _IngredientTile(
                        ingredient: ing,
                        planId: plan.planId,
                      ),
                    ),
                  ],
                ),
              ),

            // Cronograma diario
            if (plan.porciones.distribucionComidas.isNotEmpty)
              _PlanSection(
                title: 'Cronograma alimenticio diario',
                icon: Icons.schedule_outlined,
                child: Column(
                  children: [
                    // Cabecera de tabla
                    Container(
                      padding: const EdgeInsets.symmetric(
                          vertical: 6, horizontal: 8),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            flex: 2,
                            child: Text(
                              'Horario',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          Expanded(
                            child: Text(
                              'Proteína',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          Expanded(
                            child: Text(
                              'Carbo',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          Expanded(
                            child: Text(
                              'Vegetal',
                              style: theme.textTheme.labelSmall?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                        ],
                      ),
                    ),
                    ...plan.porciones.distribucionComidas
                        .asMap()
                        .entries
                        .map((entry) {
                      final comida = entry.value;
                      final isEven = entry.key.isEven;
                      return Container(
                        padding: const EdgeInsets.symmetric(
                            vertical: 6, horizontal: 8),
                        decoration: BoxDecoration(
                          color: isEven
                              ? theme.colorScheme.surfaceContainerHighest
                                  .withOpacity(0.3)
                              : null,
                        ),
                        child: Row(
                          children: [
                            Expanded(
                              flex: 2,
                              child: Text(
                                comida.horario,
                                style: theme.textTheme.bodySmall,
                              ),
                            ),
                            Expanded(
                              child: Text(
                                comida.proteinaG != null
                                    ? '${comida.proteinaG!.toStringAsFixed(0)}g'
                                    : '—',
                                style: theme.textTheme.bodySmall,
                                textAlign: TextAlign.center,
                              ),
                            ),
                            Expanded(
                              child: Text(
                                comida.carboG != null
                                    ? '${comida.carboG!.toStringAsFixed(0)}g'
                                    : '—',
                                style: theme.textTheme.bodySmall,
                                textAlign: TextAlign.center,
                              ),
                            ),
                            Expanded(
                              child: Text(
                                comida.vegeatalG != null
                                    ? '${comida.vegeatalG!.toStringAsFixed(0)}g'
                                    : '—',
                                style: theme.textTheme.bodySmall,
                                textAlign: TextAlign.center,
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                    if (plan.porciones.gPorComida != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: _InfoRow(
                          'Total por comida',
                          '${plan.porciones.gPorComida!.toStringAsFixed(0)} g',
                        ),
                      ),
                  ],
                ),
              )
            else if (plan.porciones.comidasPorDia > 0)
              _PlanSection(
                title: 'Distribución diaria',
                icon: Icons.schedule_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _InfoRow(
                        'Comidas por día', '${plan.porciones.comidasPorDia}'),
                    if (plan.porciones.gPorComida != null)
                      _InfoRow(
                        'Por comida',
                        '${plan.porciones.gPorComida!.toStringAsFixed(0)} g',
                      ),
                  ],
                ),
              ),

            // Instrucciones de preparación
            if (plan.instruccionesPreparacion.pasos.isNotEmpty)
              _PlanSection(
                title: 'Preparación',
                icon: Icons.kitchen_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (plan.instruccionesPreparacion.metodo != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: _InfoRow(
                          'Método',
                          plan.instruccionesPreparacion.metodo!,
                        ),
                      ),
                    if (plan.instruccionesPreparacion.tiempoPreparacionMinutos !=
                        null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Text(
                          'Tiempo estimado: ${plan.instruccionesPreparacion.tiempoPreparacionMinutos} min',
                          style: theme.textTheme.bodySmall,
                        ),
                      ),
                    ...plan.instruccionesPreparacion.pasos
                        .asMap()
                        .entries
                        .map(
                          (entry) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${entry.key + 1}. ',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.bold),
                                ),
                                Expanded(child: Text(entry.value)),
                              ],
                            ),
                          ),
                        ),
                  ],
                ),
              ),

            // Instrucciones por grupo
            if (plan.instruccionesPreparacion.instruccionesPorGrupo != null &&
                !plan.instruccionesPreparacion.instruccionesPorGrupo!.isEmpty)
              _PlanSection(
                title: 'Instrucciones por grupo de alimento',
                icon: Icons.info_outline,
                child: _InstruccionesPorGrupoWidget(
                  ipg: plan.instruccionesPreparacion.instruccionesPorGrupo!,
                ),
              ),

            // Adiciones permitidas
            if (plan.instruccionesPreparacion.adicionesPermitidas.isNotEmpty)
              _PlanSection(
                title: 'Adiciones permitidas',
                icon: Icons.spa_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.instruccionesPreparacion.adicionesPermitidas
                      .map((a) => _BulletItem(text: a, icon: Icons.check))
                      .toList(),
                ),
              ),

            // Almacenamiento
            if (plan.instruccionesPreparacion.almacenamiento != null)
              _PlanSection(
                title: 'Almacenamiento',
                icon: Icons.inventory_2_outlined,
                child: Text(plan.instruccionesPreparacion.almacenamiento!),
              ),

            // Suplementos
            if (plan.suplementos.isNotEmpty)
              _PlanSection(
                title: 'Suplementos prescritos',
                icon: Icons.medication_outlined,
                child: Column(
                  children: plan.suplementos
                      .map((s) => _SuplementoTile(suplemento: s))
                      .toList(),
                ),
              ),

            // Snacks saludables
            if (plan.snacksSaludables.isNotEmpty)
              _PlanSection(
                title: 'Snacks saludables aprobados',
                icon: Icons.cookie_outlined,
                child: Column(
                  children: plan.snacksSaludables
                      .map((s) => _SnackTile(snack: s))
                      .toList(),
                ),
              ),

            // Protocolo digestivo
            if (plan.protocloDigestivo.isNotEmpty)
              _PlanSection(
                title: 'Protocolo ante síntomas digestivos',
                icon: Icons.health_and_safety_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.protocloDigestivo
                      .map((p) => _BulletItem(text: p, icon: Icons.arrow_right))
                      .toList(),
                ),
              ),

            // Transición de dieta
            if (plan.transicionDieta != null &&
                plan.transicionDieta!.fases.isNotEmpty)
              _PlanSection(
                title:
                    'Protocolo de transición (${plan.transicionDieta!.duracionDias} días)',
                icon: Icons.swap_horiz_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ...plan.transicionDieta!.fases.map(
                      (fase) => Container(
                        margin: const EdgeInsets.only(bottom: 4),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.amber.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(6),
                          border: Border(
                            left: BorderSide(
                              color: Colors.amber.shade700,
                              width: 3,
                            ),
                          ),
                        ),
                        child: Row(
                          children: [
                            Text(
                              'Días ${fase.dias}:',
                              style: const TextStyle(
                                  fontWeight: FontWeight.bold, fontSize: 12),
                            ),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                fase.descripcion,
                                style: const TextStyle(fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    if (plan.transicionDieta!.senalesDeAlerta.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Señales de alerta — suspender si:',
                        style: theme.textTheme.labelMedium
                            ?.copyWith(color: theme.colorScheme.error),
                      ),
                      ...plan.transicionDieta!.senalesDeAlerta
                          .map((s) => _BulletItem(
                                text: s,
                                color: theme.colorScheme.error,
                                icon: Icons.warning_amber,
                              )),
                    ],
                  ],
                ),
              ),

            // Alertas para el propietario
            if (plan.alertasPropietario.isNotEmpty)
              _PlanSection(
                title: 'Alertas importantes',
                icon: Icons.notifications_active_outlined,
                iconColor: Colors.orange,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.alertasPropietario
                      .map((a) => _BulletItem(
                            text: a,
                            color: Colors.orange.shade800,
                            icon: Icons.info,
                          ))
                      .toList(),
                ),
              ),

            // Notas clínicas (solo si PENDING_VET)
            if (plan.notasClincias.isNotEmpty)
              _PlanSection(
                title: 'Notas para el veterinario',
                icon: Icons.medical_services_outlined,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: plan.notasClincias
                      .map((n) => _BulletItem(text: n))
                      .toList(),
                ),
              ),

            // Comentario del vet
            if (plan.vetComment != null) ...[
              const SizedBox(height: 8),
              Card(
                color: Theme.of(context).colorScheme.tertiaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Nota del veterinario',
                        style: theme.textTheme.labelLarge,
                      ),
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
                border: Border.all(
                    color: theme.colorScheme.outline.withOpacity(0.3)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child:
                        Text(plan.disclaimer, style: theme.textTheme.bodySmall),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Widgets auxiliares
// ---------------------------------------------------------------------------

class _CalorieBox extends StatelessWidget {
  const _CalorieBox({
    required this.label,
    required this.value,
    required this.subtitle,
    this.highlight = false,
  });

  final String label;
  final String value;
  final String subtitle;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        color: highlight
            ? theme.colorScheme.primary.withOpacity(0.12)
            : theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(8),
        border: highlight
            ? Border.all(color: theme.colorScheme.primary.withOpacity(0.4))
            : null,
      ),
      child: Column(
        children: [
          Text(label,
              style: theme.textTheme.labelSmall
                  ?.copyWith(color: theme.colorScheme.primary)),
          const SizedBox(height: 2),
          Text(
            value,
            style: theme.textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          Text(subtitle,
              style: theme.textTheme.labelSmall,
              textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _IngredientTile extends ConsumerWidget {
  const _IngredientTile({
    required this.ingredient,
    required this.planId,
  });

  final IngredientItem ingredient;
  final String planId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: () => _showSubstituteDialog(context, ref),
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 2),
        child: Row(
          children: [
            Icon(
              ingredient.fuente == 'vegetal'
                  ? Icons.eco_outlined
                  : ingredient.fuente == 'suplemento'
                      ? Icons.medication_outlined
                      : Icons.set_meal_outlined,
              size: 16,
              color: theme.colorScheme.primary.withOpacity(0.6),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    ingredient.nombre,
                    style: theme.textTheme.bodyMedium,
                  ),
                  if (ingredient.notas != null)
                    Text(
                      ingredient.notas!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                if (ingredient.cantidadG != null)
                  Text(
                    '${ingredient.cantidadG!.toStringAsFixed(0)} g',
                    style: theme.textTheme.bodyMedium
                        ?.copyWith(fontWeight: FontWeight.w600),
                  ),
                if (ingredient.kcal != null)
                  Text(
                    '${ingredient.kcal!.toStringAsFixed(0)} kcal',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withOpacity(0.5),
                    ),
                  ),
              ],
            ),
            const SizedBox(width: 4),
            Icon(
              Icons.swap_horiz,
              size: 16,
              color: theme.colorScheme.primary.withOpacity(0.4),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showSubstituteDialog(
    BuildContext context,
    WidgetRef ref,
  ) async {
    final substituteCtrl = TextEditingController();
    final result = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Solicitar alternativa'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ingrediente actual: ${ingredient.nombre}',
              style: Theme.of(ctx).textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 12),
            const Text(
              'La IA verificará que la alternativa no afecte el aporte '
              'nutricional ni viole restricciones médicas.',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: substituteCtrl,
              decoration: const InputDecoration(
                labelText: 'Alternativa sugerida (opcional)',
                hintText: 'Ej: salmón, pavo, calabacín...',
                border: OutlineInputBorder(),
              ),
              autofocus: true,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () =>
                Navigator.of(ctx).pop(substituteCtrl.text.trim()),
            child: const Text('Solicitar'),
          ),
        ],
      ),
    );

    if (result == null || !context.mounted) return;

    // Usar alternativa sugerida o pedir al agente que decida
    final substitute = result.isNotEmpty ? result : 'alternativa sugerida por IA';

    try {
      await ref.read(planRepositoryProvider).requestSubstitute(
            planId: planId,
            originalIngredient: ingredient.nombre,
            substituteIngredient: substitute,
          );
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              result.isNotEmpty
                  ? 'Sustitución de "${ingredient.nombre}" por "$result" procesada.'
                  : 'Solicitud procesada. El plan será actualizado.',
            ),
          ),
        );
        // Refrescar el plan
        ref.invalidate(_planDetailProvider(planId));
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'No fue posible procesar la sustitución. Intenta de nuevo.',
            ),
          ),
        );
      }
    }
  }
}

class _InstruccionesPorGrupoWidget extends StatelessWidget {
  const _InstruccionesPorGrupoWidget({required this.ipg});

  final InstruccionesPorGrupo ipg;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (ipg.proteinas.isNotEmpty) ...[
          _GroupHeader('Proteínas', Icons.set_meal_outlined),
          ...ipg.proteinas.map((i) => _BulletItem(text: i)),
          const SizedBox(height: 8),
        ],
        if (ipg.carbohidratos.isNotEmpty) ...[
          _GroupHeader('Carbohidratos', Icons.grain_outlined),
          ...ipg.carbohidratos.map((i) => _BulletItem(text: i)),
          const SizedBox(height: 8),
        ],
        if (ipg.vegetales.isNotEmpty) ...[
          _GroupHeader('Vegetales', Icons.eco_outlined),
          ...ipg.vegetales.map((i) => _BulletItem(text: i)),
        ],
      ],
    );
  }
}

class _GroupHeader extends StatelessWidget {
  const _GroupHeader(this.label, this.icon);

  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        children: [
          Icon(icon, size: 14, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 4),
          Text(
            label,
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.primary,
                ),
          ),
        ],
      ),
    );
  }
}

class _SuplementoTile extends StatelessWidget {
  const _SuplementoTile({required this.suplemento});

  final SupplementoItem suplemento;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.medication, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      suplemento.nombre,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    Text(
                      suplemento.dosis,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                Text(
                  '${suplemento.forma} · ${suplemento.frecuencia}',
                  style: theme.textTheme.bodySmall,
                ),
                Text(
                  suplemento.justificacion,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurface.withOpacity(0.6),
                    fontStyle: FontStyle.italic,
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

class _SnackTile extends StatelessWidget {
  const _SnackTile({required this.snack});

  final SnackSaludable snack;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.cookie, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      snack.nombre,
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    Text(
                      '${snack.cantidadG.toStringAsFixed(0)}g · ${snack.frecuencia}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ],
                ),
                Text(snack.descripcion, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BulletItem extends StatelessWidget {
  const _BulletItem({required this.text, this.color, this.icon});

  final String text;
  final Color? color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon ?? Icons.circle,
            size: icon != null ? 16 : 8,
            color: color ?? Theme.of(context).colorScheme.onSurface,
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              text,
              style: TextStyle(color: color),
            ),
          ),
        ],
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
  const _StatusBanner({required this.status, this.reviewDate});

  final String status;
  final DateTime? reviewDate;

  @override
  Widget build(BuildContext context) {
    final (color, label, subtitle, icon) = switch (status) {
      'ACTIVE' => (Colors.green, 'Activo — listo para usar', null, Icons.check_circle),
      'PENDING_VET' => (
          Colors.orange,
          'En revisión veterinaria',
          'Tu veterinario revisará y aprobará el plan. '
              'Tiempo estimado: 24-48 horas. '
              'Recibirás una notificación cuando esté listo.',
          Icons.hourglass_top,
        ),
      'UNDER_REVIEW' => (
          Colors.blue,
          'El veterinario devolvió el plan',
          'Tu vet dejó un comentario. Revisa la nota abajo.',
          Icons.rate_review,
        ),
      'ARCHIVED' => (Colors.grey, 'Archivado', null, Icons.archive),
      _ => (Colors.grey, status, null, Icons.info),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w600)),
                if (subtitle != null) ...[
                  const SizedBox(height: 4),
                  Text(subtitle, style: TextStyle(color: color.withOpacity(0.8), fontSize: 12)),
                ],
                if (status == 'ACTIVE' && reviewDate != null) ...[
                  const SizedBox(height: 4),
                  Builder(builder: (context) {
                    final now = DateTime.now();
                    final diff = reviewDate!.difference(now);
                    final daysLeft = diff.inDays;
                    final reviewText = daysLeft > 0
                        ? 'Revisión veterinaria programada en $daysLeft día${daysLeft == 1 ? '' : 's'}'
                        : 'Revisión veterinaria vencida — contacta a tu vet';
                    return Text(
                      reviewText,
                      style: TextStyle(
                        color: (daysLeft > 3 ? Colors.green : Colors.orange).withOpacity(0.9),
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    );
                  }),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Banner prominente que muestra el comentario del vet cuando devuelve el plan.
class _VetCommentBanner extends StatelessWidget {
  const _VetCommentBanner({required this.comment});

  final String comment;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: theme.colorScheme.secondary.withOpacity(0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.comment_outlined, size: 16, color: theme.colorScheme.secondary),
              const SizedBox(width: 6),
              Text(
                'Nota del veterinario',
                style: theme.textTheme.labelMedium?.copyWith(
                  color: theme.colorScheme.secondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            comment,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSecondaryContainer,
            ),
          ),
        ],
      ),
    );
  }
}

class _PlanSection extends StatelessWidget {
  const _PlanSection({
    required this.title,
    required this.child,
    this.icon,
    this.iconColor,
  });

  final String title;
  final Widget child;
  final IconData? icon;
  final Color? iconColor;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                if (icon != null) ...[
                  Icon(
                    icon,
                    size: 18,
                    color: iconColor ?? theme.colorScheme.primary,
                  ),
                  const SizedBox(width: 8),
                ],
                Expanded(
                  child: Text(
                    title,
                    style: theme.textTheme.titleSmall
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            child,
          ],
        ),
      ),
    );
  }
}

// Alias para acceder a authRepositoryProvider desde este archivo
final _authRepoProvider = authRepositoryProvider;

/// Pantalla para generar un plan con polling automático y progreso visual.
class GeneratePlanScreen extends ConsumerStatefulWidget {
  const GeneratePlanScreen(
      {super.key, required this.petId, required this.petName});

  final String petId;
  final String petName;

  @override
  ConsumerState<GeneratePlanScreen> createState() => _GeneratePlanScreenState();
}

class _GeneratePlanScreenState extends ConsumerState<GeneratePlanScreen> {
  String _modality = 'natural';
  bool _loading = false;
  bool _checkingQuota = true;
  bool _canGenerate = true;
  String? _jobId;
  String? _errorMsg;
  int _currentStep = 0; // 0=idle, 1=encolando, 2=calculando, 3=generando, 4=verificando
  String _progressMessage = ''; // Mensaje del backend en tiempo real

  static const _steps = [
    (Icons.schedule, 'Encolando solicitud'),
    (Icons.calculate_outlined, 'Calculando requerimientos NRC'),
    (Icons.auto_awesome, 'Generando plan con IA'),
    (Icons.shield_outlined, 'Verificando seguridad nutricional'),
  ];

  @override
  void initState() {
    super.initState();
    _checkQuota();
  }

  Future<void> _checkQuota() async {
    try {
      // Import is via auth_repository.dart — need to access it from plan context
      // We use the auth repo through the ref
      final authRepo = ref.read(_authRepoProvider);
      final usage = await authRepo.getTierUsage();
      if (mounted) {
        setState(() {
          _canGenerate = usage.canGeneratePlan;
          _checkingQuota = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _checkingQuota = false);
    }
  }

  Future<void> _generate() async {
    setState(() {
      _loading = true;
      _errorMsg = null;
      _currentStep = 1;
    });
    try {
      final repo = ref.read(planRepositoryProvider);
      final job = await repo.generatePlan(
        petId: widget.petId,
        modality: _modality,
      );
      _jobId = job.jobId;
      // Persistir para que plan_list_screen muestre el estado en curso
      await repo.saveActiveJob(widget.petId, job.jobId);
      await _pollUntilReady(repo);
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _currentStep = 0;
          _errorMsg = 'Error al iniciar la generación del plan. Intenta de nuevo.';
        });
      }
    }
  }

  Future<void> _pollUntilReady(PlanRepository repo) async {
    if (_jobId == null) return;
    // Hasta 10 minutos: 200 intentos × 3s = 600s
    for (var i = 0; i < 200; i++) {
      await Future<void>.delayed(const Duration(seconds: 3));
      if (!mounted) return;
      try {
        final job = await repo.getJobStatus(_jobId!);
        // Usar progreso real del backend si está disponible; sino, estimar por tiempo
        final step = job.progressStep > 0
            ? _backendStepToUiStep(job.progressStep)
            : _stepFromIteration(i, job.status);
        final message = job.progressMessage.isNotEmpty
            ? job.progressMessage
            : '';
        setState(() {
          _currentStep = step;
          _progressMessage = message;
        });
        if (job.isReady && job.planId != null) {
          await repo.clearActiveJob(widget.petId);
          if (mounted) context.go('/plan/${job.planId}');
          return;
        }
        if (job.isFailed) {
          await repo.clearActiveJob(widget.petId);
          setState(() {
            _loading = false;
            _currentStep = 0;
            _progressMessage = '';
            _errorMsg = 'No fue posible generar el plan. Intenta de nuevo o contacta soporte.';
          });
          return;
        }
      } on Exception {
        // Error de red durante polling — continuar hasta agotar intentos
      }
    }
    // Timeout — limpiar job y mostrar mensaje
    await repo.clearActiveJob(widget.petId);
    setState(() {
      _loading = false;
      _currentStep = 0;
      _progressMessage = '';
      _errorMsg = 'La generación está tomando más de lo esperado. '
          'Revisa "Mis planes" en unos minutos — el plan puede estar listo.';
    });
  }

  /// Mapea el paso del backend (1-10) al paso visual de la UI (1-4).
  int _backendStepToUiStep(int backendStep) {
    if (backendStep <= 2) return 1;
    if (backendStep <= 5) return 2;
    if (backendStep == 6) return 3;
    return 4; // pasos 7-10
  }

  int _stepFromIteration(int iteration, String status) {
    if (status == 'PROCESSING') {
      if (iteration < 3) return 2;
      if (iteration < 8) return 3;
      return 4;
    }
    return 1; // QUEUED
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (_checkingQuota) {
      return Scaffold(
        appBar: AppBar(title: NutrivetTitle('Generar plan — ${widget.petName}')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (!_canGenerate) {
      return Scaffold(
        appBar: AppBar(title: NutrivetTitle('Generar plan — ${widget.petName}')),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Text('📋', style: TextStyle(fontSize: 52)),
              const SizedBox(height: 16),
              Text(
                'Límite del plan gratuito alcanzado',
                style: theme.textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                'Con el plan Free puedes generar 1 plan nutricional. '
                'Actualiza para generar planes ilimitados.',
                style: theme.textTheme.bodyMedium
                    ?.copyWith(color: theme.colorScheme.outline),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () => context.push('/upgrade?reason=plan_limit'),
                  child: const Text('Ver planes de suscripción'),
                ),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => context.pop(),
                child: const Text('Volver'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
          title: NutrivetTitle('Generar plan — ${widget.petName}')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: _loading
            ? _GenerationProgress(
                currentStep: _currentStep,
                steps: _steps,
                progressMessage: _progressMessage,
              )
            : Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Modalidad del plan', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 16),
                  RadioListTile<String>(
                    key: const ValueKey('modality_natural'),
                    title: const Text('Dieta Natural (BARF/casera)'),
                    subtitle:
                        const Text('Ingredientes frescos con porciones en gramos'),
                    value: 'natural',
                    groupValue: _modality,
                    onChanged: (v) => setState(() => _modality = v!),
                  ),
                  RadioListTile<String>(
                    key: const ValueKey('modality_concentrado'),
                    title: const Text('Concentrado comercial'),
                    subtitle:
                        const Text('Criterios de selección del alimento ideal'),
                    value: 'concentrado',
                    groupValue: _modality,
                    onChanged: (v) => setState(() => _modality = v!),
                  ),
                  if (_errorMsg != null) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.errorContainer,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline, color: theme.colorScheme.error, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _errorMsg!,
                              style: TextStyle(color: theme.colorScheme.onErrorContainer),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      key: const ValueKey('generate_button'),
                      onPressed: _generate,
                      icon: const Icon(Icons.auto_awesome),
                      label: const Text('Generar plan nutricional'),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

/// Indicador visual de progreso durante la generación del plan.
class _GenerationProgress extends StatelessWidget {
  const _GenerationProgress({
    required this.currentStep,
    required this.steps,
    this.progressMessage = '',
  });

  final int currentStep;
  final List<(IconData, String)> steps;

  /// Mensaje en tiempo real proveniente del backend (vacío = no disponible).
  final String progressMessage;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(
              width: 64,
              height: 64,
              child: CircularProgressIndicator(strokeWidth: 3),
            ),
            const SizedBox(height: 32),
            Text(
              'Generando plan nutricional...',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 400),
              child: Text(
                progressMessage.isNotEmpty
                    ? progressMessage
                    : 'Esto puede tomar entre 30 segundos y 2 minutos.',
                key: ValueKey(progressMessage),
                style: theme.textTheme.bodySmall?.copyWith(
                  color: progressMessage.isNotEmpty
                      ? theme.colorScheme.primary
                      : theme.colorScheme.outline,
                ),
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: 32),
            ...steps.asMap().entries.map((entry) {
              final stepNum = entry.key + 1;
              final (icon, label) = entry.value;
              final isDone = stepNum < currentStep;
              final isActive = stepNum == currentStep;

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 300),
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isDone
                            ? Colors.green
                            : isActive
                                ? theme.colorScheme.primary
                                : theme.colorScheme.surfaceContainerHighest,
                      ),
                      child: Icon(
                        isDone ? Icons.check : icon,
                        size: 16,
                        color: isDone || isActive ? Colors.white : theme.colorScheme.outline,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        label,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: isDone
                              ? Colors.green
                              : isActive
                                  ? theme.colorScheme.primary
                                  : theme.colorScheme.outline,
                          fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                    ),
                    if (isActive)
                      SizedBox(
                        width: 14,
                        height: 14,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: theme.colorScheme.primary,
                        ),
                      ),
                    if (isDone)
                      const Icon(Icons.check_circle, size: 16, color: Colors.green),
                  ],
                ),
              );
            }),
            const SizedBox(height: 16),
            Text(
              'NutriVet.IA es asesoría nutricional digital — '
              'no reemplaza el diagnóstico médico veterinario.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
                fontStyle: FontStyle.italic,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
