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
      // Guardar en cache local como Map, no como PetModel
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
    final response =
        await dio.post<Map<String, dynamic>>('/v1/pets', data: data);
    return PetModel.fromJson(response.data!);
  }

  /// Actualiza datos editables de la mascota (peso, BCS, actividad, dieta).
  Future<PetModel> updatePet(String petId, Map<String, dynamic> data) async {
    final response = await dio.patch<Map<String, dynamic>>(
      '/v1/pets/$petId',
      data: data,
    );
    return PetModel.fromJson(response.data!);
  }

  /// Elimina (soft-delete) una mascota.
  /// Lanza Exception si la mascota tiene planes activos.
  Future<void> deletePet(String petId) async {
    try {
      await dio.delete<void>('/v1/pets/$petId');
    } on DioException catch (e) {
      final detail = (e.response?.data as Map?)?['detail'] as String?;
      throw Exception(detail ?? 'Error al eliminar la mascota');
    }
  }
}
