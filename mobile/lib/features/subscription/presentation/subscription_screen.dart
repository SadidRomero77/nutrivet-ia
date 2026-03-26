/// SubscriptionScreen — pantalla de planes y precios de NutriVet.IA.
///
/// Muestra los 4 tiers (Free, Básico, Premium, Vet) con sus características.
/// Al seleccionar un plan de pago, inicia el checkout PayU en el browser.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/subscription_repository.dart';

/// Información de cada tier para mostrar en la pantalla.
class _TierInfo {
  final String tier;
  final String name;
  final String price;
  final String period;
  final List<String> features;
  final bool isPopular;
  final Color color;

  const _TierInfo({
    required this.tier,
    required this.name,
    required this.price,
    required this.period,
    required this.features,
    this.isPopular = false,
    required this.color,
  });
}

const _tiers = [
  _TierInfo(
    tier: 'free',
    name: 'Free',
    price: '\$0',
    period: 'Siempre gratis',
    features: [
      '1 mascota',
      '1 plan nutricional total',
      '9 preguntas al agente (3/día × 3 días)',
      'Puede incluir mascota con condición médica',
    ],
    color: Color(0xFF78909C),
  ),
  _TierInfo(
    tier: 'basico',
    name: 'Básico',
    price: '\$29.900',
    period: 'COP/mes',
    features: [
      '1 mascota',
      'Planes ilimitados (1 nuevo/mes)',
      'Agente conversacional ilimitado',
      'Exportar plan a PDF',
      'Scanner de etiquetas nutricionales',
    ],
    color: Color(0xFF42A5F5),
  ),
  _TierInfo(
    tier: 'premium',
    name: 'Premium',
    price: '\$59.900',
    period: 'COP/mes',
    features: [
      'Hasta 3 mascotas',
      'Planes ilimitados',
      'Agente conversacional ilimitado',
      'Exportar y compartir PDFs',
      'Scanner de etiquetas nutricionales',
      'Historial completo de planes',
    ],
    isPopular: true,
    color: Color(0xFF66BB6A),
  ),
  _TierInfo(
    tier: 'vet',
    name: 'Vet',
    price: '\$89.000',
    period: 'COP/mes',
    features: [
      'Pacientes ilimitados',
      'Dashboard clínico para vets',
      'Revisión y firma de planes HITL',
      'Asistente IA en modo guía',
      'Trazabilidad clínica completa',
      'Exportar y compartir PDFs',
    ],
    color: Color(0xFFAB47BC),
  ),
];

class SubscriptionScreen extends ConsumerStatefulWidget {
  const SubscriptionScreen({super.key});

  @override
  ConsumerState<SubscriptionScreen> createState() => _SubscriptionScreenState();
}

class _SubscriptionScreenState extends ConsumerState<SubscriptionScreen> {
  bool _isProcessing = false;

