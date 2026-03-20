/// Punto de entrada de NutriVet.IA.
///
/// - ProviderScope (Riverpod) en raíz.
/// - Hive inicializado antes del runApp.
/// - GoRouter como sistema de navegación.
/// - Tema claro/oscuro desde AppTheme.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

import 'core/router/app_router.dart';
import 'core/theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter();
  runApp(const ProviderScope(child: NutriVetApp()));
}

class NutriVetApp extends ConsumerWidget {
  const NutriVetApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'NutriVet.IA',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
