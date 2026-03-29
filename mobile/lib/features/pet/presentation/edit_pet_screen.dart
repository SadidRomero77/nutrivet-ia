/// Pantalla de edición de mascota.
///
/// Permite editar todos los campos que cambian con el tiempo:
/// edad, peso, BCS, nivel de actividad, dieta, condiciones médicas y alergias.
///
/// Regla: si se agregan condiciones médicas a un plan ACTIVE,
/// el plan vuelve a PENDING_VET (la lógica corre en el backend).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/pet_repository.dart';
import 'dashboard_screen.dart';

// ── Opciones de dominio ────────────────────────────────────────────────────────

const _medicalConditions = [
  'diabético',
  'hipotiroideo',
  'cancerígeno',
  'articular',
  'renal',
  'hepático/hiperlipidemia',
  'pancreático',
  'neurodegenerativo',
  'bucal/periodontal',
  'piel/dermatitis',
  'gastritis',
  'cistitis/enfermedad_urinaria',
  'sobrepeso/obesidad',
  'insuficiencia_cardiaca',
  'hiperadrenocorticismo_cushing',
  'epilepsia',
  'megaesofago',
];

const _allergens = [
  'Pollo',
  'Res/Vaca',
  'Cordero',
  'Pescado/Salmón',
  'Huevo',
  'Leche/Lácteos',
  'Trigo/Gluten',
  'Soya',
  'Maíz',
];

const _activityLevelsDog = ['sedentario', 'moderado', 'activo', 'muy_activo'];
const _activityLevelsCat = ['indoor', 'indoor_outdoor', 'outdoor'];
const _dietOptions = ['concentrado', 'natural', 'mixto'];

class EditPetScreen extends ConsumerStatefulWidget {
  const EditPetScreen({super.key, required this.petId});

  final String petId;

  @override
  ConsumerState<EditPetScreen> createState() => _EditPetScreenState();
}

class _EditPetScreenState extends ConsumerState<EditPetScreen> {
  final _formKey = GlobalKey<FormState>();
  final _weightCtrl = TextEditingController();

  // Edad
  int _ageYears = 0;
  int _ageMonthsExtra = 1;

  int _bcs = 5;
  String? _activityLevel;
  String? _currentDiet;
  String? _species;
  final Set<String> _selectedConditions = {};
  final Set<String> _selectedAllergens = {};

  bool _loading = false;
  bool _initialized = false;

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

        // Descomponer ageMonths en años + meses
        _ageYears = pet.ageMonths ~/ 12;
        _ageMonthsExtra = pet.ageMonths % 12;

        // Condiciones médicas actuales
        _selectedConditions
          ..clear()
          ..addAll(pet.medicalConditions);

        // Alergias actuales
        _selectedAllergens
          ..clear()
          ..addAll(pet.allergies);

