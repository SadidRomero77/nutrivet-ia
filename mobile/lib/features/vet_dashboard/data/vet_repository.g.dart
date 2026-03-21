// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vet_repository.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$vetRepositoryHash() => r'c098c355bfa1c228d9d438f322deff2e6f02d7a5';

/// See also [vetRepository].
@ProviderFor(vetRepository)
final vetRepositoryProvider = AutoDisposeProvider<VetRepository>.internal(
  vetRepository,
  name: r'vetRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$vetRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef VetRepositoryRef = AutoDisposeProviderRef<VetRepository>;
String _$vetPatientsHash() => r'74e3fc17f9278049198b31bc7f99c4483014df82';

/// Pacientes del vet — cacheado para uso en el drawer y otras pantallas.
///
/// Copied from [vetPatients].
@ProviderFor(vetPatients)
final vetPatientsProvider = AutoDisposeFutureProvider<List<PetModel>>.internal(
  vetPatients,
  name: r'vetPatientsProvider',
  debugGetCreateSourceHash:
      const bool.fromEnvironment('dart.vm.product') ? null : _$vetPatientsHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
typedef VetPatientsRef = AutoDisposeFutureProviderRef<List<PetModel>>;
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
