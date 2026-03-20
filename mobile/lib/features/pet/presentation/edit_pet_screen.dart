/// Pantalla de edición de mascota.
/// Solo permite editar campos que cambian con el tiempo:
/// peso, BCS, nivel de actividad y tipo de alimentación actual.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/pet_repository.dart';
import 'dashboard_screen.dart';

class EditPetScreen extends ConsumerStatefulWidget {
  const EditPetScreen({super.key, required this.petId});

  final String petId;

  @override
  ConsumerState<EditPetScreen> createState() => _EditPetScreenState();
}

class _EditPetScreenState extends ConsumerState<EditPetScreen> {
  final _formKey = GlobalKey<FormState>();
  final _weightCtrl = TextEditingController();
  int _bcs = 5;
  String? _activityLevel;
  String? _currentDiet;
  String? _species;
  bool _loading = false;
  bool _initialized = false;

  static const _activityLevelsDog = ['sedentario', 'moderado', 'activo', 'muy_activo'];
  static const _activityLevelsCat = ['indoor', 'indoor_outdoor', 'outdoor'];
  static const _dietOptions = ['concentrado', 'natural', 'mixto'];

  @override
  void dispose() {
    _weightCtrl.dispose();
    super.dispose();
  }

  Future<void> _initFromPet() async {
    if (_initialized) return;
    final pets = await ref.read(petRepositoryProvider).listPets();
    final pet = pets.firstWhere((p) => p.petId == widget.petId);
    if (mounted) {
      setState(() {
        _weightCtrl.text = pet.weightKg.toString();
        _bcs = pet.bcs;
        _activityLevel = pet.activityLevel;
        _currentDiet = pet.currentFeedingType;
        _species = pet.species;
        _initialized = true;
      });
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);
    try {
      await ref.read(petRepositoryProvider).updatePet(
        widget.petId,
        {
          'weight_kg': double.parse(_weightCtrl.text),
          'bcs': _bcs,
          if (_activityLevel != null) 'activity_level': _activityLevel,
          if (_currentDiet != null) 'current_diet': _currentDiet,
        },
      );
      ref.invalidate(petsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Perfil actualizado correctamente')),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al actualizar: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Editar mascota')),
      body: FutureBuilder<void>(
        future: _initFromPet(),
        builder: (context, snapshot) {
          if (!_initialized) {
            return const Center(child: CircularProgressIndicator());
          }
          final activityOptions =
              _species == 'perro' ? _activityLevelsDog : _activityLevelsCat;

          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: Breakpoints.maxFormWidth),
              child: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(24),
              children: [
                // Peso
                TextFormField(
                  key: const ValueKey('edit_weight_field'),
                  controller: _weightCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Peso (kg)',
                    suffixText: 'kg',
                  ),
                  validator: (v) {
                    final n = double.tryParse(v ?? '');
                    if (n == null || n <= 0) return 'Peso inválido';
                    return null;
                  },
                ),
                const SizedBox(height: 24),

                // BCS
                Text(
                  'BCS — Body Condition Score: $_bcs / 9',
                  style: Theme.of(context).textTheme.titleSmall,
                ),
                Slider(
                  key: const ValueKey('edit_bcs_slider'),
                  value: _bcs.toDouble(),
                  min: 1,
                  max: 9,
                  divisions: 8,
                  label: _bcs.toString(),
                  onChanged: (v) => setState(() => _bcs = v.round()),
                ),
                Text(
                  _bcs <= 3
                      ? 'Bajo peso — fase de aumento'
                      : _bcs >= 7
                          ? 'Sobrepeso — fase de reducción'
                          : 'Peso ideal — fase de mantenimiento',
                  style: TextStyle(
                    fontSize: 12,
                    color: _bcs <= 3
                        ? Colors.orange
                        : _bcs >= 7
                            ? Colors.red
                            : Colors.green,
                  ),
                ),
                const SizedBox(height: 24),

                // Nivel de actividad
                DropdownButtonFormField<String>(
                  key: const ValueKey('edit_activity_dropdown'),
                  value: _activityLevel,
                  decoration: const InputDecoration(labelText: 'Nivel de actividad'),
                  items: activityOptions
                      .map((l) => DropdownMenuItem(value: l, child: Text(l)))
                      .toList(),
                  onChanged: (v) => setState(() => _activityLevel = v),
                ),
                const SizedBox(height: 16),

                // Dieta actual
                DropdownButtonFormField<String>(
                  key: const ValueKey('edit_diet_dropdown'),
                  value: _currentDiet,
                  decoration: const InputDecoration(labelText: 'Alimentación actual'),
                  items: _dietOptions
                      .map((d) => DropdownMenuItem(value: d, child: Text(d)))
                      .toList(),
                  onChanged: (v) => setState(() => _currentDiet = v),
                ),
                const SizedBox(height: 32),

                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    key: const ValueKey('save_edit_button'),
                    onPressed: _loading ? null : _save,
                    child: _loading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Guardar cambios'),
                  ),
                ),
                const AppFooter(),
              ],
            ),
          ),
            ),
          );
        },
      ),
    );
  }
}
