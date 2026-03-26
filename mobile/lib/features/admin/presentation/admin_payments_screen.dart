/// Panel admin — historial de pagos del sistema.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/admin_repository.dart';

part 'admin_payments_screen.g.dart';

@riverpod
Future<List<PaymentRecord>> _adminPayments(Ref ref) =>
    ref.read(adminRepositoryProvider).listPayments();

class AdminPaymentsScreen extends ConsumerWidget {
  const AdminPaymentsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final paymentsAsync = ref.watch(_adminPaymentsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Pagos'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(_adminPaymentsProvider),
          ),
        ],
      ),
      bottomNavigationBar: const AppFooter(),
      body: paymentsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (payments) => payments.isEmpty
            ? const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.payments_outlined,
                        size: 48, color: Colors.grey),
                    SizedBox(height: 12),
                    Text('Sin pagos registrados',
                        style: TextStyle(color: Colors.grey)),
                  ],
                ),
              )
            : Column(
                children: [
                  // Resumen
                  _SummaryBanner(payments: payments),
                  // Lista
                  Expanded(
                    child: ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: payments.length,
                      separatorBuilder: (_, __) =>
                          const SizedBox(height: 4),
                      itemBuilder: (_, i) =>
                          _PaymentTile(payment: payments[i]),
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}

class _SummaryBanner extends StatelessWidget {
  const _SummaryBanner({required this.payments});

  final List<PaymentRecord> payments;

  @override
  Widget build(BuildContext context) {
    final approved = payments.where((p) => p.status == 'APPROVED');
    final totalCop =
        approved.fold<double>(0, (sum, p) => sum + p.amountCop);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _Stat('${payments.length}', 'Transacciones'),
          _Stat('${approved.length}', 'Aprobados'),
          _Stat('\$${_format(totalCop)} COP', 'Ingresos'),
        ],
      ),
    );
  }

  String _format(double v) {
    if (v >= 1000000) return '${(v / 1000000).toStringAsFixed(1)}M';
    if (v >= 1000) return '${(v / 1000).toStringAsFixed(0)}K';
    return v.toStringAsFixed(0);
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.value, this.label);

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
              fontWeight: FontWeight.bold, fontSize: 16),
        ),
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Colors.grey),
        ),
      ],
    );
  }
}

class _PaymentTile extends StatelessWidget {
  const _PaymentTile({required this.payment});

  final PaymentRecord payment;

  @override
  Widget build(BuildContext context) {
    final isApproved = payment.status == 'APPROVED';
    final statusColor = isApproved ? Colors.green : Colors.red;
    final tierColor = switch (payment.tier) {
      'vet' || 'premium' => Colors.deepPurple,
      'basico' => Colors.green,
      _ => Colors.grey,
    };

    return Card(
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: statusColor.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(
            isApproved ? Icons.check_circle_outline : Icons.cancel_outlined,
            color: statusColor,
            size: 22,
          ),
        ),
        title: Row(
          children: [
            Text(
              '\$${_formatCop(payment.amountCop)} COP',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: tierColor.withOpacity(0.12),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                payment.tier,
                style: TextStyle(
                    fontSize: 10,
                    color: tierColor,
                    fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        subtitle: Text(
          payment.createdAt != null
              ? _formatDate(payment.createdAt!)
              : payment.paymentId.substring(0, 8),
          style: const TextStyle(fontSize: 11),
        ),
        trailing: Container(
          padding:
              const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: statusColor.withOpacity(0.1),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            payment.status,
            style: TextStyle(
                fontSize: 10,
                color: statusColor,
                fontWeight: FontWeight.w600),
          ),
        ),
      ),
    );
  }

  String _formatCop(double v) {
    if (v >= 1000) return '${(v / 1000).toStringAsFixed(0)}.${((v % 1000) / 100).toStringAsFixed(0)}00';
    return v.toStringAsFixed(0);
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}
