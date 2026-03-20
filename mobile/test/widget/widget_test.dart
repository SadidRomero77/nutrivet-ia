/// Tests de widgets NutriVet.IA — 7 casos clave.
///
/// Verifica que las pantallas principales renderizan correctamente
/// con providers mockeados.
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
import 'package:nutrivet_ia/features/plan/presentation/plan_detail_screen.dart';
import 'package:nutrivet_ia/features/plan/data/plan_repository.dart';
import 'package:nutrivet_ia/features/pet/presentation/pet_wizard_screen.dart';
import 'package:nutrivet_ia/features/scanner/presentation/scanner_screen.dart';

class _MockDio extends Mock implements Dio {}

class _MockAuthRepository extends Mock implements AuthRepository {}

class _MockPlanRepository extends Mock implements PlanRepository {}

/// Helper: construye un widget con ProviderScope y tema.
Widget _app(Widget child, {List<Override> overrides = const []}) =>
    ProviderScope(
      overrides: overrides,
      child: MaterialApp(
        theme: AppTheme.light,
        home: child,
      ),
    );

void main() {
  // ─── 1. LoginScreen renderiza campos de email y contraseña ──────────────
  testWidgets('LoginScreen — muestra campos email y contraseña', (tester) async {
    final mockRepo = _MockAuthRepository();
    await tester.pumpWidget(
      _app(
        const LoginScreen(),
        overrides: [
          authRepositoryProvider.overrideWithValue(mockRepo),
        ],
      ),
    );
    expect(find.byKey(const ValueKey('email_field')), findsOneWidget);
    expect(find.byKey(const ValueKey('password_field')), findsOneWidget);
    expect(find.byKey(const ValueKey('login_button')), findsOneWidget);
  });

  // ─── 2. LoginScreen valida email inválido ────────────────────────────────
  testWidgets('LoginScreen — valida email inválido', (tester) async {
    final mockRepo = _MockAuthRepository();
    await tester.pumpWidget(
      _app(
        const LoginScreen(),
        overrides: [authRepositoryProvider.overrideWithValue(mockRepo)],
      ),
    );
    // Ingresa email sin @
    await tester.enterText(
      find.byKey(const ValueKey('email_field')),
      'invalido',
    );
    await tester.tap(find.byKey(const ValueKey('login_button')));
    await tester.pump();
    expect(find.text('Email inválido'), findsOneWidget);
  });

  // ─── 3. RegisterScreen renderiza correctamente ───────────────────────────
  testWidgets('RegisterScreen — muestra campos de registro', (tester) async {
    final mockRepo = _MockAuthRepository();
    await tester.pumpWidget(
      _app(
        const RegisterScreen(),
        overrides: [authRepositoryProvider.overrideWithValue(mockRepo)],
      ),
    );
    expect(find.byKey(const ValueKey('name_field')), findsOneWidget);
    expect(find.byKey(const ValueKey('email_field')), findsOneWidget);
    expect(find.byKey(const ValueKey('password_field')), findsOneWidget);
    expect(find.byKey(const ValueKey('register_button')), findsOneWidget);
  });

  // ─── 4. PetWizardScreen — paso 1 visible ────────────────────────────────
  testWidgets('PetWizardScreen — primer paso muestra nombre y especie',
      (tester) async {
    await tester.pumpWidget(_app(const PetWizardScreen()));
    expect(find.byKey(const ValueKey('pet_name_field')), findsOneWidget);
    expect(find.byKey(const ValueKey('species_dropdown')), findsOneWidget);
    expect(find.byKey(const ValueKey('next_button')), findsOneWidget);
  });

  // ─── 5. PlanDetailScreen — disclaimer REGLA 8 visible ───────────────────
  testWidgets('PlanDetailScreen — disclaimer siempre visible', (tester) async {
    final mockRepo = _MockPlanRepository();
    final plan = PlanDetail.fromJson({
      'plan_id': 'abc-123',
      'status': 'ACTIVE',
      'rer_kcal': 396.0,
      'der_kcal': 534.0,
      'content': {
        'seccion_1_perfil': {'especie': 'perro'},
        'seccion_3_ingredientes': [],
        'seccion_5_sustitutos': [],
        'has_transition_protocol': false,
      },
    });
    when(() => mockRepo.getPlan('abc-123'))
        .thenAnswer((_) async => plan);

    await tester.pumpWidget(
      _app(
        const PlanDetailScreen(planId: 'abc-123'),
        overrides: [planRepositoryProvider.overrideWithValue(mockRepo)],
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    // Disclaimer visible (REGLA 8)
    expect(find.byKey(const ValueKey('disclaimer_banner')), findsOneWidget);
  });

  // ─── 6. ScannerScreen — aviso REGLA 7 visible ───────────────────────────
  testWidgets('ScannerScreen — muestra aviso de solo tabla nutricional',
      (tester) async {
    final mockDio = _MockDio();
    await tester.pumpWidget(
      _app(
        const ScannerScreen(petId: 'pet-1'),
        overrides: [
          // No necesitamos override de apiClientProvider para verificar el aviso
        ],
      ),
    );
    expect(find.text('Solo se acepta imagen de la tabla nutricional '
        'o la lista de ingredientes. No logos ni empaques frontales.'), findsOneWidget);
  });

  // ─── 7. ScannerScreen — botones de cámara y galería ─────────────────────
  testWidgets('ScannerScreen — botones cámara y galería presentes',
      (tester) async {
    await tester.pumpWidget(_app(const ScannerScreen(petId: 'pet-1')));
    expect(find.byKey(const ValueKey('camera_button')), findsOneWidget);
    expect(find.byKey(const ValueKey('gallery_button')), findsOneWidget);
  });
}
