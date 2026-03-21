/// Pantalla de registro de nuevo usuario (owner o veterinario).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/auth_repository.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  String _role = 'owner';
  bool _loading = false;
  bool _obscurePass = true;
  String? _error;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _phoneCtrl.dispose();
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final role = await ref.read(authRepositoryProvider).register(
            email: _emailCtrl.text.trim(),
            password: _passCtrl.text,
            fullName: _nameCtrl.text.trim(),
            phone: _phoneCtrl.text.trim(),
            role: _role,
          );
      if (mounted) {
        context.go(role == 'vet' ? '/vet/dashboard' : '/dashboard');
      }
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Registro')),
      bottomNavigationBar: const AppFooter(),
      body: ResponsiveBody(
        formLayout: true,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Form(
            key: _formKey,
            child: ListView(
              children: [
                const SizedBox(height: 16),
                // Selector de rol
                Card(
                  margin: EdgeInsets.zero,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '¿Cómo vas a usar NutriVet.IA?',
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: _RoleOption(
                                key: const ValueKey('role_owner'),
                                icon: Icons.pets,
                                label: 'Propietario',
                                subtitle: 'Tengo una mascota',
                                selected: _role == 'owner',
                                onTap: () => setState(() => _role = 'owner'),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: _RoleOption(
                                key: const ValueKey('role_vet'),
                                icon: Icons.local_hospital_outlined,
                                label: 'Veterinario',
                                subtitle: 'Soy médico vet.',
                                selected: _role == 'vet',
                                onTap: () => setState(() => _role = 'vet'),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                TextFormField(
                  key: const ValueKey('name_field'),
                  controller: _nameCtrl,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                    labelText: 'Nombre completo',
                    prefixIcon: Icon(Icons.person_outline),
                  ),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Nombre requerido' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const ValueKey('phone_field'),
                  controller: _phoneCtrl,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Teléfono móvil',
                    prefixIcon: Icon(Icons.phone_outlined),
                    hintText: '+57 300 000 0000',
                  ),
                  validator: (v) {
                    if (v == null || v.trim().isEmpty) return 'Teléfono requerido';
                    if (v.trim().length < 7) return 'Teléfono inválido';
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const ValueKey('email_field'),
                  controller: _emailCtrl,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Correo electrónico',
                    prefixIcon: Icon(Icons.email_outlined),
                  ),
                  validator: (v) =>
                      (v == null || !v.contains('@')) ? 'Email inválido' : null,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  key: const ValueKey('password_field'),
                  controller: _passCtrl,
                  obscureText: _obscurePass,
                  decoration: InputDecoration(
                    labelText: 'Contraseña',
                    prefixIcon: const Icon(Icons.lock_outline),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePass
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined,
                      ),
                      onPressed: () =>
                          setState(() => _obscurePass = !_obscurePass),
                      tooltip: _obscurePass ? 'Mostrar' : 'Ocultar',
                    ),
                  ),
                  validator: (v) {
                    if (v == null || v.length < 8) return 'Mínimo 8 caracteres';
                    if (!RegExp(r'[A-Z]').hasMatch(v)) {
                      return 'Debe contener al menos una mayúscula';
                    }
                    if (!RegExp(r'[0-9]').hasMatch(v)) {
                      return 'Debe contener al menos un número';
                    }
                    return null;
                  },
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    style: TextStyle(color: theme.colorScheme.error),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 24),
                ElevatedButton(
                  key: const ValueKey('register_button'),
                  onPressed: _loading ? null : _submit,
                  child: _loading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Crear cuenta'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RoleOption extends StatelessWidget {
  const _RoleOption({
    super.key,
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = selected ? theme.colorScheme.primary : theme.colorScheme.outline;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
        decoration: BoxDecoration(
          border: Border.all(
            color: selected ? theme.colorScheme.primary : theme.colorScheme.outlineVariant,
            width: selected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
          color: selected ? theme.colorScheme.primaryContainer.withOpacity(0.3) : null,
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 6),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: color,
                fontSize: 13,
              ),
            ),
            Text(
              subtitle,
              style: TextStyle(fontSize: 11, color: theme.colorScheme.outline),
            ),
          ],
        ),
      ),
    );
  }
}