  Future<void> _startCheckout(String tier) async {
    if (tier == 'free') return;

    setState(() => _isProcessing = true);

    try {
      final repo = ref.read(subscriptionRepositoryProvider);
      final result = await repo.createCheckout(tier);

      if (!mounted) return;

      if (result.hasRedirectUrl) {
        // Abrir PayU en el browser externo
        final uri = Uri.parse(result.redirectUrl);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.externalApplication);
          // Mostrar mensaje para que el usuario regrese después del pago
          if (mounted) {
            _showPaymentPendingSnackbar(tier);
          }
        } else {
          if (mounted) _showError('No se pudo abrir la página de pago.');
        }
      } else {
        // Modo dev: PayU no configurado → tier aprobado directamente
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Plan ${tier.capitalize()} activado (modo dev).'),
              backgroundColor: Colors.green,
            ),
          );
          // Refrescar estado de suscripción
          ref.invalidate(subscriptionStatusProvider);
        }
      }
    } catch (e) {
      if (mounted) _showError('Error iniciando el pago. Intenta de nuevo.');
    } finally {
      if (mounted) setState(() => _isProcessing = false);
    }
  }

  void _showPaymentPendingSnackbar(String tier) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Completá el pago en el browser para activar el plan '
          '${tier.capitalize()}. Al regresar, actualiza la app.',
        ),
        duration: const Duration(seconds: 8),
        action: SnackBarAction(
          label: 'Actualizar',
          onPressed: () => ref.invalidate(subscriptionStatusProvider),
        ),
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  @override
  Widget build(BuildContext context) {
    final statusAsync = ref.watch(subscriptionStatusProvider);
    final currentTier = statusAsync.valueOrNull?.tier ?? 'free';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Planes NutriVet.IA'),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          ListView(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            children: [
              _Header(currentTier: currentTier),
              const SizedBox(height: 20),
              ..._tiers.map(
                (tier) => _TierCard(
                  tierInfo: tier,
                  isCurrent: tier.tier == currentTier,
                  isProcessing: _isProcessing,
                  onSelect: () => _startCheckout(tier.tier),
                ),
              ),
              const SizedBox(height: 16),
              const _DisclaimerFooter(),
            ],
          ),
          if (_isProcessing)
            const ColoredBox(
              color: Colors.black26,
              child: Center(child: CircularProgressIndicator()),
            ),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  final String currentTier;
  const _Header({required this.currentTier});

  @override
  Widget build(BuildContext context) {
    final tierInfo = _tiers.firstWhere(
      (t) => t.tier == currentTier,
      orElse: () => _tiers.first,
    );
    return Column(
      children: [
        Text(
          'Tu plan actual: ${tierInfo.name}',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: tierInfo.color,
              ),
        ),
        const SizedBox(height: 4),
        Text(
          'Elige el plan que mejor se adapta a ti y tu mascota.',
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.black54,
              ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}

class _TierCard extends StatelessWidget {
  final _TierInfo tierInfo;
  final bool isCurrent;
  final bool isProcessing;
  final VoidCallback onSelect;

  const _TierCard({
    required this.tierInfo,
    required this.isCurrent,
    required this.isProcessing,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: tierInfo.isPopular ? 4 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isCurrent
              ? tierInfo.color
              : tierInfo.isPopular
                  ? tierInfo.color.withOpacity(0.5)
                  : Colors.transparent,
          width: isCurrent ? 2 : 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: tierInfo.color,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  tierInfo.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const Spacer(),
                if (tierInfo.isPopular)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: tierInfo.color,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      'Popular',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                if (isCurrent)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.green,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      'Activo',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  tierInfo.price,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: tierInfo.color,
                      ),
                ),
                const SizedBox(width: 4),
                Text(
                  tierInfo.period,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.black54,
                      ),
                ),
              ],
            ),
            const Divider(height: 20),
            ...tierInfo.features.map(
              (feature) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.check_circle,
                        size: 16, color: tierInfo.color),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        feature,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            if (!isCurrent && tierInfo.tier != 'free')
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: isProcessing ? null : onSelect,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: tierInfo.color,
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: Text('Activar plan ${tierInfo.name}'),
                ),
              )
            else if (isCurrent)
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: null,
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(color: tierInfo.color),
                  ),
                  child: Text(
                    'Plan actual',
                    style: TextStyle(color: tierInfo.color),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _DisclaimerFooter extends StatelessWidget {
  const _DisclaimerFooter();

  @override
  Widget build(BuildContext context) {
    return Text(
      'Los pagos son procesados de forma segura por PayU Colombia. '
      'NutriVet.IA no almacena datos de tarjetas. '
      'Puedes cancelar tu suscripción en cualquier momento.',
      style: Theme.of(context)
          .textTheme
          .bodySmall
          ?.copyWith(color: Colors.black38),
      textAlign: TextAlign.center,
    );
  }
}

extension _StringCapitalize on String {
  String capitalize() =>
      isEmpty ? this : '${this[0].toUpperCase()}${substring(1)}';
}
