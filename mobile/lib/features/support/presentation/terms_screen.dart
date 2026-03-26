/// Pantalla de términos y condiciones / política de privacidad.
library;

import 'package:flutter/material.dart';

class TermsScreen extends StatefulWidget {
  const TermsScreen({super.key, this.initialTab});

  /// 'terms' (default) o 'privacy'
  final String? initialTab;

  @override
  State<TermsScreen> createState() => _TermsScreenState();
}

class _TermsScreenState extends State<TermsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(
      length: 2,
      vsync: this,
      initialIndex: widget.initialTab == 'privacy' ? 1 : 0,
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Legal'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Términos y condiciones'),
            Tab(text: 'Privacidad'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _LegalContent(
            title: 'Términos y Condiciones',
            sections: const [
              _LegalSection(
                heading: '1. Aceptación',
                body:
                    'Al usar NutriVet.IA, aceptás estos términos. Si no estás de acuerdo, '
                    'no utilices el servicio.',
              ),
              _LegalSection(
                heading: '2. Naturaleza del servicio',
                body:
                    'NutriVet.IA es una herramienta de asesoría nutricional digital para mascotas. '
                    'NO reemplaza el diagnóstico, tratamiento, ni la consulta médica veterinaria. '
                    'Para mascotas con condiciones médicas, los planes requieren revisión y '
                    'aprobación de un médico veterinario habilitado.',
              ),
              _LegalSection(
                heading: '3. Limitación de responsabilidad',
                body:
                    'NutriVet.IA y sus desarrolladores no se hacen responsables de daños '
                    'derivados del uso de los planes nutricionales sin supervisión veterinaria '
                    'adecuada. El usuario asume la responsabilidad de consultar con un profesional '
                    'ante cualquier duda sobre la salud de su mascota.',
              ),
              _LegalSection(
                heading: '4. Suscripciones',
                body:
                    'Los planes de suscripción se cobran mensualmente. Podés cancelar en cualquier '
                    'momento. No hay reembolsos por períodos parciales. Los precios pueden cambiar '
                    'con 30 días de aviso.',
              ),
              _LegalSection(
                heading: '5. Propiedad intelectual',
                body:
                    'Todo el contenido generado por NutriVet.IA es propiedad de sus creadores. '
                    'Los planes nutricionales generados son para uso personal del usuario y no '
                    'pueden ser redistribuidos comercialmente.',
              ),
              _LegalSection(
                heading: '6. Modificaciones',
                body:
                    'Nos reservamos el derecho de modificar estos términos. Los cambios '
                    'significativos serán notificados con al menos 15 días de anticipación.',
              ),
            ],
          ),
          _LegalContent(
            title: 'Política de Privacidad',
            sections: const [
              _LegalSection(
                heading: '1. Datos que recopilamos',
                body:
                    'Recopilamos: email, nombre, datos del perfil de tu mascota (especie, raza, '
                    'edad, peso, condiciones médicas), historial de planes, y conversaciones con '
                    'el agente. Los datos médicos se almacenan cifrados con AES-256.',
              ),
              _LegalSection(
                heading: '2. Cómo usamos tus datos',
                body:
                    'Usamos tus datos para: generar planes nutricionales personalizados, mejorar '
                    'el servicio, y permitir la revisión veterinaria cuando aplique. Nunca vendemos '
                    'tus datos a terceros.',
              ),
              _LegalSection(
                heading: '3. Datos enviados a IA',
                body:
                    'Los prompts enviados a modelos de IA externos usan únicamente IDs anónimos. '
                    'Nunca se envían nombres, especies, condiciones médicas en texto plano a '
                    'proveedores externos.',
              ),
              _LegalSection(
                heading: '4. Retención de datos',
                body:
                    'Conservamos tus datos mientras tengas una cuenta activa. Al eliminar tu '
                    'cuenta, los datos se eliminan en un plazo máximo de 30 días, excepto los '
                    'registros requeridos por ley.',
              ),
              _LegalSection(
                heading: '5. Tus derechos',
                body:
                    'Tenés derecho a acceder, corregir, y eliminar tus datos. Para ejercer estos '
                    'derechos, contactá a soporte@nutrivet.ia.',
              ),
              _LegalSection(
                heading: '6. Cookies y analytics',
                body:
                    'Usamos analytics anónimos para mejorar el servicio. No usamos cookies de '
                    'rastreo ni compartimos datos de uso con terceros.',
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _LegalContent extends StatelessWidget {
  const _LegalContent({required this.title, required this.sections});

  final String title;
  final List<_LegalSection> sections;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text(
          title,
          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          'Última actualización: enero 2026',
          style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.outline),
        ),
        const SizedBox(height: 16),
        ...sections,
        const SizedBox(height: 32),
      ],
    );
  }
}

class _LegalSection extends StatelessWidget {
  const _LegalSection({required this.heading, required this.body});

  final String heading;
  final String body;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            heading,
            style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            body,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.onSurface.withOpacity(0.8),
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}
