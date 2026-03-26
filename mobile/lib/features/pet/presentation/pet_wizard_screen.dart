/// Wizard de registro de mascota — 6 pasos progresivos.
///
/// Paso 1: Especie + Nombre + Raza + Sexo
/// Paso 2: Edad + Peso + Talla (solo perros)
/// Paso 3: Estado reproductivo + Actividad + BCS
/// Paso 4: Condiciones médicas
/// Paso 5: Alergias / intolerancias
/// Paso 6: Alimentación actual + Confirmar
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/app_footer.dart';
import '../data/pet_repository.dart';
import 'dashboard_screen.dart';

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

// ── Títulos de pasos ──────────────────────────────────────────────────────────
const _stepTitles = [
  'Tu mascota',
  'Medidas',
  'Condición física',
  'Historial médico',
  'Alergias',
  'Alimentación',
];

const _stepIcons = [
  Icons.pets,
  Icons.monitor_weight_outlined,
  Icons.fitness_center_outlined,
  Icons.medical_services_outlined,
  Icons.warning_amber_outlined,
  Icons.restaurant_outlined,
];

// ── Widget principal ──────────────────────────────────────────────────────────

class PetWizardScreen extends ConsumerStatefulWidget {
  const PetWizardScreen({super.key});

  @override
  ConsumerState<PetWizardScreen> createState() => _PetWizardScreenState();
}

class _PetWizardScreenState extends ConsumerState<PetWizardScreen> {
  final _pageCtrl = PageController();
  int _currentStep = 0;

  // ── Form keys por paso ─────────────────────────────────────────────────────
  final _step1Key = GlobalKey<FormState>();
  final _step2Key = GlobalKey<FormState>();
  final _step3Key = GlobalKey<FormState>();

  // ── Controllers ───────────────────────────────────────────────────────────
  final _nameCtrl = TextEditingController();
  final _breedCtrl = TextEditingController();
  final _ageCtrl = TextEditingController();
  final _weightCtrl = TextEditingController();
  final _customAllergyCtrl = TextEditingController();

  // ── Estado del formulario ─────────────────────────────────────────────────
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

  @override
  void dispose() {
    _pageCtrl.dispose();
    _nameCtrl.dispose();
    _breedCtrl.dispose();
    _ageCtrl.dispose();
    _weightCtrl.dispose();
    _customAllergyCtrl.dispose();
    super.dispose();
  }

  // ── Validación por paso ───────────────────────────────────────────────────

