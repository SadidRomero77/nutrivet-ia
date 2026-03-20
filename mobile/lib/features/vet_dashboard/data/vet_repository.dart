/// Repositorio de datos para el dashboard del veterinario.
/// Planes pendientes, pacientes ClinicPet.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';
import '../../pet/data/pet_repository.dart';

part 'vet_repository.g.dart';

/// Plan pendiente de revisión en el dashboard del vet.
class VetPendingPlan {
  VetPendingPlan({
    required this.planId,
    required this.petId,
    required this.planType,
    required this.modality,
    required this.rerKcal,
    required this.derKcal,
    required this.llmModel,
    required this.createdAt,
  });

  factory VetPendingPlan.fromJson(Map<String, dynamic> json) => VetPendingPlan(
        planId: json['plan_id'] as String,
        petId: json['pet_id'] as String,
        planType: json['plan_type'] as String,
        modality: json['modality'] as String,
        rerKcal: (json['rer_kcal'] as num).toDouble(),
        derKcal: (json['der_kcal'] as num).toDouble(),
        llmModel: json['llm_model_used'] as String? ?? '',
        createdAt: DateTime.now(),
      );

  final String planId;
  final String petId;
  final String planType;
  final String modality;
  final double rerKcal;
  final double derKcal;
  final String llmModel;
  final DateTime createdAt;
}

@riverpod
VetRepository vetRepository(Ref ref) =>
    VetRepository(dio: ref.watch(apiClientProvider));

class VetRepository {
  VetRepository({required this.dio});

  final Dio dio;

  /// Lista planes PENDING_VET para revisión del vet.
  Future<List<VetPendingPlan>> listPendingPlans() async {
    final response = await dio.get<List<dynamic>>('/v1/vet/plans/pending');
    return (response.data!)
        .map((e) => VetPendingPlan.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Lista ClinicPets creados por el vet.
  Future<List<PetModel>> listPatients() async {
    final response = await dio.get<List<dynamic>>('/v1/vet/patients');
    return (response.data!)
        .map((e) => PetModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Obtiene un paciente clínico por ID (vet puede ver cualquier mascota).
  Future<PetModel> getPatient(String petId) async {
    final response = await dio.get<Map<String, dynamic>>('/v1/pets/$petId');
    return PetModel.fromJson(response.data!);
  }

  /// Aprueba un plan PENDING_VET.
  Future<void> approvePlan(String planId, {DateTime? reviewDate}) async {
    await dio.patch<Map<String, dynamic>>(
      '/v1/plans/$planId/approve',
      data: {
        if (reviewDate != null) 'review_date': reviewDate.toIso8601String(),
      },
    );
  }

  /// Devuelve un plan al owner con comentario.
  Future<void> returnPlan(String planId, String comment) async {
    await dio.patch<Map<String, dynamic>>(
      '/v1/plans/$planId/return',
      data: {'comment': comment},
    );
  }
}
