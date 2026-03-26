/// Panel de administración — dashboard principal.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/admin_repository.dart';

part 'admin_dashboard_screen.g.dart';

@riverpod
Future<AdminStats> _adminStats(Ref ref) =>
    ref.read(adminRepositoryProvider).getStats();

class AdminDashboardScreen extends ConsumerWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statsAsync = ref.watch(_adminStatsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Panel Admin'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(_adminStatsProvider),
          ),
        ],
      ),
      bottomNavigationBar: const AppFooter(),
      body: statsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (stats) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Alerta si hay vets pendientes
            if (stats.vetsPending > 0)
              _AlertBanner(
                message:
                    '${stats.vetsPending} veterinario${stats.vetsPending > 1 ? 's' : ''} pendiente${stats.vetsPending > 1 ? 's' : ''} de aprobación',
                onTap: () => context.push('/admin/vets/pending'),
              ),

            const SizedBox(height: 8),

            // Grid de métricas
            Text('Usuarios',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _MetricsGrid(children: [
              _MetricCard(
                label: 'Total usuarios',
                value: stats.totalUsers,
                icon: Icons.people_outline,
                color: theme.colorScheme.primary,
              ),
              _MetricCard(
                label: 'Propietarios',
                value: stats.ownersCount,
                icon: Icons.person_outline,
                color: Colors.blue,
              ),
              _MetricCard(
                label: 'Veterinarios',
                value: stats.vetsCount,
                icon: Icons.local_hospital_outlined,
                color: Colors.teal,
              ),
              _MetricCard(
                label: 'Vets pendientes',
                value: stats.vetsPending,
                icon: Icons.pending_actions,
                color: Colors.orange,
                onTap: stats.vetsPending > 0
                    ? () => context.push('/admin/vets/pending')
                    : null,
              ),
            ]),
            const SizedBox(height: 16),

            Text('Negocio',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _MetricsGrid(children: [
              _MetricCard(
                label: 'Suscripciones activas',
                value: stats.activeSubscriptions,
                icon: Icons.workspace_premium_outlined,
                color: Colors.deepPurple,
              ),
              _MetricCard(
                label: 'Pagos aprobados',
                value: stats.totalPayments,
                icon: Icons.payments_outlined,
                color: Colors.green,
              ),
            ]),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: const Icon(Icons.attach_money, color: Colors.green),
                title: const Text('Ingresos totales'),
                trailing: Text(
                  '\$${_formatCop(stats.totalRevenueCop)} COP',
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 15),
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Acciones rápidas
            Text('Acciones rápidas',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            _QuickActions(),
          ],
        ),
      ),
    );
  }

  String _formatCop(double value) {
    if (value >= 1000000) {
      return '${(value / 1000000).toStringAsFixed(1)}M';
    }
    if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(0)}K';
    }
    return value.toStringAsFixed(0);
  }
}

class _AlertBanner extends StatelessWidget {
  const _AlertBanner({required this.message, required this.onTap});

  final String message;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      color: Colors.orange.shade50,
      child: ListTile(
        leading: const Icon(Icons.warning_amber_rounded, color: Colors.orange),
        title: Text(message,
            style: const TextStyle(
                fontWeight: FontWeight.w600, color: Colors.orange)),
        trailing: const Icon(Icons.chevron_right, color: Colors.orange),
        onTap: onTap,
      ),
    );
  }
}

class _MetricsGrid extends StatelessWidget {
  const _MetricsGrid({required this.children});
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 8,
      mainAxisSpacing: 8,
      childAspectRatio: 1.6,
      children: children,
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.onTap,
  });

  final String label;
  final int value;
  final IconData icon;
  final Color color;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Icon(icon, color: color, size: 22),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('$value',
                      style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.bold,
                          color: color)),
                  Text(label,
                      style: const TextStyle(
                          fontSize: 11, color: Colors.grey)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _ActionTile(
          icon: Icons.people_outline,
          title: 'Gestionar usuarios',
          subtitle: 'Ver, cambiar tier, activar/desactivar',
          onTap: () => context.push('/admin/users'),
        ),
        _ActionTile(
          icon: Icons.person_add_outlined,
          title: 'Crear veterinario',
          subtitle: 'Cuenta vet verificada directamente',
          onTap: () => context.push('/admin/vets/new'),
        ),
        _ActionTile(
          icon: Icons.pending_actions,
          title: 'Vets pendientes',
          subtitle: 'Aprobar o rechazar solicitudes',
          onTap: () => context.push('/admin/vets/pending'),
        ),
        _ActionTile(
          icon: Icons.payments_outlined,
          title: 'Pagos',
          subtitle: 'Historial de transacciones PayU',
          onTap: () => context.push('/admin/payments'),
        ),
      ],
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: theme.colorScheme.primary),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle,
            style: const TextStyle(fontSize: 12, color: Colors.grey)),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