  bool _validateCurrentStep() {
    switch (_currentStep) {
      case 0:
        return _step1Key.currentState?.validate() ?? false;
      case 1:
        if (_step2Key.currentState?.validate() == false) return false;
        if (_species == 'perro' && _size == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Selecciona la talla de tu perro')),
          );
          return false;
        }
        return true;
      case 2:
        if (_step3Key.currentState?.validate() == false) return false;
        if (_activityLevel == null) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Selecciona el nivel de actividad')),
          );
          return false;
        }
        return true;
      default:
        return true;
    }
  }

  void _nextStep() {
    if (!_validateCurrentStep()) return;
    if (_currentStep < 5) {
      setState(() => _currentStep++);
      _pageCtrl.animateToPage(
        _currentStep,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      _submit();
    }
  }

  void _prevStep() {
    if (_currentStep > 0) {
      setState(() => _currentStep--);
      _pageCtrl.animateToPage(
        _currentStep,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    } else {
      context.pop();
    }
  }

  // ── Envío ─────────────────────────────────────────────────────────────────

  Future<void> _submit() async {
    setState(() => _loading = true);

    final conditions = _selectedConditions
        .where((c) => c != 'Ninguno conocido')
        .toList();
    final allergies = [
      ..._selectedAllergens.where((a) => a != 'No conozco las alergias'),
      ..._customAllergyCtrl.text
          .split(',')
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty),
    ];

    try {
      await ref.read(petRepositoryProvider).createPet({
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
      });
      ref.invalidate(petsProvider);
      if (mounted) context.go('/dashboard');
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              e.toString().contains('Exception:')
                  ? e.toString().replaceFirst('Exception: ', '')
                  : 'Error al guardar el perfil. Intenta de nuevo.',
            ),
          ),
        );
        setState(() => _loading = false);
      }
    }
  }

  // ── Alerta de alergenos desconocidos ──────────────────────────────────────

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
          'Sin conocer las alergias de tu mascota, el plan nutricional '
          'podría incluir ingredientes que causen reacciones adversas.\n\n'
          'Te recomendamos realizar una prueba de alergenos con tu veterinario '
          'antes de iniciar el plan.',
        ),
        actions: [
          OutlinedButton(
            onPressed: () {
              Navigator.pop(ctx);
              setState(() =>
                  _selectedAllergens.remove('No conozco las alergias'));
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

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return PopScope(
      canPop: _currentStep == 0,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop && _currentStep > 0) _prevStep();
      },
      child: Scaffold(
        appBar: AppBar(
          title: const NutrivetTitle('Nueva mascota'),
          leading: IconButton(
            icon: const Icon(Icons.arrow_back),
            onPressed: _prevStep,
          ),
        ),
        bottomNavigationBar: const AppFooter(),
        body: Column(
          children: [
            // ── Indicador de progreso ────────────────────────────────────────
            _StepProgress(
              current: _currentStep,
              total: 6,
              stepTitles: _stepTitles,
              stepIcons: _stepIcons,
            ),

            // ── Páginas ──────────────────────────────────────────────────────
            Expanded(
              child: PageView(
                controller: _pageCtrl,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  _Step1Identity(
                    formKey: _step1Key,
                    species: _species,
                    nameCtrl: _nameCtrl,
                    breedCtrl: _breedCtrl,
                    sex: _sex,
                    onSpeciesChanged: (v) => setState(() {
                      _species = v;
                      _activityLevel = null;
                      _size = null;
                    }),
                    onSexChanged: (v) => setState(() => _sex = v),
                  ),
                  _Step2Measures(
                    formKey: _step2Key,
                    species: _species,
                    ageCtrl: _ageCtrl,
                    weightCtrl: _weightCtrl,
                    size: _size,
                    onSizeChanged: (v) => setState(() => _size = v),
                  ),
                  _Step3Condition(
                    formKey: _step3Key,
                    species: _species,
                    reproductiveStatus: _reproductiveStatus,
                    activityLevel: _activityLevel,
                    bcs: _bcs,
                    onReproductiveChanged: (v) =>
                        setState(() => _reproductiveStatus = v),
                    onActivityChanged: (v) =>
                        setState(() => _activityLevel = v),
                    onBcsChanged: (v) => setState(() => _bcs = v),
                  ),
                  _Step4MedicalHistory(
                    selectedConditions: _selectedConditions,
                    onToggle: (c, selected) {
                      setState(() {
                        if (selected) {
                          if (c == 'Ninguno conocido') {
                            _selectedConditions
                              ..clear()
                              ..add(c);
                          } else {
                            _selectedConditions
                              ..remove('Ninguno conocido')
                              ..add(c);
                          }
                        } else {
                          _selectedConditions.remove(c);
                        }
                      });
                    },
                  ),
                  _Step5Allergies(
                    selectedAllergens: _selectedAllergens,
                    customCtrl: _customAllergyCtrl,
                    onAllergenChanged: _onAllergenChanged,
                  ),
                  _Step6Diet(
                    currentDiet: _currentDiet,
                    onDietChanged: (v) => setState(() => _currentDiet = v),
                    // Resumen para revisión
                    petName: _nameCtrl.text,
                    species: _species,
                    breed: _breedCtrl.text,
                    conditions: _selectedConditions
                        .where((c) => c != 'Ninguno conocido')
                        .toList(),
                  ),
                ],
              ),
            ),

            // ── Barra de navegación ──────────────────────────────────────────
            _WizardNavBar(
              currentStep: _currentStep,
              totalSteps: 6,
              loading: _loading,
              onBack: _currentStep > 0 ? _prevStep : null,
              onNext: _nextStep,
            ),
          ],
        ),
      ),
    );
  }
}

// ── Indicador de progreso ─────────────────────────────────────────────────────

class _StepProgress extends StatelessWidget {
  const _StepProgress({
    required this.current,
    required this.total,
    required this.stepTitles,
    required this.stepIcons,
  });

