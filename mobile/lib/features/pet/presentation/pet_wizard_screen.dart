/// Wizard de registro de mascota — 6 pasos, 13 campos obligatorios.
///
/// Estado guardado localmente en memoria durante el wizard.
/// Solo envía al backend cuando todos los 13 campos están completos.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/pet_repository.dart';
import 'dashboard_screen.dart';

// Opciones de dominio
const _medicalConditions = [
  'Ninguno conocido',
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
];

const _activityLevelsDog = ['sedentario', 'moderado', 'activo', 'muy_activo'];
const _activityLevelsCat = ['indoor', 'indoor_outdoor', 'outdoor'];
const _sizesOptions = [
  'mini',
  'pequeño',
  'mediano',
  'grande',
  'gigante',
];

/// Proveedor del estado del wizard.
final _wizardStateProvider =
    StateProvider.autoDispose<Map<String, dynamic>>((ref) => {});

class PetWizardScreen extends ConsumerStatefulWidget {
  const PetWizardScreen({super.key});

  @override
  ConsumerState<PetWizardScreen> createState() => _PetWizardScreenState();
}

class _PetWizardScreenState extends ConsumerState<PetWizardScreen> {
  final _pageCtrl = PageController();
  int _currentPage = 0;
  bool _loading = false;

  void _next() {
    if (_currentPage < 5) {
      _pageCtrl.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
      setState(() => _currentPage++);
    } else {
      _submit();
    }
  }

  void _back() {
    if (_currentPage > 0) {
      _pageCtrl.previousPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
      setState(() => _currentPage--);
    }
  }

  Future<void> _submit() async {
    final data = ref.read(_wizardStateProvider);
    setState(() => _loading = true);
    try {
      await ref.read(petRepositoryProvider).createPet(data);
      ref.invalidate(petsProvider);
      if (mounted) context.go('/dashboard');
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
    final wizardData = ref.watch(_wizardStateProvider);

    return Scaffold(
      appBar: AppBar(
        title: NutrivetTitle('Paso ${_currentPage + 1} de 6'),
        leading: _currentPage > 0
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: _back,
              )
            : null,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(
            value: (_currentPage + 1) / 6,
          ),
        ),
      ),
      bottomNavigationBar: const AppFooter(),
      body: PageView(
        controller: _pageCtrl,
        physics: const NeverScrollableScrollPhysics(),
        children: [
          _Step1BasicInfo(data: wizardData, onNext: _next),
          _Step2Physical(data: wizardData, onNext: _next),
          _Step3Health(data: wizardData, onNext: _next),
          _Step4Activity(data: wizardData, onNext: _next),
          _Step5Medical(data: wizardData, onNext: _next),
          _Step6Feeding(
            data: wizardData,
            onNext: _next,
            loading: _loading,
          ),
        ],
      ),
    );
  }
}

// ─── Step 1: Nombre, especie, raza, sexo ────────────────────────────────────

class _Step1BasicInfo extends ConsumerStatefulWidget {
  const _Step1BasicInfo({required this.data, required this.onNext});

  final Map<String, dynamic> data;
  final VoidCallback onNext;

  @override
  ConsumerState<_Step1BasicInfo> createState() => _Step1BasicInfoState();
}

class _Step1BasicInfoState extends ConsumerState<_Step1BasicInfo> {
  final _formKey = GlobalKey<FormState>();
  final _nameCtrl = TextEditingController();
  final _breedCtrl = TextEditingController();
  String _species = 'perro';
  String _sex = 'macho';

