/// Repositorio de mascotas — CRUD + sincronización offline (Hive).
library;

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../core/api/api_client.dart';

part 'pet_repository.g.dart';

/// Modelo de mascota para UI.
class PetModel {
  PetModel({
    required this.petId,
    required this.name,
    required this.species,
    required this.breed,
    required this.sex,
    required this.ageMonths,
    required this.weightKg,
    this.size,
    required this.reproductiveStatus,
    required this.activityLevel,
    required this.bcs,
    required this.medicalConditions,
    required this.allergies,
    required this.currentFeedingType,
    this.vetId,
    this.ownerName,
    this.ownerPhone,
    this.claimCode,
  });

  factory PetModel.fromJson(Map<String, dynamic> json) => PetModel(
        petId: json['pet_id'] as String,
        name: json['name'] as String,
        species: json['species'] as String,
        breed: json['breed'] as String,
        sex: json['sex'] as String,
        ageMonths: (json['age_months'] as num).toInt(),
        weightKg: (json['weight_kg'] as num).toDouble(),
        size: json['size'] as String?,
        reproductiveStatus: json['reproductive_status'] as String,
        activityLevel: json['activity_level'] as String,
        bcs: (json['bcs'] as num).toInt(),
        medicalConditions: List<String>.from(
          json['medical_conditions'] as List? ?? [],
        ),
        allergies: List<String>.from(json['allergies'] as List? ?? []),
        currentFeedingType: json['current_diet'] as String,
        vetId: json['vet_id'] as String?,
        ownerName: json['owner_name'] as String?,
        ownerPhone: json['owner_phone'] as String?,
        claimCode: json['claim_code'] as String?,
      );

  final String petId;
  final String name;
  final String species;
  final String breed;
  final String sex;
  final int ageMonths;
  final double weightKg;
  final String? size;
  final String reproductiveStatus;
  final String activityLevel;
  final int bcs;
  final List<String> medicalConditions;
  final List<String> allergies;
  final String currentFeedingType;
  final String? vetId;
  // Campos exclusivos de pacientes clínicos (solo presentes en endpoints vet)
  final String? ownerName;
  final String? ownerPhone;
  final String? claimCode;
}

@riverpod
PetRepository petRepository(Ref ref) =>
    PetRepository(dio: ref.watch(apiClientProvider));

class PetRepository {
  PetRepository({required this.dio});

  final Dio dio;
  static const _boxName = 'pets';

  /// Lista todas las mascotas del usuario autenticado.
  Future<List<PetModel>> listPets() async {
    final box = await Hive.openBox<Map>(_boxName);
    try {
      final response =
          await dio.get<List<dynamic>>('/v1/pets');
      final pets = (response.data!)
          .map((e) => PetModel.fromJson(e as Map<String, dynamic>))
          .toList();
      // Guardar en cache local como Map incluyendo todos los campos
      for (final pet in pets) {
        await box.put(pet.petId, {
          'pet_id': pet.petId,
          'name': pet.name,
          'species': pet.species,
          'breed': pet.breed,
          'sex': pet.sex,
          'age_months': pet.ageMonths,
          'weight_kg': pet.weightKg,
          'size': pet.size,
          'reproductive_status': pet.reproductiveStatus,
          'activity_level': pet.activityLevel,
          'bcs': pet.bcs,
          'medical_conditions': pet.medicalConditions,
          'allergies': pet.allergies,
          'current_diet': pet.currentFeedingType,
          'vet_id': pet.vetId,
          'owner_name': pet.ownerName,
          'owner_phone': pet.ownerPhone,
          'claim_code': pet.claimCode,
        });
      }
      return pets;
    } on DioException {
      // Fallback a cache offline
      return box.values
          .map((e) => PetModel.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    }
  }

  /// Crea una nueva mascota (13 campos del wizard).
  Future<PetModel> createPet(Map<String, dynamic> data) async {
    try {
      final response =
          await dio.post<Map<String, dynamic>>('/v1/pets', data: data);
      return PetModel.fromJson(response.data!);
    } on DioException catch (e) {
      throw Exception(_extractDetail(e));
    }
  }

  /// Actualiza datos editables de la mascota (peso, BCS, actividad, dieta).
  Future<PetModel> updatePet(String petId, Map<String, dynamic> data) async {
    try {
      final response = await dio.patch<Map<String, dynamic>>(
        '/v1/pets/$petId',
        data: data,
      );
      return PetModel.fromJson(response.data!);
    } on DioException catch (e) {
      throw Exception(_extractDetail(e));
    }
  }

  /// Elimina (soft-delete) una mascota.
  /// Lanza Exception si la mascota tiene planes activos.
  Future<void> deletePet(String petId) async {
    try {
      await dio.delete<void>('/v1/pets/$petId');
    } on DioException catch (e) {
      throw Exception(_extractDetail(e));
    }
  }

  /// Extrae el campo 'detail' del cuerpo de la respuesta de error del backend.
  static String _extractDetail(DioException e) {
    final data = e.response?.data;
    if (data is Map) {
      final detail = data['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        // Errores de validación Pydantic: lista de objetos con 'msg'
        final first = detail.first;
        if (first is Map) return first['msg']?.toString() ?? detail.toString();
      }
    }
    final status = e.response?.statusCode;
    if (status == 401) return 'Sesión expirada. Por favor inicia sesión nuevamente.';
    if (status == 403) return 'No tienes permisos para realizar esta acción.';
    if (status == 422) return 'Datos inválidos. Revisa el formulario.';
    return 'Error de conexión. Verifica tu internet e intenta de nuevo.';
  }
}
