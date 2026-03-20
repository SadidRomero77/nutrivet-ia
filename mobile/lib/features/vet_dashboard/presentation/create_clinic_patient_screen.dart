/// Pantalla para crear un paciente clínico (ClinicPet) desde el flujo del vet.
///
/// El vet ingresa los 13 campos del animal + datos de contacto del propietario.
/// Al finalizar se genera un claim code que el propietario puede usar para
/// vincular el paciente a su cuenta en la app.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/api/api_client.dart';
import '../../../core/widgets/app_footer.dart';

class CreateClinicPatientScreen extends ConsumerStatefulWidget {
  const CreateClinicPatientScreen({super.key});

  @override
  ConsumerState<CreateClinicPatientScreen> createState() =>
      _CreateClinicPatientScreenState();
}

class _CreateClinicPatientScreenState
    extends ConsumerState<CreateClinicPatientScreen> {
  final _formKey = GlobalKey<FormState>();

  // Datos del animal
  final _nameCtrl = TextEditingController();
  final _breedCtrl = TextEditingController();
  final _ageCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  String _species = 'perro';
  String _sex = 'macho';
  String? _size;
  String _reproductiveStatus = 'esterilizado';
  String? _activityLevel;
  int _bcs = 5;
  String _currentDiet = 'concentrado';
  final List<String> _medicalConditions = [];

  // Datos del propietario
  final _ownerNameCtrl = TextEditingController();
  final _ownerPhoneCtrl = TextEditingController();

  bool _loading = false;
  String? _claimCode;

  static const _activityDog = ['sedentario', 'moderado', 'activo', 'muy_activo'];
  static const _activityCat = ['indoor', 'indoor_outdoor', 'outdoor'];
  static const _conditions = [
    'diabético', 'hipotiroideo', 'cancerígeno', 'articular', 'renal',
    'hepático/hiperlipidemia', 'pancreático', 'neurodegenerativo',
    'bucal/periodontal', 'piel/dermatitis', 'gastritis',
    'cistitis/enfermedad_urinaria', 'sobrepeso/obesidad',
  ];

  @override
  void dispose() {
    _nameCtrl.dispose();
    _breedCtrl.dispose();
    _ageCtrl.dispose();
    _weightCtrl.dispose();
    _ownerNameCtrl.dispose();
    _ownerPhoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_activityLevel == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecciona el nivel de actividad')),
      );
      return;
    }
    setState(() => _loading = true);

    try {
      final dio = ref.read(apiClientProvider);
      final response = await dio.post<Map<String, dynamic>>(
        '/v1/pets/clinic',
        data: {
          'pet_data': {
            'name': _nameCtrl.text.trim(),
            'species': _species,
            'breed': _breedCtrl.text.trim(),
            'sex': _sex,
            'age_months': int.parse(_ageCtrl.text),
            'weight_kg': double.parse(_weightCtrl.text),
            if (_size != null) 'size': _size,
            'reproductive_status': _reproductiveStatus,
            'activity_level': _activityLevel,
            'bcs': _bcs,
            'medical_conditions': _medicalConditions,
            'allergies': <String>[],
            'current_diet': _currentDiet,
          },
          if (_ownerNameCtrl.text.trim().isNotEmpty)
            'owner_name': _ownerNameCtrl.text.trim(),
          if (_ownerPhoneCtrl.text.trim().isNotEmpty)
            'owner_phone': _ownerPhoneCtrl.text.trim(),
        },
      );
      setState(() {
        _claimCode = response.data!['claim_code'] as String;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al crear paciente: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_claimCode != null) return _ClaimCodeSuccess(code: _claimCode!);

    final activityOptions = _species == 'perro' ? _activityDog : _activityCat;

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Nuevo paciente clínico')),
      bottomNavigationBar: const AppFooter(),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _SectionHeader(title: 'Datos del animal'),

            // Especie
            Row(
              children: [
                Expanded(
                  child: _SpeciesCard(
                    label: 'Perro',
                    emoji: '🐕',
                    selected: _species == 'perro',
                    onTap: () => setState(() {
                      _species = 'perro';
                      _activityLevel = null;
                      _size = null;
                    }),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _SpeciesCard(
                    label: 'Gato',
                    emoji: '🐈',
                    selected: _species == 'gato',
                    onTap: () => setState(() {
                      _species = 'gato';
                      _activityLevel = null;
                      _size = null;
                    }),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            TextFormField(
              controller: _nameCtrl,
              decoration: const InputDecoration(labelText: 'Nombre del animal *'),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Campo requerido' : null,
            ),
            const SizedBox(height: 12),

            TextFormField(
              controller: _breedCtrl,
              decoration: const InputDecoration(labelText: 'Raza *'),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Campo requerido' : null,
            ),
            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _ageCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Edad (meses) *',
                      suffixText: 'meses',
                    ),
                    validator: (v) =>
                        (int.tryParse(v ?? '') == null) ? 'Edad inválida' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _weightCtrl,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Peso (kg) *',
                      suffixText: 'kg',
                    ),
                    validator: (v) {
                      final n = double.tryParse(v ?? '');
                      return (n == null || n <= 0) ? 'Peso inválido' : null;
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Sexo
            DropdownButtonFormField<String>(
              value: _sex,
              decoration: const InputDecoration(labelText: 'Sexo *'),
              items: const [
                DropdownMenuItem(value: 'macho', child: Text('Macho')),
                DropdownMenuItem(value: 'hembra', child: Text('Hembra')),
              ],
              onChanged: (v) => setState(() => _sex = v!),
            ),
            const SizedBox(height: 12),

            // Talla (solo perros)
            if (_species == 'perro') ...[
              DropdownButtonFormField<String>(
                value: _size,
                decoration: const InputDecoration(labelText: 'Talla'),
                items: const [
                  DropdownMenuItem(value: 'mini', child: Text('Mini (1-4 kg)')),
                  DropdownMenuItem(value: 'pequeño', child: Text('Pequeño (4-9 kg)')),
                  DropdownMenuItem(value: 'mediano', child: Text('Mediano (9-14 kg)')),
                  DropdownMenuItem(value: 'grande', child: Text('Grande (14-30 kg)')),
                  DropdownMenuItem(value: 'gigante', child: Text('Gigante (+30 kg)')),
                ],
                onChanged: (v) => setState(() => _size = v),
              ),
              const SizedBox(height: 12),
            ],

            // Estado reproductivo
            DropdownButtonFormField<String>(
              value: _reproductiveStatus,
              decoration:
                  const InputDecoration(labelText: 'Estado reproductivo *'),
              items: const [
                DropdownMenuItem(
                    value: 'esterilizado', child: Text('Esterilizado/a')),
                DropdownMenuItem(
                    value: 'no esterilizado',
                    child: Text('No esterilizado/a')),
              ],
              onChanged: (v) => setState(() => _reproductiveStatus = v!),
            ),
            const SizedBox(height: 12),

            // Nivel de actividad
            DropdownButtonFormField<String>(
              value: _activityLevel,
              decoration:
                  const InputDecoration(labelText: 'Nivel de actividad *'),
              items: activityOptions
                  .map((l) => DropdownMenuItem(value: l, child: Text(l)))
                  .toList(),
              onChanged: (v) => setState(() => _activityLevel = v),
            ),
            const SizedBox(height: 16),

            // BCS
            Text(
              'BCS — Body Condition Score: $_bcs / 9',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            Slider(
              value: _bcs.toDouble(),
              min: 1,
              max: 9,
              divisions: 8,
              label: _bcs.toString(),
              onChanged: (v) => setState(() => _bcs = v.round()),
            ),
            const SizedBox(height: 12),

            // Dieta actual
            DropdownButtonFormField<String>(
              value: _currentDiet,
              decoration:
                  const InputDecoration(labelText: 'Alimentación actual *'),
              items: const [
                DropdownMenuItem(
                    value: 'concentrado', child: Text('Concentrado')),
                DropdownMenuItem(value: 'natural', child: Text('Natural/BARF')),
                DropdownMenuItem(value: 'mixto', child: Text('Mixto')),
              ],
              onChanged: (v) => setState(() => _currentDiet = v!),
            ),
            const SizedBox(height: 16),

            // Condiciones médicas
            Text(
              'Condiciones médicas',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: _conditions
                  .map(
                    (c) => FilterChip(
                      label: Text(c, style: const TextStyle(fontSize: 12)),
                      selected: _medicalConditions.contains(c),
                      onSelected: (sel) => setState(() {
                        if (sel) {
                          _medicalConditions.add(c);
                        } else {
                          _medicalConditions.remove(c); // ignore: avoid_dynamic_calls
                        }
                      }),
                    ),
                  )
                  .toList(),
            ),
            const SizedBox(height: 24),

            _SectionHeader(title: 'Datos del propietario (opcional)'),
            TextFormField(
              controller: _ownerNameCtrl,
              decoration:
                  const InputDecoration(labelText: 'Nombre del propietario'),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _ownerPhoneCtrl,
              keyboardType: TextInputType.phone,
              decoration:
                  const InputDecoration(labelText: 'Teléfono del propietario'),
            ),
            const SizedBox(height: 32),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _loading ? null : _submit,
                icon: _loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.add),
                label: const Text('Crear paciente clínico'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Pantalla de éxito que muestra el claim code al vet.
class _ClaimCodeSuccess extends StatelessWidget {
  const _ClaimCodeSuccess({required this.code});

  final String code;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Paciente creado')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 64),
              const SizedBox(height: 16),
              Text(
                'Paciente creado correctamente',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              Text(
                'Código de vinculación para el propietario:',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 16),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  code,
                  style: theme.textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    letterSpacing: 6,
                    color: theme.colorScheme.primary,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'El propietario puede usar este código en la app\n'
                '"Reclamar mascota" para vincular el paciente a su cuenta.',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => context.go('/vet/dashboard'),
                child: const Text('Volver al dashboard'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Theme.of(context).colorScheme.primary,
            ),
      ),
    );
  }
}

class _SpeciesCard extends StatelessWidget {
  const _SpeciesCard({
    required this.label,
    required this.emoji,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String emoji;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          border: Border.all(
            color: selected
                ? theme.colorScheme.primary
                : theme.colorScheme.outlineVariant,
            width: selected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
          color: selected
              ? theme.colorScheme.primaryContainer.withOpacity(0.3)
              : null,
        ),
        child: Column(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 28)),
            const SizedBox(height: 4),
            Text(label,
                style: TextStyle(
                  fontWeight:
                      selected ? FontWeight.bold : FontWeight.normal,
                  color: selected
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurface,
                )),
          ],
        ),
      ),
    );
  }
}
