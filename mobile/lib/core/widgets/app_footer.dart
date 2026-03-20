/// Footer de la aplicación — créditos y derechos.
/// Diseñado para usarse como [Scaffold.bottomNavigationBar].
library;

import 'package:flutter/material.dart';

/// Footer estático de NutriVet.IA.
///
/// Usar como [Scaffold.bottomNavigationBar] para que aparezca fijado
/// al fondo de la pantalla con SafeArea automático.
class AppFooter extends StatelessWidget {
  const AppFooter({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SafeArea(
      top: false,
      child: Container(
        color: theme.colorScheme.primaryContainer,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'NutriVet.IA',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onPrimaryContainer,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Desarrollada por Sadid Romero',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onPrimaryContainer.withAlpha(180),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              '© ${DateTime.now().year} BampysVet · Todos los derechos reservados',
              style: theme.textTheme.labelSmall?.copyWith(
                color: theme.colorScheme.onPrimaryContainer.withAlpha(160),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// AppBar title que siempre muestra "NutriVet.IA" como branding
/// con el nombre de la pantalla como subtítulo.
class NutrivetTitle extends StatelessWidget {
  const NutrivetTitle(this.screenTitle, {super.key});
  final String screenTitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Text(
          'NutriVet.IA',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 16,
            color: Colors.white,
            letterSpacing: 0.5,
          ),
        ),
        Text(
          screenTitle,
          style: const TextStyle(
            fontSize: 11,
            color: Colors.white70,
            fontWeight: FontWeight.normal,
          ),
        ),
      ],
    );
  }
}
