/// Pantalla de inicio de sesión.
library;

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/auth_repository.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _loading = false;
  bool _obscurePass = true;
  String? _error;
  // Guard contra doble-submit: isométrico al flag _loading pero se setea
  // de forma síncrona ANTES del setState para evitar race entre taps rápidos.
  bool _submitting = false;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    // Guard síncrono: previene doble submit antes de que setState reconstruya el botón
    if (_submitting) return;
    _submitting = true;

    if (!_formKey.currentState!.validate()) {
      _submitting = false;
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    String role;
    try {
      role = await ref.read(authRepositoryProvider).login(
            email: _emailCtrl.text.trim(),
            password: _passCtrl.text,
          );
    } catch (e) {
      String msg;
      if (e is DioException && e.response?.statusCode == 401) {
        msg = 'Email o contraseña incorrectos.';
      } else if (e is DioException &&
          (e.type == DioExceptionType.connectionError ||
              e.type == DioExceptionType.connectionTimeout ||
              e.type == DioExceptionType.unknown)) {
        msg = 'Sin conexión. Verifica tu red e intenta de nuevo.';
      } else {
        msg = 'Error al iniciar sesión. Intenta de nuevo.';
      }
      if (mounted) setState(() => _error = msg);
      if (mounted) setState(() => _loading = false);
      _submitting = false;
      return;
    }

    _submitting = false;
    // Navegación fuera del try: si context.go() falla, no se muestra error de credenciales
    if (mounted) context.go(role == 'vet' ? '/vet/dashboard' : '/dashboard');
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Iniciar sesión')),
      bottomNavigationBar: const AppFooter(),
      body: ResponsiveBody(
        formLayout: true,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SizedBox(height: 40),
                // Logo
                Center(
                  child: Image.asset(
                    'assets/images/Logo.png',
                    height: 180,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'NutriVet.IA',
                  style: theme.textTheme.headlineMedium?.copyWith(
                    color: theme.colorScheme.primary,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 4),
                Text(
                  'Nutrición personalizada para tu mascota',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 36),

                // Email
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

                // Contraseña con ojo
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
                  validator: (v) =>
                      (v == null || v.length < 6) ? 'Mínimo 6 caracteres' : null,
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
                  key: const ValueKey('login_button'),
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
                      : const Text('Iniciar sesión'),
                ),
                const SizedBox(height: 8),
                Center(
                  child: TextButton(
                    onPressed: () => context.push('/forgot-password'),
                    child: const Text('¿Olvidaste tu contraseña?'),
                  ),
                ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: () => context.push('/register'),
                  child: const Text('¿No tienes cuenta? Regístrate'),
                ),

              ],
            ),
          ),
        ),
      ),
    );
  }
}
