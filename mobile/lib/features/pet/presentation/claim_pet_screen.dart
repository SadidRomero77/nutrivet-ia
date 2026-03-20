/// Pantalla para que el propietario ingrese el código de vinculación
/// entregado por el veterinario al crear un paciente clínico (ClinicPet).
///
/// Llama a POST /v1/pets/claim con el código.
/// Al éxito, invalida el caché de mascotas y navega al dashboard.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/widgets/app_footer.dart';
import 'dashboard_screen.dart';

class ClaimPetScreen extends ConsumerStatefulWidget {
  const ClaimPetScreen({super.key});

  @override
  ConsumerState<ClaimPetScreen> createState() => _ClaimPetScreenState();
}

class _ClaimPetScreenState extends ConsumerState<ClaimPetScreen> {
  final _formKey = GlobalKey<FormState>();
  final _codeCtrl = TextEditingController();
  bool _loading = false;

  @override
  void dispose() {
    _codeCtrl.dispose();
    super.dispose();
  }

  Future<void> _claim() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    try {
      final dio = ref.read(apiClientProvider);
      await dio.post<Map<String, dynamic>>(
        '/v1/pets/claim',
        data: {'code': _codeCtrl.text.trim().toUpperCase()},
      );

      // Invalida la lista de mascotas para reflejar la nueva mascota reclamada
      ref.invalidate(petsProvider);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('¡Mascota vinculada correctamente!'),
            backgroundColor: Colors.green,
          ),
        );
        context.go('/dashboard');
      }
    } catch (e) {
      if (mounted) {
        final msg = e.toString().contains('expirado')
            ? 'El código ha expirado. Solicita uno nuevo al veterinario.'
            : e.toString().contains('usado')
                ? 'Este código ya fue utilizado.'
                : e.toString().contains('404') || e.toString().contains('no encontrado')
                    ? 'Código no encontrado. Verifica que esté escrito correctamente.'
                    : 'Error al vincular la mascota: $e';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg)),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Vincular mascota clínica')),
      bottomNavigationBar: const AppFooter(),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(24),
          children: [
            // Ilustración / ícono
            Center(
              child: Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.qr_code,
                  size: 40,
                  color: theme.colorScheme.primary,
                ),
              ),
            ),
            const SizedBox(height: 24),

            Text(
              'Ingresa el código del veterinario',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Tu veterinario generó un código de 8 caracteres al registrar '
              'a tu mascota. Ingrésalo aquí para vincularla a tu cuenta.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.outline,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 32),

            TextFormField(
              controller: _codeCtrl,
              textCapitalization: TextCapitalization.characters,
              textAlign: TextAlign.center,
              style: theme.textTheme.headlineMedium?.copyWith(
                letterSpacing: 6,
                fontWeight: FontWeight.bold,
              ),
              decoration: InputDecoration(
                labelText: 'Código de vinculación',
                hintText: 'XXXXXXXX',
                prefixIcon: const Icon(Icons.lock_open_outlined),
                counterText: '',
              ),
              maxLength: 8,
              validator: (v) {
                if (v == null || v.trim().length < 8) {
                  return 'El código debe tener 8 caracteres';
                }
                return null;
              },
            ),
            const SizedBox(height: 32),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _loading ? null : _claim,
                icon: _loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.link),
                label: Text(_loading ? 'Vinculando...' : 'Vincular mascota'),
              ),
            ),
            const SizedBox(height: 16),

            // Nota informativa
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.info_outline,
                      size: 16, color: theme.colorScheme.outline),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Una vez vinculada, podrás ver los planes nutricionales '
                      'que el veterinario genere para tu mascota.',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.outline,
                      ),
                    ),
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
