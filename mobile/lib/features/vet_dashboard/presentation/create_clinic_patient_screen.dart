/// Pantalla para crear un paciente clínico (ClinicPet) desde el flujo del vet.
///
/// El vet ingresa los 13 campos del animal + datos de contacto del propietario.
/// Al finalizar se genera un claim code que el propietario puede usar para
/// vincular el paciente a su cuenta en la app.
///
/// Wizard de 4 pasos:
///   1. Básicos   — especie, nombre, sexo
///   2. Perfil    — raza (dropdown), edad, peso/talla
///   3. Clínico   — estado reproductivo, actividad, BCS, condiciones, alergias
///   4. Dieta     — alimentación actual + datos del propietario (opcional)
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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

const _dogBreeds = [
  'Criollo / Mestizo',
  'Labrador Retriever',
  'Golden Retriever',
  'French Bulldog',
  'Bulldog Inglés',
  'Poodle (Caniche)',
  'Beagle',
  'Rottweiler',
  'Pastor Alemán',
  'Boxer',
  'Chihuahua',
  'Dachshund (Salchicha)',
  'Shih Tzu',
  'Yorkshire Terrier',
  'Pomeranian',
  'Doberman',
  'Schnauzer Miniatura',
  'Maltés',
  'Border Collie',
  'Husky Siberiano',
  'Jack Russell Terrier',
  'Cocker Spaniel',
  'Shar Pei',
  'Gran Danés',
  'Bull Terrier',
  'Pitbull',
  'Bichón Frisé',
  'Samoyedo',
  'Akita Inu',
  'Chow Chow',
  'Otra raza...',
];

const _catBreeds = [
  'Criollo / Mestizo',
  'Siamés',
  'Persa',
  'Maine Coon',
  'Bengala',
  'Ragdoll',
  'Scottish Fold',
  'Abisinio',
  'Sphynx (Sin pelo)',
  'Birmano',
  'British Shorthair',
  'Himalayo',
  'Angora Turco',
  'Ruso Azul',
  'Noruego de los Bosques',
  'Devon Rex',
  'Burmés',
  'Otra raza...',
];

// ── Screen ─────────────────────────────────────────────────────────────────────

class CreateClinicPatientScreen extends ConsumerStatefulWidget {
  const CreateClinicPatientScreen({super.key});

  @override
  ConsumerState<CreateClinicPatientScreen> createState() =>
      _CreateClinicPatientScreenState();
}