  @override
  void initState() {
    super.initState();
    _nameCtrl.text = widget.data['name'] as String? ?? '';
    _breedCtrl.text = widget.data['breed'] as String? ?? '';
    _species = widget.data['species'] as String? ?? 'perro';
    _sex = widget.data['sex'] as String? ?? 'macho';
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _breedCtrl.dispose();
    super.dispose();
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    ref.read(_wizardStateProvider.notifier).update((s) => {
          ...s,
          'name': _nameCtrl.text.trim(),
          'species': _species,
          'breed': _breedCtrl.text.trim(),
          'sex': _sex,
        });
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            TextFormField(
              key: const ValueKey('pet_name_field'),
              controller: _nameCtrl,
              decoration: const InputDecoration(labelText: 'Nombre de la mascota'),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Requerido' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              key: const ValueKey('species_dropdown'),
              value: _species,
              decoration: const InputDecoration(labelText: 'Especie'),
              items: const [
                DropdownMenuItem(value: 'perro', child: Text('🐕 Perro')),
                DropdownMenuItem(value: 'gato', child: Text('🐈 Gato')),
              ],
              onChanged: (v) => setState(() => _species = v!),
            ),
            const SizedBox(height: 16),
            TextFormField(
              key: const ValueKey('breed_field'),
              controller: _breedCtrl,
              decoration: const InputDecoration(labelText: 'Raza'),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Requerido' : null,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              key: const ValueKey('sex_dropdown'),
              value: _sex,
              decoration: const InputDecoration(labelText: 'Sexo'),
              items: const [
                DropdownMenuItem(value: 'macho', child: Text('Macho')),
                DropdownMenuItem(value: 'hembra', child: Text('Hembra')),
              ],
              onChanged: (v) => setState(() => _sex = v!),
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                key: const ValueKey('next_button'),
                onPressed: _save,
                child: const Text('Siguiente'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Step 2: Edad, peso, talla (solo perros) ────────────────────────────────

class _Step2Physical extends ConsumerStatefulWidget {
  const _Step2Physical({required this.data, required this.onNext});

  final Map<String, dynamic> data;
  final VoidCallback onNext;

  @override
  ConsumerState<_Step2Physical> createState() => _Step2PhysicalState();
}

class _Step2PhysicalState extends ConsumerState<_Step2Physical> {
  final _formKey = GlobalKey<FormState>();
  final _ageCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  String? _size;

  @override
  void initState() {
    super.initState();
    _ageCtrl.text = widget.data['age_months']?.toString() ?? '';
    _weightCtrl.text = widget.data['weight_kg']?.toString() ?? '';
    _size = widget.data['size'] as String?;
  }

  @override
  void dispose() {
    _ageCtrl.dispose();
    _weightCtrl.dispose();
    super.dispose();
  }

  void _save() {
    if (!_formKey.currentState!.validate()) return;
    final isPerro = widget.data['species'] == 'perro';
    ref.read(_wizardStateProvider.notifier).update((s) => {
          ...s,
          'age_months': int.parse(_ageCtrl.text),
          'weight_kg': double.parse(_weightCtrl.text),
          if (isPerro) 'size': _size,
        });
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    final isPerro = widget.data['species'] == 'perro';

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            TextFormField(
              key: const ValueKey('age_field'),
              controller: _ageCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Edad (meses)'),
              validator: (v) {
                final n = int.tryParse(v ?? '');
                if (n == null || n <= 0) return 'Edad inválida';
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              key: const ValueKey('weight_field'),
              controller: _weightCtrl,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Peso (kg)'),
              validator: (v) {
                final n = double.tryParse(v ?? '');
                if (n == null || n <= 0) return 'Peso inválido';
                return null;
              },
            ),
            if (isPerro) ...[
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                key: const ValueKey('size_dropdown'),
                value: _size,
                decoration: const InputDecoration(labelText: 'Talla'),
                items: _sizesOptions
                    .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                    .toList(),
                onChanged: (v) => setState(() => _size = v),
                validator: (v) => v == null ? 'Selecciona talla' : null,
              ),
            ],
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(onPressed: _save, child: const Text('Siguiente')),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Step 3: Estado reproductivo, BCS ───────────────────────────────────────

class _Step3Health extends ConsumerStatefulWidget {
  const _Step3Health({required this.data, required this.onNext});

  final Map<String, dynamic> data;
  final VoidCallback onNext;

  @override
  ConsumerState<_Step3Health> createState() => _Step3HealthState();
}

class _Step3HealthState extends ConsumerState<_Step3Health> {
  String _reproductiveStatus = 'esterilizado';
  int _bcs = 5;

  @override
  void initState() {
    super.initState();
    _reproductiveStatus =
        widget.data['reproductive_status'] as String? ?? 'esterilizado';
    _bcs = widget.data['bcs'] as int? ?? 5;
  }

  void _save() {
    ref.read(_wizardStateProvider.notifier).update((s) => {
          ...s,
          'reproductive_status': _reproductiveStatus,
          'bcs': _bcs,
        });
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          DropdownButtonFormField<String>(
            value: _reproductiveStatus,
            decoration: const InputDecoration(labelText: 'Estado reproductivo'),
            items: const [
              DropdownMenuItem(
                value: 'esterilizado',
                child: Text('Esterilizado/a'),
              ),
              DropdownMenuItem(
                value: 'no_esterilizado',
                child: Text('No esterilizado/a'),
              ),
            ],
            onChanged: (v) => setState(() => _reproductiveStatus = v!),
          ),
          const SizedBox(height: 24),
          Text(
            'BCS — Body Condition Score: $_bcs / 9',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          Slider(
            value: _bcs.toDouble(),
            min: 1,
            max: 9,
            divisions: 8,
            label: _bcs.toString(),
            onChanged: (v) => setState(() => _bcs = v.round()),
          ),
          Text(
            _bcs <= 3
                ? 'Bajo peso — se usará fase de aumento'
                : _bcs >= 7
                    ? 'Sobrepeso — se usará fase de reducción'
                    : 'Peso ideal — se usará fase de mantenimiento',
            style: TextStyle(
              color: _bcs <= 3
                  ? Colors.orange
                  : _bcs >= 7
                      ? Colors.red
                      : Colors.green,
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(onPressed: _save, child: const Text('Siguiente')),
          ),
        ],
      ),
    );
  }
}

// ─── Step 4: Nivel de actividad ─────────────────────────────────────────────

class _Step4Activity extends ConsumerStatefulWidget {
  const _Step4Activity({required this.data, required this.onNext});

  final Map<String, dynamic> data;
  final VoidCallback onNext;

  @override
  ConsumerState<_Step4Activity> createState() => _Step4ActivityState();
}

class _Step4ActivityState extends ConsumerState<_Step4Activity> {
  String? _activityLevel;

  @override
  void initState() {
    super.initState();
    _activityLevel = widget.data['activity_level'] as String?;
  }

  void _save() {
    if (_activityLevel == null) return;
    ref.read(_wizardStateProvider.notifier).update((s) => {
          ...s,
          'activity_level': _activityLevel,
        });
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    final isPerro = widget.data['species'] == 'perro';
    final options = isPerro ? _activityLevelsDog : _activityLevelsCat;

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Nivel de actividad',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 16),
          ...options.map(
            (level) => RadioListTile<String>(
              title: Text(level),
              value: level,
              groupValue: _activityLevel,
              onChanged: (v) => setState(() => _activityLevel = v),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _activityLevel != null ? _save : null,
              child: const Text('Siguiente'),
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Step 5: Condiciones médicas + alergias ──────────────────────────────────

class _Step5Medical extends ConsumerStatefulWidget {
  const _Step5Medical({required this.data, required this.onNext});

  final Map<String, dynamic> data;
  final VoidCallback onNext;

  @override
  ConsumerState<_Step5Medical> createState() => _Step5MedicalState();
}

class _Step5MedicalState extends ConsumerState<_Step5Medical> {
  final Set<String> _selectedConditions = {};
  final _allergiesCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    final existing = widget.data['medical_conditions'] as List<String>?;
    if (existing != null) _selectedConditions.addAll(existing);
    _allergiesCtrl.text =
        (widget.data['allergies'] as List<String>?)?.join(', ') ?? '';
  }

  @override
  void dispose() {
    _allergiesCtrl.dispose();
    super.dispose();
  }

  void _save() {
    final allergies = _allergiesCtrl.text
        .split(',')
        .map((s) => s.trim())
        .where((s) => s.isNotEmpty)
        .toList();
    // Filtrar 'Ninguno conocido' — el backend espera lista vacía cuando no hay condiciones
    final conditions = _selectedConditions
        .where((c) => c != 'Ninguno conocido')
        .toList();
    ref.read(_wizardStateProvider.notifier).update((s) => {
          ...s,
          'medical_conditions': conditions,
          'allergies': allergies,
        });
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Antecedentes médicos',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          ..._medicalConditions
              .map(
                (cond) => CheckboxListTile(
                  key: ValueKey('cond_$cond'),
                  title: Text(cond),
                  value: _selectedConditions.contains(cond),
                  onChanged: (v) => setState(() {
                    if (v == true) {
                      if (cond == 'Ninguno conocido') {
                        _selectedConditions
                          ..clear()
                          ..add(cond);
                      } else {
                        _selectedConditions
                          ..remove('Ninguno conocido')
                          ..add(cond);
                      }
                    } else {
                      _selectedConditions.remove(cond);
                    }
                  }),
                ),
              )
              .toList(),
          const SizedBox(height: 8),
          TextFormField(
            controller: _allergiesCtrl,
            decoration: const InputDecoration(
              labelText: 'Alergias / intolerancias (separadas por coma)',
              hintText: 'pollo, trigo, ...',
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(onPressed: _save, child: const Text('Siguiente')),
          ),
        ],
      ),
    );
  }
}

// ─── Step 6: Alimentación actual ─────────────────────────────────────────────

class _Step6Feeding extends ConsumerStatefulWidget {
  const _Step6Feeding({
    required this.data,
    required this.onNext,
    required this.loading,
  });

  final Map<String, dynamic> data;
  final VoidCallback onNext;
  final bool loading;

  @override
  ConsumerState<_Step6Feeding> createState() => _Step6FeedingState();
}

class _Step6FeedingState extends ConsumerState<_Step6Feeding> {
  String? _feedingType;

  @override
  void initState() {
    super.initState();
    _feedingType = widget.data['current_feeding_type'] as String?;
  }

  void _save() {
    if (_feedingType == null) return;
    ref.read(_wizardStateProvider.notifier).update((s) => {
          ...s,
          'current_diet': _feedingType,
        });
    widget.onNext();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '¿Qué come tu mascota HOY?',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 16),
          for (final option in ['concentrado', 'natural', 'mixto'])
            RadioListTile<String>(
              key: ValueKey('feeding_$option'),
              title: Text(option),
              value: option,
              groupValue: _feedingType,
              onChanged: (v) => setState(() => _feedingType = v),
            ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: (_feedingType != null && !widget.loading) ? _save : null,
              child: widget.loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text('Crear perfil'),
            ),
          ),
        ],
      ),
    );
  }
}
