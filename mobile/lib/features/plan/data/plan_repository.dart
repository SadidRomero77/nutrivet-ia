/// Repositorio de planes nutricionales — lectura y exportación a PDF.
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/api/api_client.dart';

part 'plan_repository.g.dart';

// ---------------------------------------------------------------------------
// Modelos — reflejan exactamente PlanResponse / PlanSummaryResponse del backend
// ---------------------------------------------------------------------------

class PerfilNutricional {
  PerfilNutricional({
    required this.rerKcal,
    required this.derKcal,
    required this.weightPhase,
    this.proteinPct,
    this.fatPct,
    this.carbsPct,
  });

  factory PerfilNutricional.fromJson(Map<String, dynamic> json) =>
      PerfilNutricional(
        rerKcal: (json['rer_kcal'] as num).toDouble(),
        derKcal: (json['der_kcal'] as num).toDouble(),
        weightPhase: json['weight_phase'] as String,
        proteinPct: (json['protein_pct'] as num?)?.toDouble(),
        fatPct: (json['fat_pct'] as num?)?.toDouble(),
        carbsPct: (json['carbs_pct'] as num?)?.toDouble(),
      );

  final double rerKcal;
  final double derKcal;
  final String weightPhase;
  final double? proteinPct;
  final double? fatPct;
  final double? carbsPct;
}

class IngredientItem {
  IngredientItem({
    required this.nombre,
    this.cantidadGramos,
    this.notas,
  });

  factory IngredientItem.fromJson(Map<String, dynamic> json) => IngredientItem(
        nombre: json['nombre'] as String,
        cantidadGramos: (json['cantidad_gramos'] as num?)?.toDouble(),
        notas: json['notas'] as String?,
      );

  final String nombre;
  final double? cantidadGramos;
  final String? notas;
}

class Porciones {
  Porciones({
    required this.comidasPorDia,
    this.porcionPorComidaGramos,
    this.notas,
  });

  factory Porciones.fromJson(Map<String, dynamic> json) => Porciones(
        comidasPorDia: (json['comidas_por_dia'] as num).toInt(),
        porcionPorComidaGramos:
            (json['porcion_por_comida_gramos'] as num?)?.toDouble(),
        notas: json['notas'] as String?,
      );

  final int comidasPorDia;
  final double? porcionPorComidaGramos;
  final String? notas;
}

class InstruccionesPreparacion {
  InstruccionesPreparacion({
    required this.pasos,
    this.tiempoEstimadoMinutos,
    this.notas,
  });

  factory InstruccionesPreparacion.fromJson(Map<String, dynamic> json) =>
      InstruccionesPreparacion(
        pasos: List<String>.from(json['pasos'] as List? ?? []),
        tiempoEstimadoMinutos:
            (json['tiempo_estimado_minutos'] as num?)?.toInt(),
        notas: json['notas'] as String?,
      );

  final List<String> pasos;
  final int? tiempoEstimadoMinutos;
  final String? notas;
}

class TransicionDieta {
  TransicionDieta({
    required this.duracionDias,
    required this.semana1PctNuevo,
    required this.semana2PctNuevo,
    required this.semana3PctNuevo,
    required this.semana4PctNuevo,
    this.notas,
  });

  factory TransicionDieta.fromJson(Map<String, dynamic> json) =>
      TransicionDieta(
        duracionDias: (json['duracion_dias'] as num).toInt(),
        semana1PctNuevo: (json['semana_1_pct_nuevo'] as num).toInt(),
        semana2PctNuevo: (json['semana_2_pct_nuevo'] as num).toInt(),
        semana3PctNuevo: (json['semana_3_pct_nuevo'] as num).toInt(),
        semana4PctNuevo: (json['semana_4_pct_nuevo'] as num).toInt(),
        notas: json['notas'] as String?,
      );

  final int duracionDias;
  final int semana1PctNuevo;
  final int semana2PctNuevo;
  final int semana3PctNuevo;
  final int semana4PctNuevo;
  final String? notas;
}

/// Modelo detallado de plan — refleja PlanResponse del backend (ADR-020).
class PlanDetail {
  PlanDetail({
    required this.planId,
    required this.petId,
    required this.status,
    required this.modality,
    required this.llmModelUsed,
    required this.perfilNutricional,
    required this.ingredientes,
    required this.porciones,
    required this.instruccionesPreparacion,
    required this.disclaimer,
    this.transicionDieta,
    this.vetComment,
    this.reviewDate,
  });

