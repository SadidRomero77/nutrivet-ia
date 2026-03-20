// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'plan_detail_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$planDetailHash() => r'40f1e50ab951ac323c69f36a10ee45554a53b1c2';

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

/// See also [_planDetail].
@ProviderFor(_planDetail)
const _planDetailProvider = _PlanDetailFamily();

/// See also [_planDetail].
class _PlanDetailFamily extends Family<AsyncValue<PlanDetail>> {
  /// See also [_planDetail].
  const _PlanDetailFamily();

  /// See also [_planDetail].
  _PlanDetailProvider call(
    String planId,
  ) {
    return _PlanDetailProvider(
      planId,
    );
  }

  @override
  _PlanDetailProvider getProviderOverride(
    covariant _PlanDetailProvider provider,
  ) {
    return call(
      provider.planId,
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
  String? get name => r'_planDetailProvider';
}

/// See also [_planDetail].
class _PlanDetailProvider extends AutoDisposeFutureProvider<PlanDetail> {
  /// See also [_planDetail].
  _PlanDetailProvider(
    String planId,
  ) : this._internal(
          (ref) => _planDetail(
            ref as _PlanDetailRef,
            planId,
          ),
          from: _planDetailProvider,
          name: r'_planDetailProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$planDetailHash,
          dependencies: _PlanDetailFamily._dependencies,
          allTransitiveDependencies:
              _PlanDetailFamily._allTransitiveDependencies,
          planId: planId,
        );

  _PlanDetailProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.planId,
  }) : super.internal();

  final String planId;

  @override
  Override overrideWith(
    FutureOr<PlanDetail> Function(_PlanDetailRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: _PlanDetailProvider._internal(
        (ref) => create(ref as _PlanDetailRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        planId: planId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<PlanDetail> createElement() {
    return _PlanDetailProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is _PlanDetailProvider && other.planId == planId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, planId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin _PlanDetailRef on AutoDisposeFutureProviderRef<PlanDetail> {
  /// The parameter `planId` of this provider.
  String get planId;
}

class _PlanDetailProviderElement
    extends AutoDisposeFutureProviderElement<PlanDetail> with _PlanDetailRef {
  _PlanDetailProviderElement(super.provider);

  @override
  String get planId => (origin as _PlanDetailProvider).planId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
