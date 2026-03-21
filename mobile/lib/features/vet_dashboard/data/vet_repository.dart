/// Repositorio de datos para el dashboard del veterinario.
/// Planes pendientes, pacientes ClinicPet.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
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

/// Pacientes del vet — cacheado para uso en el drawer y otras pantallas.
@riverpod
Future<List<PetModel>> vetPatients(Ref ref) =>
    ref.read(vetRepositoryProvider).listPatients();

class VetRepository {
  VetRepository({required this.dio});

  final Dio dio;
  static const _patientsBoxName = 'vet_patients';

  /// Lista planes PENDING_VET para revisión del vet.
  Future<List<VetPendingPlan>> listPendingPlans() async {
    final response = await dio.get<List<dynamic>>('/v1/vet/plans/pending');
    return (response.data!)
        .map((e) => VetPendingPlan.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Lista ClinicPets creados por el vet. Usa cache Hive si sin red.
  Future<List<PetModel>> listPatients() async {
    final box = await Hive.openBox<Map>(_patientsBoxName);
    try {
      final response = await dio.get<List<dynamic>>('/v1/vet/patients');
      final patients = (response.data!)
          .map((e) => PetModel.fromJson(e as Map<String, dynamic>))
          .toList();
      // Actualizar cache incluyendo campos de pacientes clínicos
      await box.clear();
      for (final p in patients) {
        await box.put(p.petId, {
          'pet_id': p.petId,
          'name': p.name,
          'species': p.species,
          'breed': p.breed,
          'sex': p.sex,
          'age_months': p.ageMonths,
          'weight_kg': p.weightKg,
          'size': p.size,
          'reproductive_status': p.reproductiveStatus,
          'activity_level': p.activityLevel,
          'bcs': p.bcs,
          'medical_conditions': p.medicalConditions,
          'allergies': p.allergies,
          'current_diet': p.currentFeedingType,
          'vet_id': p.vetId,
          'owner_name': p.ownerName,
          'owner_phone': p.ownerPhone,
          'claim_code': p.claimCode,
        });
      }
      return patients;
    } on DioException {
      // Fallback offline
      return box.values
          .map((e) => PetModel.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    }
  }

  /// Obtiene un paciente clínico por ID con datos del propietario y claim_code.
  Future<PetModel> getPatient(String petId) async {
    final response = await dio.get<Map<String, dynamic>>('/v1/vet/patients/$petId');
    return PetModel.fromJson(response.data!);
  }

  /// Elimina (soft-delete) un paciente clínico sin planes y sin vincular.
  /// Lanza Exception si tiene planes asignados o ya está vinculado.
  Future<void> deletePatient(String petId) async {
    try {
      await dio.delete<void>('/v1/vet/patients/$petId');
    } on DioException catch (e) {
      final data = e.response?.data;
      String msg = 'Error al eliminar el paciente.';
      if (data is Map) {
        final detail = data['detail'];
        if (detail is String) msg = detail;
      }
      throw Exception(msg);
    }
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
