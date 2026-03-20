/// Pantalla de perfil completo de una mascota.
/// Muestra los 13 campos, acciones rápidas y opción de eliminar.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/utils/responsive.dart';
import '../../../core/widgets/app_footer.dart';
import '../data/pet_repository.dart';
import 'dashboard_screen.dart';

part 'pet_profile_screen.g.dart';

@riverpod
Future<PetModel> _petDetail(Ref ref, String petId) async {
  final pets = await ref.read(petRepositoryProvider).listPets();
  return pets.firstWhere(
    (p) => p.petId == petId,
    orElse: () => throw Exception('Mascota no encontrada'),
  );
}

class PetProfileScreen extends ConsumerWidget {
  const PetProfileScreen({super.key, required this.petId});

  final String petId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final petAsync = ref.watch(_petDetailProvider(petId));

    return Scaffold(
      appBar: AppBar(
        title: petAsync.whenOrNull(data: (p) => Text(p.name)) ??
            const Text('Perfil de mascota'),
        actions: [
          petAsync.whenOrNull(
            data: (pet) => IconButton(
              icon: const Icon(Icons.edit),
              tooltip: 'Editar',
              onPressed: () async {
                await context.push('/pet/$petId/edit');
                ref.invalidate(_petDetailProvider(petId));
              },
            ),
          ) ??
              const SizedBox.shrink(),
        ],
      ),
      body: petAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (pet) => _PetProfileContent(
          pet: pet,
          onDelete: () => _confirmDelete(context, ref, pet),
        ),
      ),
    );
  }

  Future<void> _confirmDelete(
    BuildContext context,
    WidgetRef ref,
    PetModel pet,
  ) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Eliminar mascota'),
        content: Text(
          '¿Estás seguro de que deseas eliminar a ${pet.name}?\n\n'
          'Esta acción no se puede deshacer. Solo es posible si '
          'la mascota no tiene planes activos.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          TextButton(
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
            ),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );

    if (confirmed != true || !context.mounted) return;

    try {
      await ref.read(petRepositoryProvider).deletePet(pet.petId);
      ref.invalidate(petsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${pet.name} eliminada correctamente')),
        );
        context.go('/dashboard');
      }
    } on Exception catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceAll('Exception: ', ''))),
        );
      }
    }
  }
}

class _PetProfileContent extends StatelessWidget {
  const _PetProfileContent({required this.pet, required this.onDelete});

  final PetModel pet;
  final VoidCallback onDelete;

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
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Acciones rápidas
        Row(
          children: [
            _ActionButton(
              icon: Icons.auto_awesome,
              label: 'Generar plan',
              color: Colors.deepPurple,
              onTap: () => context.push(
                '/plan/generate?petId=${pet.petId}&petName=${Uri.encodeComponent(pet.name)}',
              ),
            ),
            const SizedBox(width: 8),
            _ActionButton(
              icon: Icons.list_alt,
              label: 'Ver planes',
              color: Colors.blue,
              onTap: () => context.push('/plans?petId=${pet.petId}'),
            ),
            const SizedBox(width: 8),
            _ActionButton(
              icon: Icons.chat_bubble_outline,
              label: 'Consultar',
              color: Colors.green,
              onTap: () => context.push('/chat?petId=${pet.petId}'),
            ),
            const SizedBox(width: 8),
            _ActionButton(
              icon: Icons.qr_code_scanner,
              label: 'Scanner',
              color: Colors.orange,
              onTap: () => context.push('/scanner?petId=${pet.petId}'),
            ),
          ],
        ),
        const SizedBox(height: 24),

        // Datos del perfil
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
        _InfoCard(
          title: 'Condición física',
          rows: [
            _InfoRow('Peso', '${pet.weightKg} kg'),
            _InfoRow('BCS', '${pet.bcs} / 9 · ${_bcsLabel(pet.bcs)}'),
            _InfoRow('Estado reproductivo', pet.reproductiveStatus),
            _InfoRow('Nivel de actividad', pet.activityLevel),
          ],
        ),
        _InfoCard(
          title: 'Salud',
          rows: [
            _InfoRow(
              'Condiciones médicas',
              pet.medicalConditions.isEmpty
                  ? 'Ninguna conocida'
                  : pet.medicalConditions.join(', '),
            ),
            _InfoRow(
              'Alergias',
              pet.allergies.isEmpty ? 'Ninguna conocida' : pet.allergies.join(', '),
            ),
          ],
        ),
        _InfoCard(
          title: 'Alimentación actual',
          rows: [_InfoRow('Tipo', pet.currentFeedingType)],
        ),

        const SizedBox(height: 24),

        // Botón eliminar
        OutlinedButton.icon(
          style: OutlinedButton.styleFrom(
            foregroundColor: theme.colorScheme.error,
            side: BorderSide(color: theme.colorScheme.error),
          ),
          onPressed: onDelete,
          icon: const Icon(Icons.delete_outline),
          label: const Text('Eliminar mascota'),
        ),
        const AppFooter(),
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

class _ActionButton extends StatelessWidget {
  const _ActionButton({
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
  const _InfoCard({required this.title, required this.rows});

  final String title;
  final List<_InfoRow> rows;

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
              style: Theme.of(context)
                  .textTheme
                  .titleSmall
                  ?.copyWith(fontWeight: FontWeight.bold),
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
  const _InfoRow(this.label, this.value);

  final String label;
  final String value;

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
              style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
            ),
          ),
        ],
      ),
    );
  }
}
