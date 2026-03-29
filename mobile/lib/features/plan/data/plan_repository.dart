/// Repositorio de planes nutricionales — lectura, exportación y cache offline.
library;

import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/api/api_client.dart';

part 'plan_repository.g.dart';

// ---------------------------------------------------------------------------
// Modelos — reflejan exactamente PlanResponse del backend
// ---------------------------------------------------------------------------

class PerfilNutricional {
  PerfilNutricional({
    required this.rerKcal,
    required this.derKcal,
    required this.weightPhase,
    this.proteinPct,
    this.fatPct,
    this.racionTotalGDia,
    this.relacionCaP,
    this.omega3MgDia,
  });

  factory PerfilNutricional.fromJson(Map<String, dynamic> json) =>
      PerfilNutricional(
        rerKcal: (json['rer_kcal'] as num).toDouble(),
        derKcal: (json['der_kcal'] as num).toDouble(),
        weightPhase: json['weight_phase'] as String,
        proteinPct: (json['protein_pct'] as num?)?.toDouble(),
        fatPct: (json['fat_pct'] as num?)?.toDouble(),
        racionTotalGDia: (json['racion_total_g_dia'] as num?)?.toDouble(),
        relacionCaP: (json['relacion_ca_p'] as num?)?.toDouble(),
        omega3MgDia: (json['omega3_mg_dia'] as num?)?.toDouble(),
      );

  final double rerKcal;
  final double derKcal;
  final String weightPhase;
  final double? proteinPct;
  final double? fatPct;
  final double? racionTotalGDia;
  final double? relacionCaP;
  final double? omega3MgDia;
}

class IngredientItem {
  IngredientItem({
    required this.nombre,
    this.cantidadG,
    this.kcal,
    this.proteinaG,
    this.grasaG,
    this.fuente,
    this.frecuencia,
    this.notas,
  });

  factory IngredientItem.fromJson(Map<String, dynamic> json) => IngredientItem(
        nombre: json['nombre'] as String,
        cantidadG: (json['cantidad_g'] as num?)?.toDouble(),
        kcal: (json['kcal'] as num?)?.toDouble(),
        proteinaG: (json['proteina_g'] as num?)?.toDouble(),
        grasaG: (json['grasa_g'] as num?)?.toDouble(),
        fuente: json['fuente'] as String?,
        frecuencia: json['frecuencia'] as String?,
        notas: json['notas'] as String?,
      );

  final String nombre;
  final double? cantidadG;
  final double? kcal;
  final double? proteinaG;
  final double? grasaG;
  final String? fuente;
  final String? frecuencia;
  final String? notas;
}

class ComidaDistribucion {
  ComidaDistribucion({
    required this.horario,
    this.porcentaje,
    this.gramos,
    this.proteinaG,
    this.carboG,
    this.vegeatalG,
  });

  factory ComidaDistribucion.fromJson(Map<String, dynamic> json) =>
      ComidaDistribucion(
        horario: json['horario'] as String,
        porcentaje: (json['porcentaje'] as num?)?.toDouble(),
        gramos: (json['gramos'] as num?)?.toDouble(),
        proteinaG: (json['proteina_g'] as num?)?.toDouble(),
        carboG: (json['carbo_g'] as num?)?.toDouble(),
        vegeatalG: (json['vegetal_g'] as num?)?.toDouble(),
      );

  final String horario;
  final double? porcentaje;
  final double? gramos;
  final double? proteinaG;
  final double? carboG;
  final double? vegeatalG;
}

class Porciones {
  Porciones({
    required this.comidasPorDia,
    this.totalGDia,
    this.gPorComida,
    this.distribucionComidas = const [],
  });

