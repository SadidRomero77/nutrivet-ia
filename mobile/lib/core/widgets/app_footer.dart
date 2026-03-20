/// Footer de la aplicación — créditos y derechos.
library;

import 'package:flutter/material.dart';

class AppFooter extends StatelessWidget {
  const AppFooter({super.key, this.topPadding = 24});

  final double topPadding;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: EdgeInsets.fromLTRB(16, topPadding, 16, 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Divider(color: theme.colorScheme.outlineVariant),
          const SizedBox(height: 8),
          Text(
            'Desarrollada por Sadid Romero',
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            '© ${DateTime.now().year} BampysVet · Todos los derechos reservados',
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
    );
  }
}