        _initialized = true;
      });
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _loading = true);

    final totalMonths = _ageYears * 12 + _ageMonthsExtra;
    if (totalMonths <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('La edad debe ser mayor a 0 meses')),
      );
      setState(() => _loading = false);
      return;
    }

    try {
      await ref.read(petRepositoryProvider).updatePet(
        widget.petId,
        {
          'weight_kg': double.parse(_weightCtrl.text),
          'age_months': totalMonths,
          'bcs': _bcs,
          if (_activityLevel != null) 'activity_level': _activityLevel,
          if (_currentDiet != null) 'current_diet': _currentDiet,
          'medical_conditions': _selectedConditions.toList(),
          'allergies': _selectedAllergens.toList(),
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

  String _bcsDescription(int bcs) {
    if (bcs <= 2) return 'Muy delgado — pérdida de masa muscular visible';
    if (bcs == 3) return 'Bajo peso — costillas muy palpables';
    if (bcs == 4) return 'Levemente delgado — costillas fácilmente palpables';
    if (bcs == 5) return 'Peso ideal — cintura visible, costillas palpables sin exceso';
    if (bcs == 6) return 'Levemente sobrepeso — costillas palpables con ligera capa';
    if (bcs == 7) return 'Sobrepeso — costillas difíciles de palpar';
    if (bcs == 8) return 'Obeso — sin cintura definida, grasa visible';
    return 'Obesidad severa — depósitos grasos evidentes';
  }

  Color _bcsColor(int bcs) {
    if (bcs <= 3) return Colors.blue;
    if (bcs <= 6) return Colors.green;
    return Colors.orange;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Editar mascota')),
      bottomNavigationBar: const AppFooter(),
      body: FutureBuilder<void>(
        future: _initFromPet(),
        builder: (context, snapshot) {
          if (!_initialized) {
            return const Center(child: CircularProgressIndicator());
          }
          final activityOptions =
              _species == 'perro' ? _activityLevelsDog : _activityLevelsCat;
          final totalMonths = _ageYears * 12 + _ageMonthsExtra;

          return Center(
            child: ConstrainedBox(
              constraints:
                  const BoxConstraints(maxWidth: Breakpoints.maxFormWidth),
              child: Form(
                key: _formKey,
                child: ListView(
                  padding: const EdgeInsets.all(24),
                  children: [
                    // ── Edad ─────────────────────────────────────────────────
                    Text(
                      'Edad',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<int>(
                            value: _ageYears,
                            decoration:
                                const InputDecoration(labelText: 'Años'),
                            isExpanded: true,
                            items: List.generate(
                              21,
                              (i) => DropdownMenuItem(
                                value: i,
                                child: Text(
                                  i == 0
                                      ? '< 1 año'
                                      : '$i año${i > 1 ? "s" : ""}',
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ),
                            onChanged: (v) {
                              if (v != null) setState(() => _ageYears = v);
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: DropdownButtonFormField<int>(
                            value: _ageMonthsExtra,
                            decoration:
                                const InputDecoration(labelText: 'Meses +'),
                            isExpanded: true,
                            items: List.generate(
                              12,
                              (i) => DropdownMenuItem(
                                value: i,
                                child:
                                    Text('$i mes${i != 1 ? "es" : ""}'),
                              ),
                            ),
                            onChanged: (v) {
                              if (v != null)
                                setState(() => _ageMonthsExtra = v);
                            },
                          ),
                        ),
                      ],
                    ),
                    if (totalMonths > 0)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                          'Total: $totalMonths ${totalMonths == 1 ? "mes" : "meses"}',
                          style: TextStyle(
                              fontSize: 12,
                              color: theme.colorScheme.outline),
                        ),
                      ),
                    const SizedBox(height: 20),

                    // ── Peso ─────────────────────────────────────────────────
                    TextFormField(
                      key: const ValueKey('edit_weight_field'),
                      controller: _weightCtrl,
                      keyboardType: const TextInputType.numberWithOptions(
                          decimal: true),
                      decoration: const InputDecoration(
                        labelText: 'Peso (kg)',
                        suffixText: 'kg',
                        prefixIcon: Icon(Icons.monitor_weight_outlined),
                      ),
                      validator: (v) {
                        final n = double.tryParse(v ?? '');
                        if (n == null || n <= 0) return 'Peso inválido';
                        return null;
                      },
                    ),
                    const SizedBox(height: 20),

                    // ── BCS ──────────────────────────────────────────────────
                    Text(
                      'Condición corporal (BCS) — $_bcs / 9',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _bcsDescription(_bcs),
                      style: TextStyle(
                        fontSize: 12,
                        color: _bcsColor(_bcs),
                        fontWeight: FontWeight.w500,
                      ),
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
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('1 · Muy delgado',
                            style: theme.textTheme.labelSmall),
                        Text('5 · Ideal',
                            style: theme.textTheme.labelSmall),
                        Text('9 · Obeso',
                            style: theme.textTheme.labelSmall),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // ── Nivel de actividad ────────────────────────────────────
                    DropdownButtonFormField<String>(
                      key: const ValueKey('edit_activity_dropdown'),
                      value: _activityLevel,
                      decoration: const InputDecoration(
                        labelText: 'Nivel de actividad',
                        prefixIcon: Icon(Icons.directions_run),
                      ),
                      items: activityOptions
                          .map((l) => DropdownMenuItem(
                              value: l,
                              child:
                                  Text(l.replaceAll('_', ' '))))
                          .toList(),
                      onChanged: (v) => setState(() => _activityLevel = v),
                    ),
                    const SizedBox(height: 20),

                    // ── Alimentación actual ───────────────────────────────────
                    DropdownButtonFormField<String>(
                      key: const ValueKey('edit_diet_dropdown'),
                      value: _currentDiet,
                      decoration: const InputDecoration(
                        labelText: 'Alimentación actual',
                        prefixIcon: Icon(Icons.restaurant_outlined),
                      ),
                      items: _dietOptions
                          .map((d) =>
                              DropdownMenuItem(value: d, child: Text(d)))
                          .toList(),
                      onChanged: (v) => setState(() => _currentDiet = v),
                    ),
                    const SizedBox(height: 28),

                    // ── Condiciones médicas ───────────────────────────────────
                    Text(
                      'Condiciones médicas',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Selecciona todas las que apliquen. Si agregas una '
                      'condición y hay un plan activo, pasará a revisión veterinaria.',
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.outline),
                    ),
                    const SizedBox(height: 10),
                    // "Ninguno" toggle
                    InkWell(
                      onTap: () => setState(() {
                        if (_selectedConditions.isEmpty) {
                          // ya vacío, no hacer nada
                        } else {
                          _selectedConditions.clear();
                        }
                      }),
                      borderRadius: BorderRadius.circular(8),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                        decoration: BoxDecoration(
                          border: Border.all(
                            color: _selectedConditions.isEmpty
                                ? Colors.green
                                : theme.colorScheme.outlineVariant,
                            width: _selectedConditions.isEmpty ? 2 : 1,
                          ),
                          borderRadius: BorderRadius.circular(8),
                          color: _selectedConditions.isEmpty
                              ? Colors.green.shade50
                              : null,
                        ),
                        child: Row(
                          children: [
                            Icon(
                              _selectedConditions.isEmpty
                                  ? Icons.check_circle
                                  : Icons.radio_button_unchecked,
                              color: _selectedConditions.isEmpty
                                  ? Colors.green
                                  : theme.colorScheme.outline,
                              size: 20,
                            ),
                            const SizedBox(width: 10),
                            Text(
                              'Ninguno conocido',
                              style: TextStyle(
                                fontWeight: _selectedConditions.isEmpty
                                    ? FontWeight.bold
                                    : FontWeight.normal,
                                color: _selectedConditions.isEmpty
                                    ? Colors.green.shade700
                                    : null,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const Divider(height: 20),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _medicalConditions
                          .map((c) => FilterChip(
                                label: Text(
                                  c.replaceAll('_', ' ')
                                      .replaceAll('/', ' / '),
                                  style: const TextStyle(fontSize: 12),
                                ),
                                selected: _selectedConditions.contains(c),
                                onSelected: (v) => setState(() {
                                  if (v) {
                                    _selectedConditions.add(c);
                                  } else {
                                    _selectedConditions.remove(c);
                                  }
                                }),
                                selectedColor:
                                    theme.colorScheme.primaryContainer,
                              ))
                          .toList(),
                    ),
                    const SizedBox(height: 28),

                    // ── Alergias ──────────────────────────────────────────────
                    Text(
                      'Alergias / intolerancias',
                      style: theme.textTheme.titleSmall
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Selecciona todos los ingredientes problemáticos.',
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: theme.colorScheme.outline),
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: _allergens
                          .map((a) => FilterChip(
                                label: Text(a,
                                    style:
                                        const TextStyle(fontSize: 12)),
                                selected: _selectedAllergens.contains(a),
                                onSelected: (v) => setState(() {
                                  if (v) {
                                    _selectedAllergens.add(a);
                                  } else {
                                    _selectedAllergens.remove(a);
                                  }
                                }),
                                selectedColor:
                                    theme.colorScheme.primaryContainer,
                              ))
                          .toList(),
                    ),
                    const SizedBox(height: 32),

                    SizedBox(
                      width: double.infinity,
                      child: FilledButton.icon(
                        key: const ValueKey('save_edit_button'),
                        onPressed: _loading ? null : _save,
                        icon: _loading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.save_outlined),
                        label: const Text('Guardar cambios'),
                        style: FilledButton.styleFrom(
                            minimumSize: const Size.fromHeight(52)),
                      ),
                    ),
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
