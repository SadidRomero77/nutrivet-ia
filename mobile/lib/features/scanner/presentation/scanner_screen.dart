/// Pantalla de escáner OCR — solo tabla nutricional o ingredientes.
///
/// REGLA 7: NUNCA imagen de marca, logo o empaque frontal.
library;

import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

import '../../../core/api/api_client.dart';

class ScannerScreen extends ConsumerStatefulWidget {
  const ScannerScreen({super.key, required this.petId});

  final String petId;

  @override
  ConsumerState<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends ConsumerState<ScannerScreen> {
  File? _image;
  bool _loading = false;
  Map<String, dynamic>? _result;
  String? _error;

  Future<void> _pickImage(ImageSource source) async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(
      source: source,
      maxWidth: 1920,
      maxHeight: 1920,
      imageQuality: 85,
    );
    if (picked == null) return;
    setState(() {
      _image = File(picked.path);
      _result = null;
      _error = null;
    });
  }

  Future<void> _analyze() async {
    if (_image == null) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final dio = ref.read(apiClientProvider);
      final formData = FormData.fromMap({
        'pet_id': widget.petId,
        'image': await MultipartFile.fromFile(
          _image!.path,
          filename: 'label.jpg',
        ),
      });
      final response = await dio.post<Map<String, dynamic>>(
        '/v1/scanner/analyze',
        data: formData,
      );
      setState(() => _result = response.data);
    } catch (e) {
      setState(() => _error = 'Error al analizar la imagen. Asegúrate de enviar solo tabla nutricional o lista de ingredientes.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Escáner nutricional')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Aviso REGLA 7
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.secondaryContainer,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              children: [
                Icon(Icons.info_outline, size: 18),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Solo se acepta imagen de la tabla nutricional '
                    'o la lista de ingredientes. No logos ni empaques frontales.',
                    style: TextStyle(fontSize: 13),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Preview de imagen
          if (_image != null)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(_image!, height: 220, fit: BoxFit.cover),
            )
          else
            Container(
              height: 220,
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.colorScheme.outline),
              ),
              child: const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.image_outlined, size: 48),
                    SizedBox(height: 8),
                    Text('Selecciona una imagen'),
                  ],
                ),
              ),
            ),

          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  key: const ValueKey('camera_button'),
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Cámara'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  key: const ValueKey('gallery_button'),
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Galería'),
                ),
              ),
            ],
          ),

          if (_image != null) ...[
            const SizedBox(height: 16),
            ElevatedButton.icon(
              key: const ValueKey('analyze_button'),
              onPressed: _loading ? null : _analyze,
              icon: _loading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.qr_code_scanner),
              label:
                  Text(_loading ? 'Analizando...' : 'Analizar etiqueta'),
            ),
          ],

          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],

          if (_result != null) ...[
            const SizedBox(height: 16),
            _ScanResult(result: _result!),
          ],
        ],
      ),
    );
  }
}

class _ScanResult extends StatelessWidget {
  const _ScanResult({required this.result});

  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final semaphore = result['semaphore'] as String? ?? 'amarillo';
    final color = switch (semaphore) {
      'verde' => Colors.green,
      'rojo' => Colors.red,
      _ => Colors.orange,
    };

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: color,
                  radius: 12,
                ),
                const SizedBox(width: 8),
                Text(
                  'Semáforo: $semaphore',
                  style: theme.textTheme.titleSmall?.copyWith(color: color),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (result['observations'] != null)
              Text(result['observations'] as String),
            if (result['toxic_ingredients'] != null &&
                (result['toxic_ingredients'] as List).isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Ingredientes problemáticos:',
                style: TextStyle(color: theme.colorScheme.error),
              ),
              for (final item in result['toxic_ingredients'] as List)
                Text('• $item', style: TextStyle(color: theme.colorScheme.error)),
            ],
          ],
        ),
      ),
    );
  }
}