class _CreateClinicPatientScreenState
    extends ConsumerState<CreateClinicPatientScreen> {
  // ── Wizard navigation ──────────────────────────────────────────────────────
  final _pageCtrl = PageController();
  int _currentStep = 0;
  bool _navigating = false;

  // ── Form keys por paso ─────────────────────────────────────────────────────
  final _formKey0 = GlobalKey<FormState>(); // paso 0: básicos + raza
  final _formKey1 = GlobalKey<FormState>(); // paso 1: medidas
  final _formKey4 = GlobalKey<FormState>(); // paso 4: dieta + propietario

  // ── Controllers ────────────────────────────────────────────────────────────
  final _nameCtrl = TextEditingController();
  final _customBreedCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  final _ownerNameCtrl = TextEditingController();
  final _ownerPhoneCtrl = TextEditingController();

  // ── Estado del formulario ──────────────────────────────────────────────────
  String? _selectedBreed; // null = no seleccionado aún
  int _ageYears = 0;
  int _ageMonthsExtra = 1;

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
    _pageCtrl.dispose();
    _nameCtrl.dispose();
    _customBreedCtrl.dispose();
    _weightCtrl.dispose();
    _ownerNameCtrl.dispose();
    _ownerPhoneCtrl.dispose();
    super.dispose();
  }

  // ── Navegación del wizard ──────────────────────────────────────────────────

  void _nextStep() {
    if (_navigating || _loading) return;
    if (!_validateCurrentStep()) return;

    if (_currentStep < 4) {
      setState(() {
        _currentStep++;
        _navigating = true;
      });
      _pageCtrl
          .animateToPage(
            _currentStep,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          )
          .then((_) {
        if (mounted) setState(() => _navigating = false);
      });
    } else {
      _submit();
    }
  }

  void _prevStep() {
    if (_navigating || _loading) return;
    if (_currentStep > 0) {
      setState(() {
        _currentStep--;
        _navigating = true;
      });
      _pageCtrl
          .animateToPage(
            _currentStep,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeInOut,
          )
          .then((_) {
        if (mounted) setState(() => _navigating = false);
      });
    }
  }

  bool _validateCurrentStep() {
    switch (_currentStep) {
      case 0:
        // Paso 0: básicos + raza
        if (_formKey0.currentState?.validate() == false) return false;
        final breedValue = _selectedBreed == 'Otra raza...'
            ? _customBreedCtrl.text.trim()
            : _selectedBreed ?? '';
        if (breedValue.isEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Selecciona o escribe la raza')),
          );
          return false;
        }
        return true;
      case 1:
        // Paso 1: medidas (edad + peso + talla)
        if (_formKey1.currentState?.validate() == false) return false;
        final totalMonths = _ageYears * 12 + _ageMonthsExtra;
        if (totalMonths <= 0) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('La edad debe ser mayor a 0 meses')),
          );
          return false;
        }
        return true;
      case 2:
        // Paso 2: condición física (reproductivo + actividad + BCS)
        if (_activityLevel == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Selecciona el nivel de actividad')),
          );
          return false;
        }
        return true;
      case 3:
        // Paso 3: condiciones + alergias — opcionales, siempre válido
        return true;
      default:
        return true;
    }
  }

  // ── Envío del formulario ───────────────────────────────────────────────────

  Future<void> _submit() async {
    setState(() => _loading = true);

    final breedValue = _selectedBreed == 'Otra raza...'
        ? _customBreedCtrl.text.trim()
        : (_selectedBreed ?? '');
    final conditions = _selectedConditions
        .where((c) => c != 'Ninguno conocido')
        .toList();
    final allergies = _selectedAllergens
        .where((a) => a != 'No conozco las alergias')
        .toList();
    final totalMonths = _ageYears * 12 + _ageMonthsExtra;

    try {
      final dio = ref.read(apiClientProvider);
      final response = await dio.post<Map<String, dynamic>>(
        '/v1/pets/clinic',
        data: {
          'pet_data': {
            'name': _nameCtrl.text.trim(),
            'species': _species,
            'breed': breedValue,
            'sex': _sex,
            'age_months': totalMonths,
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

  // ── Helpers alergias ───────────────────────────────────────────────────────

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
          FilledButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Continuar bajo mi responsabilidad'),
          ),
        ],
      ),
    );
  }

  // ── Build ──────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    if (_claimCode != null) return _ClaimCodeSuccess(code: _claimCode!);

    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Nuevo paciente clínico'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(
            value: (_currentStep + 1) / 5,
            backgroundColor: theme.colorScheme.surfaceContainerHighest,
            minHeight: 4,
          ),
        ),
      ),
      bottomNavigationBar: _VetWizardNavBar(
        currentStep: _currentStep,
        totalSteps: 5,
        loading: _loading || _navigating,
        onBack: (_currentStep > 0 && !_navigating && !_loading)
            ? _prevStep
            : null,
        onNext: _nextStep,
      ),
      body: PageView(
        controller: _pageCtrl,
        physics: const NeverScrollableScrollPhysics(),
        children: [
          _buildStep0(theme), // Especie + Nombre + Raza + Sexo
          _buildStep1(theme), // Edad + Peso + Talla
          _buildStep2(theme), // Reproductivo + Actividad + BCS
          _buildStep3(theme), // Condiciones + Alergias
          _buildStep4(theme), // Alimentación + Propietario
        ],
      ),
    );
  }

  // ── Paso 0: Básicos (especie + nombre + raza + sexo) ──────────────────────

  List<String> get _sortedBreeds {
    final raw = (_species == 'perro' ? _dogBreeds : _catBreeds).toList();
    raw.remove('Criollo / Mestizo');
    raw.remove('Otra raza...');
    raw.sort();
    return ['Criollo / Mestizo', ...raw, 'Otra raza...'];
  }

  Widget _buildStep0(ThemeData theme) {
    return Form(
      key: _formKey0,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          Text(
            'Datos básicos',
            style: theme.textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            'Especie, nombre, raza y sexo del paciente',
            style: theme.textTheme.bodyMedium
                ?.copyWith(color: theme.colorScheme.outline),
          ),
          const SizedBox(height: 24),

          // Especie
          Text('Especie *',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
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
                    _selectedBreed = null;
                    _customBreedCtrl.clear();
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
                    _selectedBreed = null;
                    _customBreedCtrl.clear();
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Nombre
          TextFormField(
            controller: _nameCtrl,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Nombre del animal *',
              prefixIcon: Icon(Icons.pets_outlined),
              hintText: 'Luna, Max, Mochi...',
            ),
            validator: (v) =>
                (v == null || v.trim().isEmpty) ? 'Requerido' : null,
          ),
          const SizedBox(height: 20),

          // Raza — dropdown ordenado alfabéticamente
          Text('Raza *',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            value: _selectedBreed,
            isExpanded: true,
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search),
              hintText: 'Selecciona la raza',
            ),
            hint: Text(
              'Selecciona la raza de ${_species == "perro" ? "tu canino" : "tu felino"}',
            ),
            items: _sortedBreeds
                .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                .toList(),
            onChanged: (v) => setState(() {
              _selectedBreed = v;
              if (v != 'Otra raza...') _customBreedCtrl.clear();
            }),
          ),
          if (_selectedBreed == 'Otra raza...') ...[
            const SizedBox(height: 12),
            TextFormField(
              controller: _customBreedCtrl,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Especifica la raza *',
                prefixIcon: Icon(Icons.edit_outlined),
                hintText: 'Ej: French Poodle, Mestizo...',
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Requerido' : null,
            ),
          ],
          const SizedBox(height: 20),

          // Sexo
          Text('Sexo *',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _RadioCard(
                  label: 'Macho',
                  icon: Icons.male,
                  selected: _sex == 'macho',
                  onTap: () => setState(() => _sex = 'macho'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _RadioCard(
                  label: 'Hembra',
                  icon: Icons.female,
                  selected: _sex == 'hembra',
                  onTap: () => setState(() => _sex = 'hembra'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ── Paso 1: Medidas ────────────────────────────────────────────────────────

  Widget _buildStep1(ThemeData theme) {
    final totalMonths = _ageYears * 12 + _ageMonthsExtra;

    return Form(
      key: _formKey1,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          Text(
            'Medidas del paciente',
            style: theme.textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            'Edad, peso y talla',
            style: theme.textTheme.bodyMedium
                ?.copyWith(color: theme.colorScheme.outline),
          ),
          const SizedBox(height: 24),

          // Edad
          Text('Edad *',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<int>(
                  value: _ageYears,
                  decoration: const InputDecoration(labelText: 'Años'),
                  isExpanded: true,
                  items: List.generate(
                    21,
                    (i) => DropdownMenuItem(
                      value: i,
                      child: Text(
                        i == 0 ? '< 1 año' : '$i año${i > 1 ? "s" : ""}',
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
                  decoration: const InputDecoration(labelText: 'Meses +'),
                  isExpanded: true,
                  items: List.generate(
                    12,
                    (i) => DropdownMenuItem(
                      value: i,
                      child: Text('$i mes${i != 1 ? "es" : ""}'),
                    ),
                  ),
                  onChanged: (v) {
                    if (v != null) setState(() => _ageMonthsExtra = v);
                  },
                ),
              ),
            ],
          ),
          if (totalMonths > 0) ...[
            const SizedBox(height: 4),
            Text(
              'Total: $totalMonths ${totalMonths == 1 ? "mes" : "meses"}',
              style: TextStyle(
                fontSize: 12,
                color: theme.colorScheme.outline,
              ),
            ),
          ],
          const SizedBox(height: 20),

          // Peso + talla
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _weightCtrl,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Peso *',
                    suffixText: 'kg',
                    prefixIcon: Icon(Icons.monitor_weight_outlined),
                    hintText: '8.5',
                  ),
                  validator: (v) {
                    final n = double.tryParse(v ?? '');
                    if (n == null || n <= 0) return 'Inválido';
                    return null;
                  },
                ),
              ),
              if (_species == 'perro') ...[
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _size,
                    decoration: const InputDecoration(labelText: 'Talla *'),
                    isExpanded: true,
                    hint: const Text('Selecciona'),
                    items: _sizeLabels.entries
                        .map((e) => DropdownMenuItem(
                            value: e.key, child: Text(e.value)))
                        .toList(),
                    onChanged: (v) => setState(() => _size = v),
                    validator: (v) => v == null ? 'Requerido' : null,
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  // ── Paso 2: Condición física ───────────────────────────────────────────────

  Widget _buildStep2(ThemeData theme) {
    final activityOptions =
        _species == 'perro' ? _activityLevelsDog : _activityLevelsCat;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      children: [
        Text(
          'Condición física',
          style: theme.textTheme.headlineSmall
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          'Estado reproductivo, actividad y condición corporal',
          style: theme.textTheme.bodyMedium
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 24),

        // Estado reproductivo
        Text('Estado reproductivo *',
            style: theme.textTheme.titleSmall
                ?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _RadioCard(
                label: 'Esterilizado/a',
                icon: Icons.check_circle_outline,
                selected: _reproductiveStatus == 'esterilizado',
                onTap: () =>
                    setState(() => _reproductiveStatus = 'esterilizado'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _RadioCard(
                label: 'Sin esterilizar',
                icon: Icons.radio_button_unchecked,
                selected: _reproductiveStatus == 'no_esterilizado',
                onTap: () =>
                    setState(() => _reproductiveStatus = 'no_esterilizado'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        // Nivel de actividad
        DropdownButtonFormField<String>(
          value: _activityLevel,
          decoration: const InputDecoration(
            labelText: 'Nivel de actividad *',
            prefixIcon: Icon(Icons.directions_run),
          ),
          hint: const Text('Selecciona'),
          items: activityOptions
              .map((a) => DropdownMenuItem(
                  value: a, child: Text(a.replaceAll('_', ' '))))
              .toList(),
          onChanged: (v) => setState(() => _activityLevel = v),
        ),
        const SizedBox(height: 24),

        // BCS
        Text(
          'Condición corporal (BCS) — $_bcs/9',
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
            Text('1 · Muy delgado', style: theme.textTheme.labelSmall),
            Text('5 · Ideal', style: theme.textTheme.labelSmall),
            Text('9 · Obeso', style: theme.textTheme.labelSmall),
          ],
        ),
      ],
    );
  }

  // ── Paso 3: Historial médico y alergias ───────────────────────────────────

  Widget _buildStep3(ThemeData theme) {
    final hasConditions = _selectedConditions
        .where((c) => c != 'Ninguno conocido')
        .isNotEmpty;

    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
      children: [
        Text(
          'Historial médico',
          style: theme.textTheme.headlineSmall
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          'Condiciones médicas y alergias / intolerancias',
          style: theme.textTheme.bodyMedium
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 24),

        // Condiciones médicas
        Text('Condiciones médicas',
            style: theme.textTheme.titleSmall
                ?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        Text(
          'Selecciona todas las que apliquen.',
          style: theme.textTheme.bodySmall
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 12),

        _ConditionTile(
          label: 'Ninguno conocido',
          selected: _selectedConditions.contains('Ninguno conocido'),
          isHealthy: true,
          onToggle: (v) => setState(() {
            if (v) {
              _selectedConditions
                ..clear()
                ..add('Ninguno conocido');
            } else {
              _selectedConditions.remove('Ninguno conocido');
            }
          }),
        ),
        const Divider(height: 20),

        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _medicalConditions
              .where((c) => c != 'Ninguno conocido')
              .map((c) => FilterChip(
                    label: Text(
                      c.replaceAll('_', ' ').replaceAll('/', ' / '),
                      style: const TextStyle(fontSize: 12),
                    ),
                    selected: _selectedConditions.contains(c),
                    onSelected:
                        _selectedConditions.contains('Ninguno conocido')
                            ? null
                            : (v) => setState(() {
                                  if (v) {
                                    _selectedConditions
                                      ..remove('Ninguno conocido')
                                      ..add(c);
                                  } else {
                                    _selectedConditions.remove(c);
                                  }
                                }),
                    selectedColor: theme.colorScheme.primaryContainer,
                  ))
              .toList(),
        ),

        if (hasConditions) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.orange.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.orange.shade200),
            ),
            child: const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline, color: Colors.orange, size: 16),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Este paciente requerirá revisión veterinaria antes de '
                    'activar el plan nutricional (PENDING_VET).',
                    style: TextStyle(fontSize: 11, color: Colors.orange),
                  ),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 24),

        // Alergias / intolerancias
        Text('Alergias / intolerancias',
            style: theme.textTheme.titleSmall
                ?.copyWith(fontWeight: FontWeight.w600)),
        const SizedBox(height: 4),
        Text(
          'Selecciona todas las que apliquen.',
          style: theme.textTheme.bodySmall
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 12),

        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _allergens
              .map((a) => FilterChip(
                    label: Text(a, style: const TextStyle(fontSize: 12)),
                    selected: _selectedAllergens.contains(a),
                    onSelected: (v) => _onAllergenChanged(a, v),
                    selectedColor: a == 'No conozco las alergias'
                        ? Colors.orange.shade100
                        : theme.colorScheme.primaryContainer,
                  ))
              .toList(),
        ),
      ],
    );
  }

  // ── Paso 4: Alimentación + propietario ─────────────────────────────────────

  Widget _buildStep4(ThemeData theme) {
    return Form(
      key: _formKey4,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 32),
        children: [
          Text(
            'Alimentación y propietario',
            style: theme.textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            'Dieta actual y contacto del propietario (opcional)',
            style: theme.textTheme.bodyMedium
                ?.copyWith(color: theme.colorScheme.outline),
          ),
          const SizedBox(height: 24),

          // Dieta actual
          Text('Alimentación actual *',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 12),

          _DietCard(
            label: 'Concentrado / croquetas',
            subtitle: 'Alimento seco o húmedo comercial',
            icon: Icons.inventory_2_outlined,
            value: 'concentrado',
            selected: _currentDiet == 'concentrado',
            onTap: () => setState(() => _currentDiet = 'concentrado'),
          ),
          const SizedBox(height: 8),
          _DietCard(
            label: 'Dieta natural',
            subtitle: 'BARF, cocinado casero o mixto natural',
            icon: Icons.grass_outlined,
            value: 'natural',
            selected: _currentDiet == 'natural',
            onTap: () => setState(() => _currentDiet = 'natural'),
          ),
          const SizedBox(height: 8),
          _DietCard(
            label: 'Mixto',
            subtitle: 'Concentrado + alimentos naturales',
            icon: Icons.merge_outlined,
            value: 'mixto',
            selected: _currentDiet == 'mixto',
            onTap: () => setState(() => _currentDiet = 'mixto'),
          ),
          const SizedBox(height: 28),

          // Propietario (opcional)
          Row(
            children: [
              Text(
                'Datos del propietario',
                style: theme.textTheme.titleSmall
                    ?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(width: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'opcional',
                  style: TextStyle(
                    fontSize: 11,
                    color: theme.colorScheme.outline,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'Si lo ingresas, aparecerá en la ficha del paciente.',
            style: theme.textTheme.bodySmall
                ?.copyWith(color: theme.colorScheme.outline),
          ),
          const SizedBox(height: 12),

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
        ],
      ),
    );
  }

  // ── Helpers BCS ────────────────────────────────────────────────────────────

  String _bcsDescription(int bcs) {
    if (bcs <= 2) return 'Muy delgado — pérdida de masa muscular visible';
    if (bcs == 3) return 'Bajo peso — costillas muy palpables';
    if (bcs == 4) return 'Levemente delgado — costillas fácilmente palpables';
    if (bcs == 5) return 'Peso ideal — cintura visible';
    if (bcs == 6) return 'Levemente sobrepeso';
    if (bcs == 7) return 'Sobrepeso — costillas difíciles de palpar';
    if (bcs == 8) return 'Obeso — sin cintura definida';
    return 'Obesidad severa';
  }

  Color _bcsColor(int bcs) {
    if (bcs <= 3) return Colors.blue;
    if (bcs <= 6) return Colors.green;
    return Colors.orange;
  }
}

// ── Barra de navegación del wizard ────────────────────────────────────────────

class _VetWizardNavBar extends StatelessWidget {
  const _VetWizardNavBar({
    required this.currentStep,
    required this.totalSteps,
    required this.loading,
    required this.onNext,
    this.onBack,
  });

  final int currentStep;
  final int totalSteps;
  final bool loading;
  final VoidCallback onNext;
  final VoidCallback? onBack;

  bool get isLast => currentStep == totalSteps - 1;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    // Inset explícito — evita doble padding con SafeArea en edge-to-edge Android
    final bottomInset = MediaQuery.viewPaddingOf(context).bottom;

    // Column(mainAxisSize.min) garantiza altura mínima reportada correctamente
    // al Scaffold para que body no solape la barra de navegación.
    return ColoredBox(
      color: theme.colorScheme.surface,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Divider(
            height: 0.5,
            thickness: 0.5,
            color: theme.colorScheme.outlineVariant,
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(16, 10, 16, 12 + bottomInset),
            child: Row(
              children: [
                // Indicador de pasos
                Text(
                  '${currentStep + 1}/$totalSteps',
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: theme.colorScheme.outline,
                  ),
                ),
                const SizedBox(width: 12),

                if (onBack != null) ...[
                  OutlinedButton.icon(
                    onPressed: onBack,
                    // Sobreescribe minimumSize del tema (Size.fromHeight = ∞ ancho)
                    // para evitar RenderFlex overflow dentro del Row.
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(80, 44),
                    ),
                    icon: const Icon(Icons.arrow_back, size: 18),
                    label: const Text('Atrás'),
                  ),
                  const SizedBox(width: 12),
                ],

                Expanded(
                  child: FilledButton.icon(
                    onPressed: loading ? null : onNext,
                    style: FilledButton.styleFrom(
                      minimumSize:
                          isLast ? const Size.fromHeight(52) : const Size(0, 44),
                    ),
                    icon: loading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : Icon(
                            isLast
                                ? Icons.check_circle_outline
                                : Icons.arrow_forward,
                            size: 20,
                          ),
                    label: Text(
                      isLast ? 'Crear paciente' : 'Siguiente',
                      style: const TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 15),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Pantalla de éxito: claim code ─────────────────────────────────────────────

class _ClaimCodeSuccess extends StatelessWidget {
  const _ClaimCodeSuccess({required this.code});

  final String code;

  /// Formatea el código en grupos de 4 caracteres separados por espacio.
  String _formatCode(String raw) {
    final clean = raw.replaceAll(RegExp(r'[\s-]'), '');
    final buf = StringBuffer();
    for (var i = 0; i < clean.length; i++) {
      if (i > 0 && i % 4 == 0) buf.write('  ');
      buf.write(clean[i]);
    }
    return buf.toString();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final formatted = _formatCode(code);

    return Scaffold(
      appBar: AppBar(
        title: const NutrivetTitle('Paciente creado'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go('/vet/dashboard'),
        ),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 72),
              const SizedBox(height: 20),
              Text(
                'Paciente creado correctamente',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 28),
              Text(
                'Código de vinculación para el propietario:',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.outline,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),

              // Card con el código formateado
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                    horizontal: 24, vertical: 20),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: theme.colorScheme.primary.withAlpha(60),
                    width: 1.5,
                  ),
                ),
                child: Column(
                  children: [
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: SelectableText(
                        formatted,
                        style: theme.textTheme.headlineMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                          letterSpacing: 3,
                          color: theme.colorScheme.primary,
                          fontFamily: 'monospace',
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      code, // código original para copiar sin espacios
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: theme.colorScheme.outline,
                        letterSpacing: 1,
                      ),
                    ),
                  ],
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
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  OutlinedButton.icon(
                    onPressed: () async {
                      await Clipboard.setData(ClipboardData(text: code));
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Código copiado al portapapeles'),
                            duration: Duration(seconds: 2),
                          ),
                        );
                      }
                    },
                    icon: const Icon(Icons.copy, size: 18),
                    label: const Text('Copiar código'),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: () => context.go('/vet/dashboard'),
                    icon: const Icon(Icons.dashboard_outlined, size: 18),
                    label: const Text('Dashboard'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Widgets compartidos ───────────────────────────────────────────────────────

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

/// Card visual de selección binaria (macho/hembra, esterilizado/no).
class _RadioCard extends StatelessWidget {
  const _RadioCard({
    required this.label,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
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
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 18,
              color: selected
                  ? theme.colorScheme.primary
                  : theme.colorScheme.outline,
            ),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight:
                      selected ? FontWeight.bold : FontWeight.normal,
                  color: selected
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurface,
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Ítem de selección para "Ninguno conocido" en condiciones médicas.
class _ConditionTile extends StatelessWidget {
  const _ConditionTile({
    required this.label,
    required this.selected,
    required this.isHealthy,
    required this.onToggle,
  });

  final String label;
  final bool selected;
  final bool isHealthy;
  final void Function(bool) onToggle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: () => onToggle(!selected),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          border: Border.all(
            color: selected
                ? Colors.green
                : theme.colorScheme.outlineVariant,
            width: selected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(8),
          color: selected ? Colors.green.shade50 : null,
        ),
        child: Row(
          children: [
            Icon(
              selected ? Icons.check_circle : Icons.radio_button_unchecked,
              color: selected ? Colors.green : theme.colorScheme.outline,
              size: 20,
            ),
            const SizedBox(width: 10),
            Text(
              label,
              style: TextStyle(
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                color: selected ? Colors.green.shade700 : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Card visual para selección de dieta actual.
class _DietCard extends StatelessWidget {
  const _DietCard({
    required this.label,
    required this.subtitle,
    required this.icon,
    required this.value,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final String subtitle;
  final IconData icon;
  final String value;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          border: Border.all(
            color: selected
                ? theme.colorScheme.primary
                : theme.colorScheme.outlineVariant,
            width: selected ? 2 : 1,
          ),
          borderRadius: BorderRadius.circular(10),
          color: selected
              ? theme.colorScheme.primaryContainer.withAlpha(80)
              : null,
        ),
        child: Row(
          children: [
            Icon(
              icon,
              size: 24,
              color: selected
                  ? theme.colorScheme.primary
                  : theme.colorScheme.outline,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      color: selected ? theme.colorScheme.primary : null,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ],
              ),
            ),
            if (selected)
              Icon(Icons.check_circle,
                  color: theme.colorScheme.primary, size: 20),
          ],
        ),
      ),
    );
  }
}
