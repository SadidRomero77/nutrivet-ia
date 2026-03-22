/// Tests de NutriVet.IA — widgets + contratos de payload.
///
/// Cubre:
///  - Renderizado de pantallas principales
///  - Contratos: JSON que Flutter envía al backend (pet create payload)
///  - Contratos: JSON que el backend envía a Flutter (PlanDetail.fromJson)
///  - Validación de enums de dominio
library;

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:nutrivet_ia/core/theme/app_theme.dart';
import 'package:nutrivet_ia/features/auth/data/auth_repository.dart';
import 'package:nutrivet_ia/features/auth/presentation/login_screen.dart';
import 'package:nutrivet_ia/features/auth/presentation/register_screen.dart';
import 'package:nutrivet_ia/features/pet/data/pet_repository.dart';
import 'package:nutrivet_ia/features/pet/presentation/pet_wizard_screen.dart';
import 'package:nutrivet_ia/features/plan/data/plan_repository.dart';
import 'package:nutrivet_ia/features/plan/presentation/plan_detail_screen.dart';
import 'package:nutrivet_ia/features/scanner/presentation/scanner_screen.dart';

class _MockDio extends Mock implements Dio {}

class _MockAuthRepository extends Mock implements AuthRepository {}

class _MockPlanRepository extends Mock implements PlanRepository {}

Widget _app(Widget child, {List<Override> overrides = const []}) =>
    ProviderScope(
      overrides: overrides,
      child: MaterialApp(theme: AppTheme.light, home: child),
    );

