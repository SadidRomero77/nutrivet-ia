// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vet_patient_profile_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$vetPatientHash() => r'57ba8ec8ea89a4847ac2baf7541c37febae5c1ef';

/// Copied from Dart SDK
class _SystemHash {
  _SystemHash._();

  static int combine(int hash, int value) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + value);
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x0007ffff & hash) << 10));
    return hash ^ (hash >> 6);
  }

  static int finish(int hash) {
    // ignore: parameter_assignments
    hash = 0x1fffffff & (hash + ((0x03ffffff & hash) << 3));
    // ignore: parameter_assignments
    hash = hash ^ (hash >> 11);
    return 0x1fffffff & (hash + ((0x00003fff & hash) << 15));
  }
}

/// See also [_vetPatient].
@ProviderFor(_vetPatient)
const _vetPatientProvider = _VetPatientFamily();

/// See also [_vetPatient].
class _VetPatientFamily extends Family<AsyncValue<PetModel>> {
  /// See also [_vetPatient].
  const _VetPatientFamily();

  /// See also [_vetPatient].
  _VetPatientProvider call(
    String petId,
  ) {
    return _VetPatientProvider(
      petId,
    );
  }

  @override
  _VetPatientProvider getProviderOverride(
    covariant _VetPatientProvider provider,
  ) {
    return call(
      provider.petId,
    );
  }

  static const Iterable<ProviderOrFamily>? _dependencies = null;

  @override
  Iterable<ProviderOrFamily>? get dependencies => _dependencies;

  static const Iterable<ProviderOrFamily>? _allTransitiveDependencies = null;

  @override
  Iterable<ProviderOrFamily>? get allTransitiveDependencies =>
      _allTransitiveDependencies;

  @override
  String? get name => r'_vetPatientProvider';
}

/// See also [_vetPatient].
class _VetPatientProvider extends AutoDisposeFutureProvider<PetModel> {
  /// See also [_vetPatient].
  _VetPatientProvider(
    String petId,
  ) : this._internal(
          (ref) => _vetPatient(
            ref as _VetPatientRef,
            petId,
          ),
          from: _vetPatientProvider,
          name: r'_vetPatientProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$vetPatientHash,
          dependencies: _VetPatientFamily._dependencies,
          allTransitiveDependencies:
              _VetPatientFamily._allTransitiveDependencies,
          petId: petId,
        );

  _VetPatientProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.petId,
  }) : super.internal();

  final String petId;

  @override
  Override overrideWith(
    FutureOr<PetModel> Function(_VetPatientRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: _VetPatientProvider._internal(
        (ref) => create(ref as _VetPatientRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        petId: petId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<PetModel> createElement() {
    return _VetPatientProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is _VetPatientProvider && other.petId == petId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, petId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin _VetPatientRef on AutoDisposeFutureProviderRef<PetModel> {
  /// The parameter `petId` of this provider.
  String get petId;
}

class _VetPatientProviderElement
    extends AutoDisposeFutureProviderElement<PetModel> with _VetPatientRef {
  _VetPatientProviderElement(super.provider);

  @override
  String get petId => (origin as _VetPatientProvider).petId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
