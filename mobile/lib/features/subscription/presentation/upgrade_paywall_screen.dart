/// Pantalla de upgrade — se muestra cuando el usuario Free alcanza su límite.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class UpgradePaywallScreen extends StatelessWidget {
  const UpgradePaywallScreen({super.key, this.reason});

  /// Motivo del bloqueo: 'plan_limit' | 'chat_limit'
  final String? reason;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isPlanLimit = reason != 'chat_limit';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Desbloquear más'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const SizedBox(height: 16),

              // Ilustración
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer.withOpacity(0.3),
                  shape: BoxShape.circle,
                ),
                child: Text(
                  isPlanLimit ? '📋' : '💬',
                  style: const TextStyle(fontSize: 52),
                ),
              ),
              const SizedBox(height: 24),

              Text(
                isPlanLimit
                    ? 'Alcanzaste el límite del plan gratuito'
                    : 'Alcanzaste tu límite de preguntas',
                style: theme.textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                isPlanLimit
                    ? 'Con el plan Free puedes generar 1 plan nutricional. '
                        'Actualiza para generar planes ilimitados para tu mascota.'
                    : 'Con el plan Free tienes 3 preguntas por día durante 3 días. '
                        'Actualiza para chat ilimitado con el agente NutriVet.',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.outline,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),

              // Cards de planes
              _PlanCard(
                name: 'Básico',
                price: '\$29.900 COP/mes',
                highlight: false,
                features: const [
                  '1 mascota',
                  '1 plan nuevo por mes',
                  'Chat ilimitado con el agente',
                  'Exportación PDF',
                ],
                onTap: () => context.push('/subscription'),
              ),
              const SizedBox(height: 12),
              _PlanCard(
                name: 'Premium',
                price: '\$59.900 COP/mes',
                highlight: true,
                features: const [
                  'Hasta 3 mascotas',
                  'Planes ilimitados',
                  'Chat ilimitado',
                  'Exportación PDF',
                  'Revisión veterinaria prioritaria',
                ],
                onTap: () => context.push('/subscription'),
              ),
              const SizedBox(height: 24),

              TextButton(
                onPressed: () => context.pop(),
                child: const Text('Continuar con el plan Free'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({
    required this.name,
    required this.price,
    required this.highlight,
    required this.features,
    required this.onTap,
  });

  final String name;
  final String price;
  final bool highlight;
  final List<String> features;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      elevation: highlight ? 4 : 1,
      color: highlight ? theme.colorScheme.primaryContainer : null,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: highlight
            ? BorderSide(color: theme.colorScheme.primary, width: 2)
            : BorderSide.none,
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Text(name,
                          style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: highlight
                                  ? theme.colorScheme.primary
                                  : null)),
                      if (highlight) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: theme.colorScheme.primary,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: const Text('Recomendado',
                              style: TextStyle(
                                  color: Colors.white, fontSize: 10)),
                        ),
                      ],
                    ],
                  ),
                  Text(price,
                      style: theme.textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: highlight ? theme.colorScheme.primary : null,
                      )),
                ],
              ),
              const SizedBox(height: 12),
              ...features.map(
                (f) => Padding(
                  padding: const EdgeInsets.only(bottom: 4),
                  child: Row(
                    children: [
                      Icon(Icons.check_circle,
                          size: 16,
                          color: highlight
                              ? theme.colorScheme.primary
                              : Colors.green),
                      const SizedBox(width: 8),
                      Text(f, style: const TextStyle(fontSize: 13)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: highlight
                    ? FilledButton(
                        onPressed: onTap,
                        child: const Text('Elegir Premium'),
                      )
                    : OutlinedButton(
                        onPressed: onTap,
                        child: const Text('Elegir Básico'),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