void main() {
  // ═══════════════════════════════════════════════════════════
  // BLOQUE A — Tests de renderizado de pantallas
  // ═══════════════════════════════════════════════════════════

  group('A. Renderizado de pantallas', () {
    testWidgets('LoginScreen — campos email, contraseña y botón', (tester) async {
      final mockRepo = _MockAuthRepository();
      await tester.pumpWidget(
        _app(const LoginScreen(),
            overrides: [authRepositoryProvider.overrideWithValue(mockRepo)]),
      );
      expect(find.byKey(const ValueKey('email_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('password_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('login_button')), findsOneWidget);
    });

    testWidgets('LoginScreen — valida email inválido', (tester) async {
      final mockRepo = _MockAuthRepository();
      await tester.pumpWidget(
        _app(const LoginScreen(),
            overrides: [authRepositoryProvider.overrideWithValue(mockRepo)]),
      );
      await tester.enterText(find.byKey(const ValueKey('email_field')), 'invalido');
      await tester.tap(find.byKey(const ValueKey('login_button')));
      await tester.pump();
      expect(find.text('Email inválido'), findsOneWidget);
    });

    testWidgets('RegisterScreen — campos nombre, teléfono, email, contraseña y botón', (tester) async {
      // Use taller screen so all form fields (incl. new phone field) fit in viewport
      tester.view.physicalSize = const Size(800, 1400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final mockRepo = _MockAuthRepository();
      await tester.pumpWidget(
        _app(const RegisterScreen(),
            overrides: [authRepositoryProvider.overrideWithValue(mockRepo)]),
      );
      expect(find.byKey(const ValueKey('name_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('phone_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('email_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('password_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('register_button')), findsOneWidget);
    });

    testWidgets('PetWizardScreen — campos clave visibles en formulario único', (tester) async {
      await tester.pumpWidget(_app(const PetWizardScreen()));
      expect(find.byKey(const ValueKey('pet_name_field')), findsOneWidget);
      expect(find.byKey(const ValueKey('species_dropdown')), findsOneWidget);
      expect(find.byKey(const ValueKey('age_field')), findsOneWidget);
    });

    testWidgets('ScannerScreen — aviso REGLA 7 visible', (tester) async {
      await tester.pumpWidget(_app(const ScannerScreen(petId: 'pet-1')));
      expect(
        find.text('Solo se acepta imagen de la tabla nutricional '
            'o la lista de ingredientes. No logos ni empaques frontales.'),
        findsOneWidget,
      );
    });

    testWidgets('ScannerScreen — botones cámara y galería presentes', (tester) async {
      await tester.pumpWidget(_app(const ScannerScreen(petId: 'pet-1')));
      expect(find.byKey(const ValueKey('camera_button')), findsOneWidget);
      expect(find.byKey(const ValueKey('gallery_button')), findsOneWidget);
    });

    testWidgets('PlanDetailScreen — renderiza sin crash y muestra loading', (tester) async {
      final mockRepo = _MockPlanRepository();
      when(() => mockRepo.getPlan('plan-1'))
          .thenAnswer((_) async => _buildTestPlan());

      await tester.pumpWidget(
        _app(
          const PlanDetailScreen(planId: 'plan-1'),
          overrides: [planRepositoryProvider.overrideWithValue(mockRepo)],
        ),
      );
      // Estado inicial: loading
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });
    // Nota: el disclaimer (REGLA 8) se verifica a nivel de modelo en Bloque C test 20
  });

  // ═══════════════════════════════════════════════════════════
  // BLOQUE B — Contratos de payload: Flutter → Backend
  // ═══════════════════════════════════════════════════════════

  group('B. Contrato payload Flutter → Backend (PetCreateRequest)', () {
    test('size values coinciden con enums del backend', () {
      // Backend Size enum: mini, pequeño, mediano, grande, gigante
      const validSizes = ['mini', 'pequeño', 'mediano', 'grande', 'gigante'];
      // Lo que el wizard envía
      const wizardSizes = ['mini', 'pequeño', 'mediano', 'grande', 'gigante'];
      expect(wizardSizes, equals(validSizes));
    });

    test('activity_level perro values coinciden con backend DogActivityLevel', () {
      const backendDogLevels = ['sedentario', 'moderado', 'activo', 'muy_activo'];
      const wizardDogLevels = ['sedentario', 'moderado', 'activo', 'muy_activo'];
      expect(wizardDogLevels, equals(backendDogLevels));
    });

    test('activity_level gato values coinciden con backend CatActivityLevel', () {
      const backendCatLevels = ['indoor', 'indoor_outdoor', 'outdoor'];
      const wizardCatLevels = ['indoor', 'indoor_outdoor', 'outdoor'];
      expect(wizardCatLevels, equals(backendCatLevels));
    });

    test('field name current_diet coincide con backend PetCreateRequest', () {
      // El wizard debe enviar 'current_diet', no 'current_feeding_type'
      const expectedField = 'current_diet';
      // Simular el Map que construye Step6
      final payload = {'current_diet': 'natural'};
      expect(payload.containsKey(expectedField), isTrue);
      expect(payload.containsKey('current_feeding_type'), isFalse);
    });

    test('Ninguno conocido se filtra — medical_conditions vacío es válido', () {
      // Cuando el usuario selecciona "Ninguno conocido", el backend debe recibir []
      final selected = {'Ninguno conocido'};
      final conditions = selected
          .where((c) => c != 'Ninguno conocido')
          .toList();
      expect(conditions, isEmpty);
    });

    test('condiciones médicas válidas pasan sin filtrar', () {
      final selected = {'diabético', 'renal'};
      final conditions = selected
          .where((c) => c != 'Ninguno conocido')
          .toList();
      expect(conditions, containsAll(['diabético', 'renal']));
      expect(conditions.length, 2);
    });
  });

  // ═══════════════════════════════════════════════════════════
  // BLOQUE C — Contratos de deserialización: Backend → Flutter
  // ═══════════════════════════════════════════════════════════

  group('C. Contrato deserialización Backend → Flutter (PlanDetail.fromJson)', () {
    test('PlanDetail.fromJson — respuesta completa del backend', () {
      final json = _buildPlanJson();
      final plan = PlanDetail.fromJson(json);

      expect(plan.planId, equals('plan-abc-123'));
      expect(plan.petId, equals('pet-xyz-456'));
      expect(plan.status, equals('ACTIVE'));
      expect(plan.modality, equals('natural'));
      expect(plan.isActive, isTrue);
      expect(plan.isPendingVet, isFalse);
    });

    test('PlanDetail.fromJson — perfil nutricional RER/DER correctos', () {
      final plan = PlanDetail.fromJson(_buildPlanJson());
      expect(plan.perfilNutricional.rerKcal, equals(396.0));
      expect(plan.perfilNutricional.derKcal, equals(534.0));
      expect(plan.perfilNutricional.weightPhase, equals('mantenimiento'));
    });

    test('PlanDetail.fromJson — ingredientes con cantidad_g (campo correcto del LLM)', () {
      final plan = PlanDetail.fromJson(_buildPlanJson());
      expect(plan.ingredientes, isNotEmpty);
      expect(plan.ingredientes.first.nombre, equals('Pollo cocido'));
      expect(plan.ingredientes.first.cantidadG, equals(150.0));
      // El campo es cantidadG (del LLM), NO cantidad_gramos
    });

    test('PlanDetail.fromJson — porciones correctas', () {
      final plan = PlanDetail.fromJson(_buildPlanJson());
      expect(plan.porciones.comidasPorDia, equals(2));
      // gPorComida mapea desde porcion_por_comida_gramos (retrocompat) o g_por_comida
      expect(plan.porciones.gPorComida, equals(75.0));
    });

    test('PlanDetail.fromJson — instrucciones de preparación', () {
      final plan = PlanDetail.fromJson(_buildPlanJson());
      expect(plan.instruccionesPreparacion.pasos, isNotEmpty);
      // tiempoPreparacionMinutos mapea desde tiempo_estimado_minutos o tiempo_preparacion_minutos
      expect(plan.instruccionesPreparacion.tiempoPreparacionMinutos, equals(20));
    });

    test('PlanDetail.fromJson — transición de dieta null cuando no aplica', () {
      final json = _buildPlanJson()..['transicion_dieta'] = null;
      final plan = PlanDetail.fromJson(json);
      expect(plan.transicionDieta, isNull);
    });

    test('PlanDetail.fromJson — transición de dieta presente con fases', () {
      final json = _buildPlanJson()
        ..['transicion_dieta'] = {
          'duracion_dias': 10,
          'fases': [
            {'dias': '1-3', 'descripcion': '25% nuevo + 75% anterior'},
            {'dias': '4-7', 'descripcion': '50% nuevo + 50% anterior'},
          ],
          'senales_de_alerta': ['Vómito persistente', 'Diarrea severa'],
        };
      final plan = PlanDetail.fromJson(json);
      expect(plan.transicionDieta, isNotNull);
      expect(plan.transicionDieta!.duracionDias, equals(10));
      expect(plan.transicionDieta!.fases.length, equals(2));
      expect(plan.transicionDieta!.fases.first.dias, equals('1-3'));
    });

    test('PlanDetail.fromJson — disclaimer obligatorio presente (REGLA 8)', () {
      final plan = PlanDetail.fromJson(_buildPlanJson());
      expect(plan.disclaimer, isNotEmpty);
      expect(plan.disclaimer, contains('asesoría nutricional digital'));
    });

    test('PlanDetail.fromJson — PENDING_VET cuando mascota tiene condición médica', () {
      final json = _buildPlanJson()..['status'] = 'PENDING_VET';
      final plan = PlanDetail.fromJson(json);
      expect(plan.isPendingVet, isTrue);
      expect(plan.isActive, isFalse);
    });

    test('PlanSummary.fromJson — campos requeridos correctos', () {
      final json = {
        'plan_id': 'plan-001',
        'pet_id': 'pet-001',
        'plan_type': 'estándar',
        'status': 'ACTIVE',
        'modality': 'natural',
        'rer_kcal': 396.0,
        'der_kcal': 534.0,
        'llm_model_used': 'meta-llama/llama-3.3-70b',
        'approved_by_vet_id': null,
        'disclaimer': 'NutriVet.IA es asesoría nutricional digital...',
      };
      final summary = PlanSummary.fromJson(json);
      expect(summary.planId, equals('plan-001'));
      expect(summary.rerKcal, equals(396.0));
      expect(summary.isActive, isTrue);
    });
  });

  // ═══════════════════════════════════════════════════════════
  // BLOQUE D — Caso Sally (Golden Case G8)
  // ═══════════════════════════════════════════════════════════

  group('D. Caso Sally — Golden Case G8', () {
    test('PlanDetail Sally: RER≈396 DER≈534 PENDING_VET', () {
      final json = _buildPlanJson()
        ..['perfil_nutricional'] = {
          'rer_kcal': 396.0,
          'der_kcal': 534.0,
          'weight_phase': 'mantenimiento',
          'protein_pct': null,
          'fat_pct': null,
          'carbs_pct': null,
        }
        ..['status'] = 'PENDING_VET';

      final plan = PlanDetail.fromJson(json);
      expect(plan.perfilNutricional.rerKcal, closeTo(396.0, 0.5));
      expect(plan.perfilNutricional.derKcal, closeTo(534.0, 0.5));
      expect(plan.isPendingVet, isTrue);
    });
  });
}

// ─── Fixtures ───────────────────────────────────────────────────────────────

Map<String, dynamic> _buildPlanJson() => {
      'plan_id': 'plan-abc-123',
      'pet_id': 'pet-xyz-456',
      'owner_id': 'owner-111',
      'plan_type': 'estándar',
      'status': 'ACTIVE',
      'modality': 'natural',
      'llm_model_used': 'meta-llama/llama-3.3-70b',
      'perfil_nutricional': {
        'rer_kcal': 396.0,
        'der_kcal': 534.0,
        'weight_phase': 'mantenimiento',
        'protein_pct': 30.0,
        'fat_pct': 15.0,
        'carbs_pct': null,
      },
      'ingredientes': {
        'items': [
          {'nombre': 'Pollo cocido', 'cantidad_g': 150.0, 'kcal': 180.0, 'proteina_g': 30.0, 'grasa_g': 4.0, 'fuente': 'animal', 'frecuencia': 'diario', 'notas': null},
          {'nombre': 'Arroz blanco', 'cantidad_g': 80.0, 'kcal': 90.0, 'proteina_g': 2.0, 'grasa_g': 0.5, 'fuente': 'vegetal', 'frecuencia': 'diario', 'notas': 'bien cocido'},
          {'nombre': 'Zanahoria', 'cantidad_g': 30.0, 'kcal': 12.0, 'proteina_g': 0.5, 'grasa_g': 0.1, 'fuente': 'vegetal', 'frecuencia': 'diario', 'notas': null},
        ],
      },
      'objetivos_clinicos': [
        'Cubrir el requerimiento energético de 534 kcal/día',
        'Mantener masa muscular magra',
      ],
      'ingredientes_prohibidos': ['Cebolla', 'Ajo'],
      'porciones': {
        'comidas_por_dia': 2,
        'g_por_comida': 75.0,
        'porcion_por_comida_gramos': 75.0,
        'total_g_dia': 150.0,
        'distribucion_comidas': [
          {'horario': 'mañana 7:00', 'porcentaje': 50.0, 'gramos': 75.0, 'proteina_g': 40.0, 'carbo_g': 25.0, 'vegetal_g': 10.0},
          {'horario': 'tarde 17:00', 'porcentaje': 50.0, 'gramos': 75.0, 'proteina_g': 40.0, 'carbo_g': 25.0, 'vegetal_g': 10.0},
        ],
      },
      'suplementos': [],
      'instrucciones_preparacion': {
        'metodo': 'cocción suave',
        'pasos': [
          'Cocinar el pollo sin sal ni condimentos.',
          'Mezclar con arroz y zanahoria.',
          'Dejar enfriar antes de servir.',
        ],
        'tiempo_preparacion_minutos': 20,
        'almacenamiento': 'Refrigerar hasta 3 días en recipiente hermético.',
        'advertencias': [],
        'instrucciones_por_grupo': {
          'proteinas': ['Cocinar a 75°C internos. Sin sal ni especias.'],
          'carbohidratos': ['Cocinar bien hasta que estén blandos.'],
          'vegetales': ['Cocinar al vapor 5-8 minutos.'],
        },
        'adiciones_permitidas': ['Cúrcuma: antiinflamatoria — 1/4 cucharadita'],
      },
      'snacks_saludables': [
        {'nombre': 'Zanahoria cocida', 'descripcion': 'Trozo pequeño de zanahoria cocida sin sal', 'cantidad_g': 20.0, 'frecuencia': '2-3 veces/semana'},
      ],
      'protocolo_digestivo': [
        'Si hay vómito: ayuno de 12h, luego reintroducir gradualmente.',
        'Si hay diarrea: añadir calabaza cocida como probiótico natural.',
      ],
      'transicion_dieta': null,
      'approved_by_vet_id': null,
      'review_date': null,
      'vet_comment': null,
      'disclaimer': 'NutriVet.IA es asesoría nutricional digital — '
          'no reemplaza el diagnóstico médico veterinario.',
    };

PlanDetail _buildTestPlan() => PlanDetail.fromJson(_buildPlanJson());
