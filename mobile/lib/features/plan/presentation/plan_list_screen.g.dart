// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'plan_list_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$planListHash() => r'44af8479ad0cf42583275a82dc87202cc8bb33d1';

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

/// See also [_planList].
@ProviderFor(_planList)
const _planListProvider = _PlanListFamily();

/// See also [_planList].
class _PlanListFamily extends Family<AsyncValue<List<PlanSummary>>> {
  /// See also [_planList].
  const _PlanListFamily();

  /// See also [_planList].
  _PlanListProvider call(
    String petId,
  ) {
    return _PlanListProvider(
      petId,
    );
  }

  @override
  _PlanListProvider getProviderOverride(
    covariant _PlanListProvider provider,
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
  String? get name => r'_planListProvider';
}

/// See also [_planList].
class _PlanListProvider extends AutoDisposeFutureProvider<List<PlanSummary>> {
  /// See also [_planList].
  _PlanListProvider(
    String petId,
  ) : this._internal(
          (ref) => _planList(
            ref as _PlanListRef,
            petId,
          ),
          from: _planListProvider,
          name: r'_planListProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$planListHash,
          dependencies: _PlanListFamily._dependencies,
          allTransitiveDependencies: _PlanListFamily._allTransitiveDependencies,
          petId: petId,
        );

  _PlanListProvider._internal(
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
    FutureOr<List<PlanSummary>> Function(_PlanListRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: _PlanListProvider._internal(
        (ref) => create(ref as _PlanListRef),
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
  AutoDisposeFutureProviderElement<List<PlanSummary>> createElement() {
    return _PlanListProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is _PlanListProvider && other.petId == petId;
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
mixin _PlanListRef on AutoDisposeFutureProviderRef<List<PlanSummary>> {
  /// The parameter `petId` of this provider.
  String get petId;
}

class _PlanListProviderElement
    extends AutoDisposeFutureProviderElement<List<PlanSummary>>
    with _PlanListRef {
  _PlanListProviderElement(super.provider);

  @override
  String get petId => (origin as _PlanListProvider).petId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
