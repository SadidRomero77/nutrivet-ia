/// Pantalla de edición de perfil — nombre, teléfono y datos clínicos (vet).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../data/auth_repository.dart';

part 'edit_profile_screen.g.dart';

@riverpod
Future<UserProfile> _editProfile(Ref ref) =>
    ref.read(authRepositoryProvider).getMe();

class EditProfileScreen extends ConsumerStatefulWidget {
  const EditProfileScreen({super.key});

  @override
  ConsumerState<EditProfileScreen> createState() => _EditProfileScreenState();
}

class _EditProfileScreenState extends ConsumerState<EditProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _clinicCtrl = TextEditingController();
  final _specialCtrl = TextEditingController();
  final _licenseCtrl = TextEditingController();

  bool _loading = false;
  bool _initialized = false;
  String? _role;

  @override
  void dispose() {
    _nameCtrl.dispose();
    _phoneCtrl.dispose();
    _clinicCtrl.dispose();
    _specialCtrl.dispose();
    _licenseCtrl.dispose();
    super.dispose();
  }

  void _initControllers(UserProfile profile) {
    if (_initialized) return;
    _initialized = true;
    _role = profile.role;
    _nameCtrl.text = profile.fullName ?? '';
    _phoneCtrl.text = profile.phone ?? '';
    _clinicCtrl.text = profile.clinicName ?? '';
    _specialCtrl.text = profile.specialization ?? '';
    _licenseCtrl.text = profile.licenseNumber ?? '';
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ref.read(authRepositoryProvider).updateProfile(
            fullName: _nameCtrl.text.trim().isEmpty ? null : _nameCtrl.text.trim(),
            phone: _phoneCtrl.text.trim().isEmpty ? null : _phoneCtrl.text.trim(),
            clinicName: _clinicCtrl.text.trim().isEmpty ? null : _clinicCtrl.text.trim(),
            specialization: _specialCtrl.text.trim().isEmpty ? null : _specialCtrl.text.trim(),
            licenseNumber: _licenseCtrl.text.trim().isEmpty ? null : _licenseCtrl.text.trim(),
          );
      ref.invalidate(_editProfileProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Perfil actualizado correctamente')),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al guardar: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final profileAsync = ref.watch(_editProfileProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Editar perfil'),
        actions: [
          if (_loading)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Center(
                child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ),
            )
          else
            TextButton(
              onPressed: _save,
              child: const Text('Guardar'),
            ),
        ],
      ),
      body: profileAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (profile) {
          _initControllers(profile);
          return SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // -- Información básica --
                  Text('Información básica',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _nameCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Nombre completo',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _phoneCtrl,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                      labelText: 'Teléfono',
                      prefixIcon: Icon(Icons.phone_outlined),
                      hintText: '+57 300 000 0000',
                    ),
                  ),

                  // -- Datos clínicos (solo vet) --
                  if (_role == 'vet') ...[
                    const SizedBox(height: 28),
                    Text('Datos clínicos',
                        style: theme.textTheme.titleSmall
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _clinicCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Nombre de la clínica',
                        prefixIcon: Icon(Icons.local_hospital_outlined),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _specialCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Especialización',
                        prefixIcon: Icon(Icons.school_outlined),
                        hintText: 'Ej: Nutrición clínica veterinaria',
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _licenseCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Cédula profesional / Tarjeta profesional',
                        prefixIcon: Icon(Icons.badge_outlined),
                      ),
                    ),
                  ],

                  // -- Email (solo lectura) --
                  const SizedBox(height: 28),
                  Text('Email registrado',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  TextFormField(
                    initialValue: profile.email,
                    readOnly: true,
                    enabled: false,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.email_outlined),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'El email no se puede cambiar.',
                    style: TextStyle(
                        fontSize: 12, color: theme.colorScheme.outline),
                  ),
                  const SizedBox(height: 32),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _loading ? null : _save,
                      child: const Text('Guardar cambios'),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
