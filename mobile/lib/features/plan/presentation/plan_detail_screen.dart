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
            // Estado del plan
            _StatusBanner(status: plan.status),
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
  const _StatusBanner({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final (color, label, subtitle, icon) = switch (status) {
      'ACTIVE' => (Colors.green, 'Activo — listo para usar', null, Icons.check_circle),
      'PENDING_VET' => (
          Colors.orange,
          'Pendiente revisión veterinaria',
          'El veterinario revisará el plan antes de activarlo. '
              'Podrás exportarlo una vez que sea aprobado.',
          Icons.pending,
        ),
      'UNDER_REVIEW' => (Colors.blue, 'En revisión', null, Icons.rate_review),
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
              ],
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

/// Pantalla para generar un plan con polling automático.
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
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _statusMsg =
              'Error al iniciar la generación del plan. Intenta de nuevo.';
        });
      }
    }
  }

  Future<void> _pollUntilReady(PlanRepository repo) async {
    if (_jobId == null) return;
    // Hasta 10 minutos: 120 intentos × 5s = 600s
    for (var i = 0; i < 120; i++) {
      await Future<void>.delayed(const Duration(seconds: 5));
      if (!mounted) return;
      try {
        final job = await repo.getJobStatus(_jobId!);
        setState(() => _statusMsg = _jobStatusLabel(job.status));
        if (job.isReady && job.planId != null) {
          if (mounted) context.go('/plan/${job.planId}');
          return;
        }
        if (job.isFailed) {
          setState(() {
            _loading = false;
            _statusMsg =
                'No fue posible generar el plan. Intenta de nuevo o contacta soporte.';
          });
          return;
        }
      } on Exception {
        // Error de red durante polling — continuar hasta agotar intentos
      }
    }
    setState(() {
      _loading = false;
      _statusMsg = 'La generación está tomando más de lo esperado. '
          'Revisa "Mis planes" en unos minutos — el plan puede estar listo.';
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
      appBar: AppBar(
          title: NutrivetTitle('Generar plan — ${widget.petName}')),
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
              subtitle:
                  const Text('Ingredientes frescos con porciones en gramos'),
              value: 'natural',
              groupValue: _modality,
              onChanged:
                  _loading ? null : (v) => setState(() => _modality = v!),
            ),
            RadioListTile<String>(
              key: const ValueKey('modality_concentrado'),
              title: const Text('Concentrado comercial'),
              subtitle:
                  const Text('Criterios de selección del alimento ideal'),
              value: 'concentrado',
              groupValue: _modality,
              onChanged:
                  _loading ? null : (v) => setState(() => _modality = v!),
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
                label:
                    Text(_loading ? 'Generando...' : 'Generar plan nutricional'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
