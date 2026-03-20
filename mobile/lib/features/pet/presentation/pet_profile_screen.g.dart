// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pet_profile_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$petDetailHash() => r'9ac064ab5bea25f3d1eb4c011ee50fc02a7c30b6';

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

/// See also [_petDetail].
@ProviderFor(_petDetail)
const _petDetailProvider = _PetDetailFamily();

/// See also [_petDetail].
class _PetDetailFamily extends Family<AsyncValue<PetModel>> {
  /// See also [_petDetail].
  const _PetDetailFamily();

  /// See also [_petDetail].
  _PetDetailProvider call(
    String petId,
  ) {
    return _PetDetailProvider(
      petId,
    );
  }

  @override
  _PetDetailProvider getProviderOverride(
    covariant _PetDetailProvider provider,
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
  String? get name => r'_petDetailProvider';
}

/// See also [_petDetail].
class _PetDetailProvider extends AutoDisposeFutureProvider<PetModel> {
  /// See also [_petDetail].
  _PetDetailProvider(
    String petId,
  ) : this._internal(
          (ref) => _petDetail(
            ref as _PetDetailRef,
            petId,
          ),
          from: _petDetailProvider,
          name: r'_petDetailProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$petDetailHash,
          dependencies: _PetDetailFamily._dependencies,
          allTransitiveDependencies:
              _PetDetailFamily._allTransitiveDependencies,
          petId: petId,
        );

  _PetDetailProvider._internal(
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
    FutureOr<PetModel> Function(_PetDetailRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: _PetDetailProvider._internal(
        (ref) => create(ref as _PetDetailRef),
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
    return _PetDetailProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is _PetDetailProvider && other.petId == petId;
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
mixin _PetDetailRef on AutoDisposeFutureProviderRef<PetModel> {
  /// The parameter `petId` of this provider.
  String get petId;
}

class _PetDetailProviderElement
    extends AutoDisposeFutureProviderElement<PetModel> with _PetDetailRef {
  _PetDetailProviderElement(super.provider);

  @override
  String get petId => (origin as _PetDetailProvider).petId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