  factory Porciones.fromJson(Map<String, dynamic> json) => Porciones(
        comidasPorDia: (json['comidas_por_dia'] as num? ?? 2).toInt(),
        totalGDia: (json['total_g_dia'] as num?)?.toDouble(),
        gPorComida: (json['g_por_comida'] as num? ??
                json['porcion_por_comida_gramos'] as num?)
            ?.toDouble(),
        distribucionComidas: ((json['distribucion_comidas'] as List?) ?? [])
            .map((e) => ComidaDistribucion.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  final int comidasPorDia;
  final double? totalGDia;
  final double? gPorComida;
  final List<ComidaDistribucion> distribucionComidas;
}

class SupplementoItem {
  SupplementoItem({
    required this.nombre,
    required this.dosis,
    required this.frecuencia,
    required this.forma,
    required this.justificacion,
  });

  factory SupplementoItem.fromJson(Map<String, dynamic> json) =>
      SupplementoItem(
        nombre: json['nombre'] as String,
        dosis: json['dosis'] as String,
        frecuencia: json['frecuencia'] as String,
        forma: json['forma'] as String,
        justificacion: json['justificacion'] as String,
      );

  final String nombre;
  final String dosis;
  final String frecuencia;
  final String forma;
  final String justificacion;
}

class InstruccionesPorGrupo {
  InstruccionesPorGrupo({
    this.proteinas = const [],
    this.carbohidratos = const [],
    this.vegetales = const [],
  });

  factory InstruccionesPorGrupo.fromJson(Map<String, dynamic> json) =>
      InstruccionesPorGrupo(
        proteinas: List<String>.from(json['proteinas'] as List? ?? []),
        carbohidratos:
            List<String>.from(json['carbohidratos'] as List? ?? []),
        vegetales: List<String>.from(json['vegetales'] as List? ?? []),
      );

  final List<String> proteinas;
  final List<String> carbohidratos;
  final List<String> vegetales;

  bool get isEmpty =>
      proteinas.isEmpty && carbohidratos.isEmpty && vegetales.isEmpty;
}

class InstruccionesPreparacion {
  InstruccionesPreparacion({
    this.metodo,
    required this.pasos,
    this.tiempoPreparacionMinutos,
    this.almacenamiento,
    this.advertencias = const [],
    this.instruccionesPorGrupo,
    this.adicionesPermitidas = const [],
  });

  factory InstruccionesPreparacion.fromJson(Map<String, dynamic> json) =>
      InstruccionesPreparacion(
        metodo: json['metodo'] as String?,
        pasos: List<String>.from(json['pasos'] as List? ?? []),
        tiempoPreparacionMinutos: (json['tiempo_preparacion_minutos'] as num? ??
                json['tiempo_estimado_minutos'] as num?)
            ?.toInt(),
        almacenamiento: json['almacenamiento'] as String?,
        advertencias:
            List<String>.from(json['advertencias'] as List? ?? []),
        instruccionesPorGrupo:
            json['instrucciones_por_grupo'] is Map<String, dynamic>
                ? InstruccionesPorGrupo.fromJson(
                    json['instrucciones_por_grupo'] as Map<String, dynamic>)
                : null,
        adicionesPermitidas:
            List<String>.from(json['adiciones_permitidas'] as List? ?? []),
      );

  final String? metodo;
  final List<String> pasos;
  final int? tiempoPreparacionMinutos;
  final String? almacenamiento;
  final List<String> advertencias;
  final InstruccionesPorGrupo? instruccionesPorGrupo;
  final List<String> adicionesPermitidas;
}

class SnackSaludable {
  SnackSaludable({
    required this.nombre,
    required this.descripcion,
    required this.cantidadG,
    required this.frecuencia,
  });

  factory SnackSaludable.fromJson(Map<String, dynamic> json) => SnackSaludable(
        nombre: json['nombre'] as String,
        descripcion: json['descripcion'] as String,
        cantidadG: (json['cantidad_g'] as num).toDouble(),
        frecuencia: json['frecuencia'] as String,
      );

  final String nombre;
  final String descripcion;
  final double cantidadG;
  final String frecuencia;
}

class FaseTransicion {
  FaseTransicion({required this.dias, required this.descripcion});

  factory FaseTransicion.fromJson(Map<String, dynamic> json) => FaseTransicion(
        dias: json['dias'] as String,
        descripcion: json['descripcion'] as String,
      );

  final String dias;
  final String descripcion;
}

class TransicionDieta {
  TransicionDieta({
    required this.duracionDias,
    this.fases = const [],
    this.senalesDeAlerta = const [],
  });

  factory TransicionDieta.fromJson(Map<String, dynamic> json) =>
      TransicionDieta(
        duracionDias: (json['duracion_dias'] as num? ?? 7).toInt(),
        fases: ((json['fases'] as List?) ?? [])
            .map((e) => FaseTransicion.fromJson(e as Map<String, dynamic>))
            .toList(),
        senalesDeAlerta:
            List<String>.from(json['senales_de_alerta'] as List? ?? []),
      );

  final int duracionDias;
  final List<FaseTransicion> fases;
  final List<String> senalesDeAlerta;
}

/// Modelo detallado de plan — estructura clínica completa (ADR-020 + Lady Carolina ref).
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
    this.objetivosClinicos = const [],
    this.ingredientesProhibidos = const [],
    this.suplementos = const [],
    this.snacksSaludables = const [],
    this.protocloDigestivo = const [],
    this.notasClincias = const [],
    this.alertasPropietario = const [],
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
        objetivosClinicos: List<String>.from(
            json['objetivos_clinicos'] as List? ?? []),
        ingredientesProhibidos: List<String>.from(
            json['ingredientes_prohibidos'] as List? ?? []),
        ingredientes:
            ((json['ingredientes'] as Map<String, dynamic>?)?['items']
                        as List? ??
                    [])
                .map((e) =>
                    IngredientItem.fromJson(e as Map<String, dynamic>))
                .toList(),
        porciones: Porciones.fromJson(
          json['porciones'] as Map<String, dynamic>? ?? {},
        ),
        suplementos: ((json['suplementos'] as List?) ?? [])
            .map((e) =>
                SupplementoItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        instruccionesPreparacion: InstruccionesPreparacion.fromJson(
          json['instrucciones_preparacion'] as Map<String, dynamic>? ?? {},
        ),
        snacksSaludables: ((json['snacks_saludables'] as List?) ?? [])
            .map((e) =>
                SnackSaludable.fromJson(e as Map<String, dynamic>))
            .toList(),
        protocloDigestivo: List<String>.from(
            json['protocolo_digestivo'] as List? ?? []),
        notasClincias: List<String>.from(
            json['notas_clinicas'] as List? ?? []),
        alertasPropietario: List<String>.from(
            json['alertas_propietario'] as List? ?? []),
        transicionDieta: json['transicion_dieta'] != null
            ? TransicionDieta.fromJson(
                json['transicion_dieta'] as Map<String, dynamic>,
              )
            : null,
        vetComment: json['vet_comment'] as String?,
        reviewDate: json['review_date'] != null
            ? DateTime.tryParse(json['review_date'] as String)
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
  final List<String> objetivosClinicos;
  final List<String> ingredientesProhibidos;
  final List<IngredientItem> ingredientes;
  final Porciones porciones;
  final List<SupplementoItem> suplementos;
  final InstruccionesPreparacion instruccionesPreparacion;
  final List<SnackSaludable> snacksSaludables;
  final List<String> protocloDigestivo;
  final List<String> notasClincias;
  final List<String> alertasPropietario;
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

  static const _summaryBoxName = 'plan_summaries';
  static const _detailBoxName = 'plan_details';

  static const _activeJobsBox = 'active_plan_jobs';

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

  /// Persiste el job activo para que plan_list_screen pueda mostrarlo.
  Future<void> saveActiveJob(String petId, String jobId) async {
    final box = await Hive.openBox<String>(_activeJobsBox);
    await box.put(petId, jobId);
  }

  /// Lee el job activo de una mascota (null si no hay ninguno en curso).
  Future<String?> getActiveJob(String petId) async {
    final box = await Hive.openBox<String>(_activeJobsBox);
    return box.get(petId);
  }

  /// Elimina el job activo una vez que terminó (READY o FAILED).
  Future<void> clearActiveJob(String petId) async {
    final box = await Hive.openBox<String>(_activeJobsBox);
    await box.delete(petId);
  }

  /// Polling del estado del job de generación.
  Future<PlanJob> getJobStatus(String jobId) async {
    final response = await dio.get<Map<String, dynamic>>(
      '/v1/plans/jobs/$jobId',
    );
    return PlanJob.fromJson(response.data!);
  }

  /// Lista resúmenes de planes. Usa cache Hive si sin red.
  Future<List<PlanSummary>> listPlans() async {
    final box = await Hive.openBox<String>(_summaryBoxName);
    try {
      final response = await dio.get<List<dynamic>>('/v1/plans');
      final plans = (response.data!)
          .map((e) => PlanSummary.fromJson(
              Map<String, dynamic>.from(e as Map)))
          .toList();
      // Actualizar cache local
      await box.clear();
      for (final plan in plans) {
        await box.put(plan.planId, json.encode({
          'plan_id': plan.planId,
          'pet_id': plan.petId,
          'status': plan.status,
          'modality': plan.modality,
          'rer_kcal': plan.rerKcal,
          'der_kcal': plan.derKcal,
          'llm_model_used': plan.llmModelUsed,
        }));
      }
      return plans;
    } on DioException {
      // Fallback offline: devolver desde cache
      return box.values
          .map((e) => PlanSummary.fromJson(
              json.decode(e) as Map<String, dynamic>))
          .toList();
    }
  }

  /// Carga el detalle completo de un plan. Usa cache Hive si sin red.
  Future<PlanDetail> getPlan(String planId) async {
    final box = await Hive.openBox<String>(_detailBoxName);
    try {
      final response =
          await dio.get<Map<String, dynamic>>('/v1/plans/$planId');
      final plan = PlanDetail.fromJson(response.data!);
      // Guardar en cache como JSON string para evitar Map<dynamic,dynamic> en Hive
      await box.put(planId, json.encode(response.data!));
      return plan;
    } on DioException {
      // Fallback offline
      final cached = box.get(planId);
      if (cached != null) {
        return PlanDetail.fromJson(
            json.decode(cached) as Map<String, dynamic>);
      }
      rethrow;
    }
  }

  /// Solicita sustitución de un ingrediente via IA.
  Future<Map<String, dynamic>> requestSubstitute({
    required String planId,
    required String originalIngredient,
    required String substituteIngredient,
  }) async {
    final response = await dio.post<Map<String, dynamic>>(
      '/v1/plans/$planId/substitutes',
      data: {
        'original_ingredient': originalIngredient,
        'substitute_ingredient': substituteIngredient,
      },
    );
    return response.data!;
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
