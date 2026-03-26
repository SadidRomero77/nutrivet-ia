/// Pantalla de soporte y ayuda.
library;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

class SupportScreen extends StatelessWidget {
  const SupportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Soporte y ayuda')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _SectionHeader('Contacto directo'),
          _ContactTile(
            icon: Icons.email_outlined,
            title: 'Email de soporte',
            subtitle: 'soporte@nutrivet.ia',
            onTap: () => _launchEmail('soporte@nutrivet.ia'),
          ),
          _ContactTile(
            icon: Icons.chat_bubble_outline,
            title: 'WhatsApp',
            subtitle: 'Respuesta en menos de 24 horas',
            onTap: () => _launchUrl('https://wa.me/573000000000'),
          ),
          const SizedBox(height: 24),
          _SectionHeader('Preguntas frecuentes'),
          _FaqTile(
            question: '¿Cómo funciona el plan nutricional?',
            answer: 'Ingresás los datos de tu mascota en el wizard (13 campos) '
                'y el agente de IA genera un plan personalizado basado en los '
                'estándares NRC/AAFCO. Si tu mascota tiene condición médica, '
                'el plan requiere revisión de un veterinario.',
          ),
          _FaqTile(
            question: '¿Cuándo llega la aprobación veterinaria?',
            answer: 'Los planes con condición médica son revisados en un plazo '
                'de 24-48 horas. Recibirás una notificación cuando el plan '
                'esté aprobado y listo para usar.',
          ),
          _FaqTile(
            question: '¿Puedo cancelar mi suscripción?',
            answer: 'Sí, podés cancelar en cualquier momento desde Configuración '
                '→ Suscripción. El acceso Premium se mantiene hasta el final '
                'del período pagado.',
          ),
          _FaqTile(
            question: '¿Los planes son seguros para mi mascota?',
            answer: 'Todos los planes incluyen verificación automática de '
                'toxicidad y restricciones médicas hard-coded. Los planes con '
                'condición médica requieren firma veterinaria antes de activarse. '
                'NutriVet.IA es asesoría nutricional digital — no reemplaza el '
                'diagnóstico médico veterinario.',
          ),
          const SizedBox(height: 24),
          _SectionHeader('Legal'),
          ListTile(
            leading: const Icon(Icons.description_outlined),
            title: const Text('Términos y condiciones'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/terms'),
          ),
          ListTile(
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Política de privacidad'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/terms?tab=privacy'),
          ),
          const SizedBox(height: 32),
          Center(
            child: Text(
              'NutriVet.IA v1.0.0\n'
              'Desarrollado con ❤ para BAMPYSVET',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _launchEmail(String email) async {
    final uri = Uri.parse('mailto:$email');
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: Theme.of(context)
            .textTheme
            .titleSmall
            ?.copyWith(fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _ContactTile extends StatelessWidget {
  const _ContactTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.open_in_new, size: 16),
        onTap: onTap,
      ),
    );
  }
}

class _FaqTile extends StatelessWidget {
  const _FaqTile({required this.question, required this.answer});

  final String question;
  final String answer;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        title: Text(question, style: const TextStyle(fontWeight: FontWeight.w500)),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
        children: [
          Text(
            answer,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Theme.of(context).colorScheme.outline,
                ),
          ),
        ],
      ),
    );
  }
}
