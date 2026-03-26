/// Historial de pagos del usuario autenticado.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/widgets/app_footer.dart';
import '../../admin/data/admin_repository.dart';

part 'payment_history_screen.g.dart';

@riverpod
Future<List<PaymentRecord>> _myPayments(Ref ref) =>
    ref.read(adminRepositoryProvider).getMyPaymentHistory();

class PaymentHistoryScreen extends ConsumerWidget {
  const PaymentHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final paymentsAsync = ref.watch(_myPaymentsProvider);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Historial de pagos')),
      bottomNavigationBar: const AppFooter(),
      body: paymentsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (payments) => payments.isEmpty
            ? const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.receipt_long_outlined,
                        size: 48, color: Colors.grey),
                    SizedBox(height: 12),
                    Text('Sin pagos registrados',
                        style: TextStyle(color: Colors.grey)),
                    SizedBox(height: 4),
                    Text(
                      'Tu historial de transacciones aparecerá aquí',
                      style: TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                  ],
                ),
              )
            : ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: payments.length,
                separatorBuilder: (_, __) => const SizedBox(height: 4),
                itemBuilder: (_, i) => _PaymentTile(payment: payments[i]),
              ),
      ),
    );
  }
}

class _PaymentTile extends StatelessWidget {
  const _PaymentTile({required this.payment});

  final PaymentRecord payment;

  @override
  Widget build(BuildContext context) {
    final isApproved = payment.status == 'APPROVED';
    final statusColor = isApproved ? Colors.green : Colors.orange;
    final tierColor = switch (payment.tier) {
      'vet' || 'premium' => Colors.deepPurple,
      'basico' => Colors.green,
      _ => Colors.grey,
    };

    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: tierColor.withOpacity(0.12),
          child: Icon(
            Icons.workspace_premium_outlined,
            color: tierColor,
            size: 20,
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
              padding:
                  const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
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
              : '',
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
            isApproved ? 'Aprobado' : payment.status,
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
    final formatted = v.toStringAsFixed(0);
    final chars = formatted.split('').reversed.toList();
    final result = <String>[];
    for (var i = 0; i < chars.length; i++) {
      if (i > 0 && i % 3 == 0) result.add('.');
      result.add(chars[i]);
    }
    return result.reversed.join('');
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      const months = [
        '', 'ene', 'feb', 'mar', 'abr', 'may', 'jun',
        'jul', 'ago', 'sep', 'oct', 'nov', 'dic'
      ];
      return '${dt.day} ${months[dt.month]} ${dt.year}';
    } catch (_) {
      return iso;
    }
  }
}
