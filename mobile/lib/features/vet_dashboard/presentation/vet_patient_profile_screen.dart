/// Pantalla de perfil de paciente clínico (vista veterinario).
///
/// Muestra datos completos del animal, datos de contacto del propietario,
/// y acceso directo a sus planes nutricionales.
library;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../../pet/data/pet_repository.dart';
import '../data/vet_repository.dart';

part 'vet_patient_profile_screen.g.dart';

@riverpod
Future<PetModel> _vetPatient(Ref ref, String petId) =>
    ref.read(vetRepositoryProvider).getPatient(petId);

class VetPatientProfileScreen extends ConsumerWidget {
  const VetPatientProfileScreen({super.key, required this.petId});

  final String petId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final petAsync = ref.watch(_vetPatientProvider(petId));

    return Scaffold(
      appBar: AppBar(
        title: petAsync.whenOrNull(data: (p) => NutrivetTitle(p.name)) ??
            const NutrivetTitle('Paciente clínico'),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome),
            tooltip: 'Generar plan',
            onPressed: petAsync.whenOrNull(
              data: (pet) => () => context.push(
                    '/plan/generate?petId=${pet.petId}&petName=${Uri.encodeComponent(pet.name)}',
                  ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: const AppFooter(),
      body: petAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (pet) => _PatientContent(pet: pet),
      ),
    );
  }
}

class _PatientContent extends StatelessWidget {
  const _PatientContent({required this.pet});

  final PetModel pet;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: Breakpoints.maxContentWidth),
        child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Avatar + nombre
        Center(
          child: Column(
            children: [
              CircleAvatar(
                radius: 40,
                backgroundColor: theme.colorScheme.primaryContainer,
                child: Text(
                  pet.species == 'perro' ? '🐕' : '🐈',
                  style: const TextStyle(fontSize: 40),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                pet.name,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                '${pet.breed} · ${pet.species}',
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
              Container(
                margin: const EdgeInsets.only(top: 6),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.blue.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'Paciente clínico',
                  style: TextStyle(fontSize: 12, color: Colors.blue),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Acciones rápidas
        Row(
          children: [
            _ActionBtn(
              icon: Icons.auto_awesome,
              label: 'Generar\nplan',
              color: Colors.deepPurple,
              onTap: () => context.push(
                '/plan/generate?petId=${pet.petId}&petName=${Uri.encodeComponent(pet.name)}',
              ),
            ),
            const SizedBox(width: 8),
            _ActionBtn(
              icon: Icons.list_alt,
              label: 'Ver\nplanes',
              color: Colors.blue,
              onTap: () => context.push('/plans?petId=${pet.petId}'),
            ),
            const SizedBox(width: 8),
            _ActionBtn(
              icon: Icons.chat_bubble_outline,
              label: 'Consultar',
              color: Colors.green,
              onTap: () => context.push('/chat?petId=${pet.petId}'),
            ),
          ],
        ),
        const SizedBox(height: 24),

        // Datos básicos
        _InfoCard(
          title: 'Datos básicos',
          rows: [
            _InfoRow('Especie', pet.species),
            _InfoRow('Raza', pet.breed),
            _InfoRow('Sexo', pet.sex),
            _InfoRow('Edad', '${pet.ageMonths} meses'),
            if (pet.size != null) _InfoRow('Talla', pet.size!),
          ],
        ),

        // Condición física
        _InfoCard(
          title: 'Condición física',
          rows: [
            _InfoRow('Peso', '${pet.weightKg} kg'),
            _InfoRow('BCS', '${pet.bcs} / 9 · ${_bcsLabel(pet.bcs)}'),
            _InfoRow('Estado reproductivo', pet.reproductiveStatus),
            _InfoRow('Nivel de actividad', pet.activityLevel),
          ],
        ),

        // Salud — sección importante para el vet
        _InfoCard(
          title: 'Salud',
          titleColor: pet.medicalConditions.isNotEmpty ? Colors.orange : null,
          rows: [
            _InfoRow(
              'Condiciones médicas',
              pet.medicalConditions.isEmpty
                  ? 'Ninguna conocida'
                  : pet.medicalConditions.join(', '),
              valueColor:
                  pet.medicalConditions.isNotEmpty ? Colors.orange : null,
            ),
            _InfoRow(
              'Alergias',
              pet.allergies.isEmpty
                  ? 'Ninguna conocida'
                  : pet.allergies.join(', '),
            ),
          ],
        ),

        // Alimentación
        _InfoCard(
          title: 'Alimentación actual',
          rows: [_InfoRow('Tipo', pet.currentFeedingType)],
        ),

        // Propietario (solo si el vet capturó los datos)
        if (pet.ownerName != null || pet.ownerPhone != null)
          _InfoCard(
            title: 'Propietario',
            rows: [
              if (pet.ownerName != null) _InfoRow('Nombre', pet.ownerName!),
              if (pet.ownerPhone != null) _InfoRow('Teléfono', pet.ownerPhone!),
            ],
          ),

        // Código de vinculación (solo si el paciente aún no fue reclamado)
        if (pet.claimCode != null) _ClaimCodeCard(code: pet.claimCode!),
      ],
    ),
      ),
    );
  }

  String _bcsLabel(int bcs) {
    if (bcs <= 3) return 'Bajo peso';
    if (bcs >= 7) return 'Sobrepeso';
    return 'Peso ideal';
  }
}

class _ActionBtn extends StatelessWidget {
  const _ActionBtn({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Column(
            children: [
              Icon(icon, color: color, size: 22),
              const SizedBox(height: 4),
              Text(
                label,
                style: TextStyle(fontSize: 10, color: color),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({
    required this.title,
    required this.rows,
    this.titleColor,
  });

  final String title;
  final List<_InfoRow> rows;
  final Color? titleColor;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: titleColor,
                  ),
            ),
            const SizedBox(height: 8),
            ...rows,
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value, {this.valueColor});

  final String label;
  final String value;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: const TextStyle(color: Colors.black54, fontSize: 13),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 13,
                color: valueColor,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Tarjeta de código de vinculación ─────────────────────────────────────────

class _ClaimCodeCard extends StatelessWidget {
  const _ClaimCodeCard({required this.code});

  final String code;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      color: theme.colorScheme.tertiaryContainer.withAlpha(80),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.link, color: theme.colorScheme.tertiary, size: 18),
                const SizedBox(width: 8),
                Text(
                  'Código de vinculación',
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.tertiary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              'Este paciente aún no ha sido reclamado por su propietario.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        vertical: 12, horizontal: 16),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surface,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                          color: theme.colorScheme.tertiaryContainer),
                    ),
                    child: Text(
                      code,
                      style: theme.textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        letterSpacing: 6,
                        color: theme.colorScheme.tertiary,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: theme.colorScheme.tertiary,
                    foregroundColor: Colors.white,
                  ),
                  icon: const Icon(Icons.copy, size: 20),
                  tooltip: 'Copiar código',
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: code));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Código copiado al portapapeles'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Comparte este código con el propietario para que lo ingrese '
              'en "Vincular mascota clínica" en la app.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