  final int current;
  final int total;
  final List<String> stepTitles;
  final List<IconData> stepIcons;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outlineVariant,
            width: 0.5,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Título del paso actual
          Row(
            children: [
              Icon(stepIcons[current],
                  size: 18, color: theme.colorScheme.primary),
              const SizedBox(width: 8),
              Text(
                'Paso ${current + 1} de $total — ${stepTitles[current]}',
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Barra de progreso lineal
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (current + 1) / total,
              minHeight: 6,
              backgroundColor: theme.colorScheme.outlineVariant.withOpacity(0.3),
              valueColor:
                  AlwaysStoppedAnimation<Color>(theme.colorScheme.primary),
            ),
          ),
          const SizedBox(height: 4),
          // Marcadores de pasos
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: List.generate(total, (i) {
              final isDone = i < current;
              final isActive = i == current;
              return Flexible(
                child: Center(
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    width: isActive ? 8 : 6,
                    height: isActive ? 8 : 6,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isDone || isActive
                          ? theme.colorScheme.primary
                          : theme.colorScheme.outlineVariant,
                    ),
                  ),
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}

// ── Barra navegación inferior ─────────────────────────────────────────────────

class _WizardNavBar extends StatelessWidget {
  const _WizardNavBar({
    required this.currentStep,
    required this.totalSteps,
    required this.loading,
    required this.onNext,
    this.onBack,
  });

  final int currentStep;
  final int totalSteps;
  final bool loading;
  final VoidCallback? onBack;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final isLast = currentStep == totalSteps - 1;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Row(
          children: [
            if (onBack != null) ...[
              OutlinedButton.icon(
                onPressed: onBack,
                icon: const Icon(Icons.arrow_back, size: 18),
                label: const Text('Anterior'),
              ),
              const SizedBox(width: 12),
            ],
            Expanded(
              child: FilledButton.icon(
                onPressed: loading ? null : onNext,
                icon: loading
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white),
                      )
                    : Icon(
                        isLast ? Icons.check : Icons.arrow_forward,
                        size: 18,
                      ),
                label: Text(isLast ? 'Guardar mascota' : 'Siguiente'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Paso 1: Identidad ─────────────────────────────────────────────────────────

class _Step1Identity extends StatelessWidget {
  const _Step1Identity({
    required this.formKey,
    required this.species,
    required this.nameCtrl,
    required this.breedCtrl,
    required this.sex,
    required this.onSpeciesChanged,
    required this.onSexChanged,
  });

  final GlobalKey<FormState> formKey;
  final String species;
  final TextEditingController nameCtrl;
  final TextEditingController breedCtrl;
  final String sex;
  final void Function(String) onSpeciesChanged;
  final void Function(String) onSexChanged;

  @override
  Widget build(BuildContext context) {
    return Form(
      key: formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          // Especie
          Text('¿Qué tipo de mascota es?',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _SpeciesCard(
                  key: const ValueKey('species_dog'),
                  label: 'Canino',
                  emoji: '🐕',
                  selected: species == 'perro',
                  onTap: () => onSpeciesChanged('perro'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _SpeciesCard(
                  key: const ValueKey('species_cat'),
                  label: 'Felino',
                  emoji: '🐈',
                  selected: species == 'gato',
                  onTap: () => onSpeciesChanged('gato'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          TextFormField(
            key: const ValueKey('pet_name_field'),
            controller: nameCtrl,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Nombre de la mascota *',
              prefixIcon: Icon(Icons.pets_outlined),
              hintText: 'Luna, Max, Mochi...',
            ),
            validator: (v) =>
                (v == null || v.trim().isEmpty) ? 'Ingresa el nombre' : null,
          ),
          const SizedBox(height: 12),

          TextFormField(
            key: const ValueKey('breed_field'),
            controller: breedCtrl,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Raza *',
              prefixIcon: Icon(Icons.search),
              hintText: 'Golden Retriever, Siamés, mestizo...',
            ),
            validator: (v) =>
                (v == null || v.trim().isEmpty) ? 'Ingresa la raza' : null,
          ),
          const SizedBox(height: 16),

          Text('Sexo',
              style: Theme.of(context)
                  .textTheme
                  .titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _RadioCard(
                  label: 'Macho',
                  icon: Icons.male,
                  selected: sex == 'macho',
                  onTap: () => onSexChanged('macho'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _RadioCard(
                  label: 'Hembra',
                  icon: Icons.female,
                  selected: sex == 'hembra',
                  onTap: () => onSexChanged('hembra'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Paso 2: Medidas ───────────────────────────────────────────────────────────

class _Step2Measures extends StatelessWidget {
  const _Step2Measures({
    required this.formKey,
    required this.species,
    required this.ageCtrl,
    required this.weightCtrl,
    required this.size,
    required this.onSizeChanged,
  });

  final GlobalKey<FormState> formKey;
  final String species;
  final TextEditingController ageCtrl;
  final TextEditingController weightCtrl;
  final String? size;
  final void Function(String?) onSizeChanged;

  @override
  Widget build(BuildContext context) {
    return Form(
      key: formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Cuéntanos más sobre su cuerpo',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: TextFormField(
                  key: const ValueKey('age_field'),
                  controller: ageCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Edad *',
                    suffixText: 'meses',
                    hintText: '24',
                    prefixIcon: Icon(Icons.cake_outlined),
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
                  key: const ValueKey('weight_field'),
                  controller: weightCtrl,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'Peso *',
                    suffixText: 'kg',
                    hintText: '8.5',
                    prefixIcon: Icon(Icons.monitor_weight_outlined),
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

          if (species == 'perro') ...[
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              key: const ValueKey('size_dropdown'),
              value: size,
              decoration: const InputDecoration(
                labelText: 'Talla *',
                prefixIcon: Icon(Icons.height),
              ),
              items: _sizeLabels.entries
                  .map((e) => DropdownMenuItem(
                      value: e.key, child: Text(e.value)))
                  .toList(),
              onChanged: onSizeChanged,
            ),
          ] else ...[
            const SizedBox(height: 20),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.blue, size: 18),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Para gatos no aplicamos clasificación por talla — '
                      'usamos el peso y BCS directamente.',
                      style: TextStyle(fontSize: 12, color: Colors.blue),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.orange.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.lightbulb_outline,
                    color: Colors.orange, size: 18),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Ingresa el peso actual de la mascota. '
                    'Ajustaremos el plan si el peso cambia.',
                    style: TextStyle(fontSize: 12, color: Colors.orange),
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

// ── Paso 3: Condición física ──────────────────────────────────────────────────

class _Step3Condition extends StatelessWidget {
  const _Step3Condition({
    required this.formKey,
    required this.species,
    required this.reproductiveStatus,
    required this.activityLevel,
    required this.bcs,
    required this.onReproductiveChanged,
    required this.onActivityChanged,
    required this.onBcsChanged,
  });

  final GlobalKey<FormState> formKey;
  final String species;
  final String reproductiveStatus;
  final String? activityLevel;
  final int bcs;
  final void Function(String) onReproductiveChanged;
  final void Function(String?) onActivityChanged;
  final void Function(int) onBcsChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final activityOptions =
        species == 'perro' ? _activityLevelsDog : _activityLevelsCat;

    return Form(
      key: formKey,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Estado y actividad',
            style: theme.textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),

          // Estado reproductivo
          Text('Estado reproductivo *',
              style: theme.textTheme.titleSmall
                  ?.copyWith(fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _RadioCard(
                  label: 'Esterilizado',
                  icon: Icons.check_circle_outline,
                  selected: reproductiveStatus == 'esterilizado',
                  onTap: () => onReproductiveChanged('esterilizado'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _RadioCard(
                  label: 'Sin esterilizar',
                  icon: Icons.radio_button_unchecked,
                  selected: reproductiveStatus == 'no_esterilizado',
                  onTap: () => onReproductiveChanged('no_esterilizado'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Nivel de actividad
          DropdownButtonFormField<String>(
            value: activityLevel,
            decoration: const InputDecoration(
              labelText: 'Nivel de actividad *',
              prefixIcon: Icon(Icons.directions_run),
            ),
            items: activityOptions
                .map((a) => DropdownMenuItem(
                    value: a,
                    child: Text(a.replaceAll('_', ' '))))
                .toList(),
            onChanged: onActivityChanged,
          ),
          const SizedBox(height: 20),

          // BCS
          Text(
            'Condición corporal (BCS) — $bcs/9',
            style: theme.textTheme.titleSmall
                ?.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 4),
          Text(
            _bcsDescription(bcs),
            style: TextStyle(
              fontSize: 12,
              color: _bcsColor(bcs),
              fontWeight: FontWeight.w500,
            ),
          ),
          Slider(
            value: bcs.toDouble(),
            min: 1,
            max: 9,
            divisions: 8,
            label: '$bcs',
            onChanged: (v) => onBcsChanged(v.round()),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('1 · Muy delgado',
                  style: theme.textTheme.labelSmall),
              Text('5 · Ideal', style: theme.textTheme.labelSmall),
              Text('9 · Obeso',
                  style: theme.textTheme.labelSmall),
            ],
          ),
        ],
      ),
    );
  }

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

// ── Paso 4: Historial médico ──────────────────────────────────────────────────

class _Step4MedicalHistory extends StatelessWidget {
  const _Step4MedicalHistory({
    required this.selectedConditions,
    required this.onToggle,
  });

  final Set<String> selectedConditions;
  final void Function(String, bool) onToggle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final hasNone = selectedConditions.contains('Ninguno conocido');

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          '¿Tiene alguna condición médica?',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          'Esta información determina si el plan requiere revisión veterinaria.',
          style: theme.textTheme.bodySmall
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 16),

        // Opción "Ninguno"
        _ConditionTile(
          label: 'Ninguno conocido',
          selected: hasNone,
          isHealthy: true,
          onToggle: (v) => onToggle('Ninguno conocido', v),
        ),
        const Divider(height: 20),

        // Condiciones médicas
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _medicalConditions
              .where((c) => c != 'Ninguno conocido')
              .map((c) => FilterChip(
                    label: Text(c.replaceAll('_', ' '),
                        style: const TextStyle(fontSize: 12)),
                    selected: selectedConditions.contains(c),
                    onSelected: hasNone ? null : (v) => onToggle(c, v),
                    selectedColor:
                        theme.colorScheme.primaryContainer,
                  ))
              .toList(),
        ),

        if (selectedConditions
            .where((c) => c != 'Ninguno conocido')
            .isNotEmpty) ...[
          const SizedBox(height: 16),
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
                Icon(Icons.info_outline,
                    color: Colors.orange, size: 16),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Los planes con condiciones médicas requieren revisión '
                    'y firma de un veterinario antes de activarse.',
                    style: TextStyle(
                        fontSize: 11, color: Colors.orange),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

// ── Paso 5: Alergias ──────────────────────────────────────────────────────────

class _Step5Allergies extends StatelessWidget {
  const _Step5Allergies({
    required this.selectedAllergens,
    required this.customCtrl,
    required this.onAllergenChanged,
  });

  final Set<String> selectedAllergens;
  final TextEditingController customCtrl;
  final void Function(String, bool) onAllergenChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          '¿Tiene alergias o intolerancias?',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          'Selecciona todos los que apliquen. Puedes agregar más abajo.',
          style: theme.textTheme.bodySmall
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 16),

        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _allergens
              .map((a) => FilterChip(
                    label: Text(a, style: const TextStyle(fontSize: 12)),
                    selected: selectedAllergens.contains(a),
                    onSelected: (v) => onAllergenChanged(a, v),
                    selectedColor:
                        a == 'No conozco las alergias'
                            ? Colors.orange.shade100
                            : theme.colorScheme.primaryContainer,
                  ))
              .toList(),
        ),
        const SizedBox(height: 16),

        TextField(
          controller: customCtrl,
          decoration: const InputDecoration(
            labelText: 'Otras alergias (opcional)',
            hintText: 'Separadas por coma: arroz, pavo...',
            prefixIcon: Icon(Icons.add_circle_outline),
          ),
        ),
        const SizedBox(height: 12),

        if (selectedAllergens.isEmpty)
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withOpacity(0.3),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              children: [
                Icon(Icons.check_circle_outline, size: 16),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Si no hay alergias conocidas, puedes continuar sin seleccionar nada.',
                    style: TextStyle(fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

// ── Paso 6: Alimentación + Resumen ────────────────────────────────────────────

class _Step6Diet extends StatelessWidget {
  const _Step6Diet({
    required this.currentDiet,
    required this.onDietChanged,
    required this.petName,
    required this.species,
    required this.breed,
    required this.conditions,
  });

  final String currentDiet;
  final void Function(String) onDietChanged;
  final String petName;
  final String species;
  final String breed;
  final List<String> conditions;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(
          '¿Qué come actualmente?',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          'El agente usará esto para personalizar la transición dietaria.',
          style: theme.textTheme.bodySmall
              ?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 16),

        _DietCard(
          label: 'Concentrado / croquetas',
          subtitle: 'Alimento seco o húmedo comercial',
          icon: Icons.inventory_2_outlined,
          value: 'concentrado',
          selected: currentDiet == 'concentrado',
          onTap: () => onDietChanged('concentrado'),
        ),
        const SizedBox(height: 8),
        _DietCard(
          label: 'Dieta natural',
          subtitle: 'BARF, cocinado casero o mixto natural',
          icon: Icons.grass_outlined,
          value: 'natural',
          selected: currentDiet == 'natural',
          onTap: () => onDietChanged('natural'),
        ),
        const SizedBox(height: 8),
        _DietCard(
          label: 'Mixto',
          subtitle: 'Concentrado + alimentos naturales',
          icon: Icons.merge_outlined,
          value: 'mixto',
          selected: currentDiet == 'mixto',
          onTap: () => onDietChanged('mixto'),
        ),

        const SizedBox(height: 24),
        const Divider(),
        const SizedBox(height: 12),

        // Resumen
        Text(
          'Resumen del perfil',
          style: theme.textTheme.titleSmall
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _SummaryRow(
                    'Mascota',
                    petName.isNotEmpty ? petName : '—'),
                _SummaryRow('Especie',
                    species == 'perro' ? 'Canino 🐕' : 'Felino 🐈'),
                _SummaryRow('Raza', breed.isNotEmpty ? breed : '—'),
                _SummaryRow(
                  'Condiciones',
                  conditions.isEmpty
                      ? 'Ninguna — plan ACTIVO directo'
                      : '${conditions.length} — requiere revisión vet',
                  color: conditions.isEmpty ? Colors.green : Colors.orange,
                ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: theme.colorScheme.primaryContainer.withOpacity(0.3),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Text(
            'NutriVet.IA es asesoría nutricional digital — '
            'no reemplaza el diagnóstico médico veterinario.',
            style: TextStyle(fontSize: 11, fontStyle: FontStyle.italic),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow(this.label, this.value, {this.color});

  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(label,
                style: const TextStyle(fontSize: 12, color: Colors.grey)),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Widgets auxiliares ────────────────────────────────────────────────────────

class _SpeciesCard extends StatelessWidget {
  const _SpeciesCard({
    super.key,
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
      borderRadius: BorderRadius.circular(12),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          color: selected
              ? theme.colorScheme.primaryContainer
              : theme.colorScheme.surfaceContainerHighest,
          border: Border.all(
            color: selected
                ? theme.colorScheme.primary
                : Colors.transparent,
            width: 2,
          ),
        ),
        child: Column(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 36)),
            const SizedBox(height: 6),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: selected ? theme.colorScheme.primary : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

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
      borderRadius: BorderRadius.circular(10),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: selected
              ? theme.colorScheme.primaryContainer
              : theme.colorScheme.surfaceContainerHighest,
          border: Border.all(
            color: selected ? theme.colorScheme.primary : Colors.transparent,
            width: 2,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon,
                size: 18,
                color: selected ? theme.colorScheme.primary : null),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 13,
                color: selected ? theme.colorScheme.primary : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConditionTile extends StatelessWidget {
  const _ConditionTile({
    required this.label,
    required this.selected,
    required this.onToggle,
    this.isHealthy = false,
  });

  final String label;
  final bool selected;
  final void Function(bool) onToggle;
  final bool isHealthy;

  @override
  Widget build(BuildContext context) {
    return CheckboxListTile(
      value: selected,
      onChanged: (v) => onToggle(v ?? false),
      title: Text(label,
          style: TextStyle(
            fontWeight: FontWeight.w500,
            color: isHealthy ? Colors.green : null,
          )),
      secondary: isHealthy
          ? const Icon(Icons.check_circle, color: Colors.green)
          : null,
      controlAffinity: ListTileControlAffinity.leading,
    );
  }
}

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
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: selected
              ? theme.colorScheme.primaryContainer
              : theme.colorScheme.surfaceContainerHighest,
          border: Border.all(
            color: selected ? theme.colorScheme.primary : Colors.transparent,
            width: 2,
          ),
        ),
        child: Row(
          children: [
            Icon(icon,
                color: selected ? theme.colorScheme.primary : Colors.grey),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: selected
                            ? theme.colorScheme.primary
                            : null,
                      )),
                  Text(subtitle,
                      style: const TextStyle(
                          fontSize: 12, color: Colors.grey)),
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
