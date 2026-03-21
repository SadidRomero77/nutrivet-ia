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

// ── Opciones de dominio ────────────────────────────────────────────────────────

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
  'No conozco las alergias',
];

const _activityLevelsDog = ['sedentario', 'moderado', 'activo', 'muy_activo'];
const _activityLevelsCat = ['indoor', 'indoor_outdoor', 'outdoor'];

const _sizeLabels = {
  'mini': 'Mini (1-4 kg)',
  'pequeño': 'Pequeño (4-9 kg)',
  'mediano': 'Mediano (9-14 kg)',
  'grande': 'Grande (14-30 kg)',
  'gigante': 'Gigante (+30 kg)',
};

class CreateClinicPatientScreen extends ConsumerStatefulWidget {
  const CreateClinicPatientScreen({super.key});

  @override
  ConsumerState<CreateClinicPatientScreen> createState() =>
      _CreateClinicPatientScreenState();
}

class _CreateClinicPatientScreenState
    extends ConsumerState<CreateClinicPatientScreen> {
  final _formKey = GlobalKey<FormState>();

  final _nameCtrl = TextEditingController();
  final _breedCtrl = TextEditingController();
  final _ageCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  final _ownerNameCtrl = TextEditingController();
  final _ownerPhoneCtrl = TextEditingController();

  String _species = 'perro';
  String _sex = 'macho';
  String? _size;
  String _reproductiveStatus = 'esterilizado';
  String? _activityLevel;
  int _bcs = 5;
  final Set<String> _selectedConditions = {};
  final Set<String> _selectedAllergens = {};
  String _currentDiet = 'concentrado';
  bool _loading = false;
  String? _claimCode;

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

    final conditions = _selectedConditions
        .where((c) => c != 'Ninguno conocido')
        .toList();
    final allergies = _selectedAllergens
        .where((a) => a != 'No conozco las alergias')
        .toList();

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
            'medical_conditions': conditions,
            'allergies': allergies,
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

  void _onAllergenChanged(String allergen, bool selected) {
    setState(() {
      if (selected) {
        if (allergen == 'No conozco las alergias') {
          _selectedAllergens
            ..clear()
            ..add(allergen);
          _showAllergenAlert();
        } else {
          _selectedAllergens
            ..remove('No conozco las alergias')
            ..add(allergen);
        }
      } else {
        _selectedAllergens.remove(allergen);
      }
    });
  }

  void _showAllergenAlert() {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        icon: const Icon(
          Icons.warning_amber_rounded,
          color: Colors.orange,
          size: 40,
        ),
        title: const Text('Prueba de alergenos recomendada'),
        content: const Text(
          'Sin conocer las alergias del paciente, el plan nutricional '
          'podría incluir ingredientes que causen reacciones adversas.\n\n'
          'Se recomienda realizar una prueba de alergenos antes de iniciar '
          'el plan nutricional.',
        ),
        actions: [
          OutlinedButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(
                  () => _selectedAllergens.remove('No conozco las alergias'));
            },
            child: const Text('Volver'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Continuar bajo mi responsabilidad'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_claimCode != null) return _ClaimCodeSuccess(code: _claimCode!);

    final theme = Theme.of(context);
    final activityOptions =
        _species == 'perro' ? _activityLevelsDog : _activityLevelsCat;

    return Scaffold(
      appBar: AppBar(title: const NutrivetTitle('Nuevo paciente clínico')),
      bottomNavigationBar: const AppFooter(),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // ── Datos básicos ─────────────────────────────────────────────────
            _SectionHeader(title: 'Datos básicos'),

            Row(
              children: [
                Expanded(
                  child: _SpeciesCard(
                    label: 'Canino',
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
                    label: 'Felino',
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
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Nombre del animal *',
                prefixIcon: Icon(Icons.pets_outlined),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Requerido' : null,
            ),
            const SizedBox(height: 12),

            TextFormField(
              controller: _breedCtrl,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Raza *',
                prefixIcon: Icon(Icons.search),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Requerido' : null,
            ),
            const SizedBox(height: 12),

            DropdownButtonFormField<String>(
              value: _sex,
              decoration: const InputDecoration(labelText: 'Sexo *'),
              items: const [
                DropdownMenuItem(value: 'macho', child: Text('Macho')),
                DropdownMenuItem(value: 'hembra', child: Text('Hembra')),
              ],
              onChanged: (v) => setState(() => _sex = v!),
            ),
            const SizedBox(height: 24),

            // ── Medidas ───────────────────────────────────────────────────────
            _SectionHeader(title: 'Medidas'),

            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _ageCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Edad *',
                      suffixText: 'meses',
                    ),
                    validator: (v) {
                      final n = int.tryParse(v ?? '');
                      if (n == null || n <= 0) return 'Inválida';
                      return null;
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _weightCtrl,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Peso *',
                      suffixText: 'kg',
                    ),
                    validator: (v) {
                      final n = double.tryParse(v ?? '');
                      if (n == null || n <= 0) return 'Inválido';
                      return null;
                    },
                  ),
                ),
              ],
            ),
            if (_species == 'perro') ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _size,
                decoration: const InputDecoration(labelText: 'Talla'),
                items: _sizeLabels.entries
                    .map((e) =>
                        DropdownMenuItem(value: e.key, child: Text(e.value)))
                    .toList(),
                onChanged: (v) => setState(() => _size = v),
                validator: (v) => v == null ? 'Selecciona talla' : null,
              ),
            ],
            const SizedBox(height: 24),

            // ── Condición física ──────────────────────────────────────────────
            _SectionHeader(title: 'Condición física'),

            DropdownButtonFormField<String>(
              value: _reproductiveStatus,
              decoration:
                  const InputDecoration(labelText: 'Estado reproductivo *'),
              items: const [
                DropdownMenuItem(
                    value: 'esterilizado', child: Text('Esterilizado/a')),
                DropdownMenuItem(
                    value: 'no_esterilizado', child: Text('No esterilizado/a')),
              ],
              onChanged: (v) => setState(() => _reproductiveStatus = v!),
            ),
            const SizedBox(height: 16),

            Text('Nivel de actividad *', style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            ...activityOptions.map(
              (level) => RadioListTile<String>(
                title: Text(level),
                value: level,
                groupValue: _activityLevel,
                onChanged: (v) => setState(() => _activityLevel = v),
                dense: true,
              ),
            ),
            const SizedBox(height: 12),

            Text(
              'BCS — Body Condition Score: $_bcs / 9',
              style: theme.textTheme.titleSmall,
            ),
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
                fontSize: 12,
                color: _bcs <= 3
                    ? Colors.orange
                    : _bcs >= 7
                        ? Colors.red
                        : Colors.green,
              ),
            ),
            const SizedBox(height: 24),

            // ── Historial médico ──────────────────────────────────────────────
            _SectionHeader(title: 'Historial médico'),

            Text('Condiciones médicas', style: theme.textTheme.titleSmall),
            ..._medicalConditions.map(
              (cond) => CheckboxListTile(
                title: Text(cond),
                value: _selectedConditions.contains(cond),
                dense: true,
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
            ),
            const SizedBox(height: 16),

            Text('Alergias / intolerancias', style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            ..._allergens.map(
              (allergen) => CheckboxListTile(
                title: Text(allergen),
                value: _selectedAllergens.contains(allergen),
                dense: true,
                onChanged: (v) => _onAllergenChanged(allergen, v ?? false),
              ),
            ),
            const SizedBox(height: 24),

            // ── Alimentación actual ───────────────────────────────────────────
            _SectionHeader(title: 'Alimentación actual'),

            for (final option in ['concentrado', 'natural', 'mixto'])
              RadioListTile<String>(
                title: Text(option == 'natural'
                    ? 'Natural/BARF'
                    : option[0].toUpperCase() + option.substring(1)),
                value: option,
                groupValue: _currentDiet,
                onChanged: (v) => setState(() => _currentDiet = v!),
                dense: true,
              ),
            const SizedBox(height: 24),

            // ── Datos del propietario ─────────────────────────────────────────
            _SectionHeader(title: 'Datos del propietario (opcional)'),

            TextFormField(
              controller: _ownerNameCtrl,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Nombre del propietario',
                prefixIcon: Icon(Icons.person_outline),
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _ownerPhoneCtrl,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(
                labelText: 'Teléfono del propietario',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
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

// ── Widgets compartidos ───────────────────────────────────────────────────────

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
              ? theme.colorScheme.primaryContainer.withAlpha(80)
              : null,
        ),
        child: Column(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 28)),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                color: selected
                    ? theme.colorScheme.primary
                    : theme.colorScheme.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