  factory PlanDetail.fromJson(Map<String, dynamic> json) => PlanDetail(
        planId: json['plan_id'] as String,
        petId: json['pet_id'] as String,
        status: json['status'] as String,
        modality: json['modality'] as String,
        llmModelUsed: json['llm_model_used'] as String,
        perfilNutricional: PerfilNutricional.fromJson(
          json['perfil_nutricional'] as Map<String, dynamic>,
        ),
        ingredientes: ((json['ingredientes'] as Map<String, dynamic>?)?['items']
                    as List? ??
                [])
            .map((e) => IngredientItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        porciones: Porciones.fromJson(
          json['porciones'] as Map<String, dynamic>? ?? {},
        ),
        instruccionesPreparacion: InstruccionesPreparacion.fromJson(
          json['instrucciones_preparacion'] as Map<String, dynamic>? ?? {},
        ),
        transicionDieta: json['transicion_dieta'] != null
            ? TransicionDieta.fromJson(
                json['transicion_dieta'] as Map<String, dynamic>,
              )
            : null,
        vetComment: json['vet_comment'] as String?,
        reviewDate: json['review_date'] != null
            ? DateTime.parse(json['review_date'] as String)
            : null,
        disclaimer: json['disclaimer'] as String? ??
            'NutriVet.IA es asesoría nutricional digital — '
                'no reemplaza el diagnóstico médico veterinario.',
      );

  final String planId;
  final String petId;
  final String status;
  final String modality;
  final String llmModelUsed;
  final PerfilNutricional perfilNutricional;
  final List<IngredientItem> ingredientes;
  final Porciones porciones;
  final InstruccionesPreparacion instruccionesPreparacion;
  final TransicionDieta? transicionDieta;
  final String? vetComment;
  final DateTime? reviewDate;
  final String disclaimer;

  bool get isActive => status == 'ACTIVE';
  bool get isPendingVet => status == 'PENDING_VET';
}

/// Modelo resumido para listados — refleja PlanSummaryResponse del backend.
class PlanSummary {
  PlanSummary({
    required this.planId,
    required this.petId,
    required this.status,
    required this.modality,
    required this.rerKcal,
    required this.derKcal,
    required this.llmModelUsed,
  });

  factory PlanSummary.fromJson(Map<String, dynamic> json) => PlanSummary(
        planId: json['plan_id'] as String,
        petId: json['pet_id'] as String,
        status: json['status'] as String,
        modality: json['modality'] as String,
        rerKcal: (json['rer_kcal'] as num).toDouble(),
        derKcal: (json['der_kcal'] as num).toDouble(),
        llmModelUsed: json['llm_model_used'] as String,
      );

  final String planId;
  final String petId;
  final String status;
  final String modality;
  final double rerKcal;
  final double derKcal;
  final String llmModelUsed;

  bool get isActive => status == 'ACTIVE';
}

/// Modelo de job de generación — refleja PlanJobResponse del backend.
class PlanJob {
  PlanJob({
    required this.jobId,
    required this.status,
    this.planId,
    this.errorMessage,
  });

  factory PlanJob.fromJson(Map<String, dynamic> json) => PlanJob(
        jobId: json['job_id'] as String,
        status: json['status'] as String,
        planId: json['plan_id'] as String?,
        errorMessage: json['error_message'] as String?,
      );

  final String jobId;
  final String status; // QUEUED | PROCESSING | READY | FAILED
  final String? planId;
  final String? errorMessage;

  bool get isReady => status == 'READY';
  bool get isFailed => status == 'FAILED';
  bool get isPending => status == 'QUEUED' || status == 'PROCESSING';
}

@riverpod
PlanRepository planRepository(Ref ref) =>
    PlanRepository(dio: ref.watch(apiClientProvider));

class PlanRepository {
  PlanRepository({required this.dio});

  final Dio dio;

  /// Encola la generación de un plan. Retorna job para polling.
  Future<PlanJob> generatePlan({
    required String petId,
    required String modality,
  }) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/plans/generate',
      data: {'pet_id': petId, 'modality': modality},
    );
    return PlanJob.fromJson(response.data!);
  }

  /// Polling del estado del job de generación.
  Future<PlanJob> getJobStatus(String jobId) async {
    final response = await dio.get<Map<String, dynamic>>(
      '/v1/plans/jobs/$jobId',
    );
    return PlanJob.fromJson(response.data!);
  }

  /// Lista resúmenes de planes del owner autenticado.
  Future<List<PlanSummary>> listPlans() async {
    final response = await dio.get<List<dynamic>>('/v1/plans');
    return (response.data!)
        .map((e) => PlanSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Carga el detalle completo de un plan.
  Future<PlanDetail> getPlan(String planId) async {
    final response =
        await dio.get<Map<String, dynamic>>('/v1/plans/$planId');
    return PlanDetail.fromJson(response.data!);
  }

  /// Exporta el plan a PDF y comparte la URL pre-signed.
  Future<void> exportAndShare(String planId) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/plans/$planId/export',
    );
    final url = response.data!['url'] as String;
    await Share.share(
      'Plan nutricional NutriVet.IA: $url',
      subject: 'Plan nutricional de tu mascota',
    );
  }
}
