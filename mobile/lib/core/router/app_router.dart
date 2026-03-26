/// Router principal de NutriVet.IA usando GoRouter.
///
/// Rutas protegidas: redirige a /login si no hay token.
/// Ruta raíz: /dashboard (owner) o /vet/dashboard (vet).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../features/agent/presentation/chat_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/pet/presentation/pet_wizard_screen.dart';
import '../../features/pet/presentation/pet_profile_screen.dart';
import '../../features/pet/presentation/edit_pet_screen.dart';
import '../../features/pet/presentation/dashboard_screen.dart';
import '../../features/plan/presentation/plan_detail_screen.dart';
import '../../features/plan/presentation/plan_list_screen.dart';
import '../../features/scanner/presentation/scanner_screen.dart';
import '../../features/vet_dashboard/presentation/vet_dashboard_screen.dart';
import '../../features/vet_dashboard/presentation/vet_patient_profile_screen.dart';
import '../../features/vet_dashboard/presentation/vet_review_plan_screen.dart';
import '../../features/vet_dashboard/presentation/create_clinic_patient_screen.dart';
import '../../features/pet/presentation/claim_pet_screen.dart';
import '../../features/auth/presentation/change_password_screen.dart';
import '../../features/auth/presentation/edit_profile_screen.dart';
import '../../features/auth/presentation/profile_screen.dart';
import '../../features/subscription/presentation/subscription_screen.dart';
import '../storage/secure_storage.dart';

part 'app_router.g.dart';

@riverpod
GoRouter appRouter(Ref ref) {
  final storage = ref.watch(secureStorageProvider);

  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) async {
      final hasTokens = await storage.hasTokens();
      final loc = state.matchedLocation;
      final isAuthRoute = loc == '/login' ||
          loc == '/register' ||
          loc == '/splash';

      if (!hasTokens && !isAuthRoute) return '/login';

      final role = await storage.readRole();

      if (hasTokens && isAuthRoute) {
        return role == 'vet' ? '/vet/dashboard' : '/dashboard';
      }

      // Guards de rol: evita que owner acceda a rutas de vet y viceversa
      if (hasTokens && role != null) {
        final isVetRoute = loc.startsWith('/vet/');
        final isOwnerOnlyRoute = loc == '/dashboard' ||
            loc == '/pet/new' ||
            loc == '/pets/claim' ||
            loc.startsWith('/pet/');

        if (isVetRoute && role != 'vet') return '/dashboard';
        if (isOwnerOnlyRoute && role == 'vet') return '/vet/dashboard';
      }

      return null;
    },
    routes: [
      GoRoute(
        path: '/splash',
        builder: (_, __) => const _SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (_, __) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (_, __) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (_, __) => const DashboardScreen(),
      ),
      GoRoute(
        path: '/pet/new',
        builder: (_, __) => const PetWizardScreen(),
      ),
      GoRoute(
        path: '/pet/:petId',
        builder: (_, state) =>
            PetProfileScreen(petId: state.pathParameters['petId']!),
      ),
      GoRoute(
        path: '/pet/:petId/edit',
        builder: (_, state) =>
            EditPetScreen(petId: state.pathParameters['petId']!),
      ),
      GoRoute(
        path: '/plan/generate',
        builder: (_, state) => GeneratePlanScreen(
          petId: state.uri.queryParameters['petId'] ?? '',
          petName: state.uri.queryParameters['petName'] ?? 'Mascota',
        ),
      ),
      GoRoute(
        path: '/plans',
        builder: (_, state) =>
            PlanListScreen(petId: state.uri.queryParameters['petId'] ?? ''),
      ),
      GoRoute(
        path: '/plan/:planId',
        builder: (_, state) =>
            PlanDetailScreen(planId: state.pathParameters['planId']!),
      ),
      GoRoute(
        path: '/chat',
        builder: (_, state) {
          final petId = state.uri.queryParameters['petId'] ?? '';
          return ChatScreen(petId: petId);
        },
      ),
      GoRoute(
        path: '/scanner',
        builder: (_, state) {
          final petId = state.uri.queryParameters['petId'] ?? '';
          return ScannerScreen(petId: petId);
        },
      ),
      GoRoute(
        path: '/pets/claim',
        builder: (_, __) => const ClaimPetScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (_, __) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/profile/edit',
        builder: (_, __) => const EditProfileScreen(),
      ),
      GoRoute(
        path: '/profile/change-password',
        builder: (_, __) => const ChangePasswordScreen(),
      ),
      GoRoute(
        path: '/subscription',
        builder: (_, __) => const SubscriptionScreen(),
      ),
      GoRoute(
        path: '/vet/dashboard',
        builder: (_, __) => const VetDashboardScreen(),
      ),
      GoRoute(
        path: '/vet/patient/:petId',
        builder: (_, state) =>
            VetPatientProfileScreen(petId: state.pathParameters['petId']!),
      ),
      GoRoute(
        path: '/vet/patients/new',
        builder: (_, __) => const CreateClinicPatientScreen(),
      ),
      GoRoute(
        path: '/vet/plan/:planId',
        builder: (_, state) =>
            VetReviewPlanScreen(planId: state.pathParameters['planId']!),
      ),
    ],
    errorBuilder: (context, state) => Scaffold(
      body: Center(child: Text('Ruta no encontrada: ${state.uri}')),
    ),
  );
}

/// Pantalla de splash — verifica tokens y navega programáticamente.
class _SplashScreen extends ConsumerStatefulWidget {
  const _SplashScreen();

  @override
  ConsumerState<_SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<_SplashScreen> {
  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final storage = ref.read(secureStorageProvider);
    bool hasTokens = false;
    try {
      hasTokens = await storage.hasTokens().timeout(
        const Duration(seconds: 3),
        onTimeout: () => false,
      );
    } catch (_) {
      hasTokens = false;
    }
    if (mounted) {
      if (!hasTokens) {
        context.go('/login');
      } else {
        final storage = ref.read(secureStorageProvider);
        final role = await storage.readRole();
        if (mounted) {
          context.go(role == 'vet' ? '/vet/dashboard' : '/dashboard');
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) => const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
}
