// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'vet_review_plan_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$reviewPlanHash() => r'140c54e4e09ed923e53c64ce78f7bb2cc1b869af';

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

/// See also [_reviewPlan].
@ProviderFor(_reviewPlan)
const _reviewPlanProvider = _ReviewPlanFamily();

/// See also [_reviewPlan].
class _ReviewPlanFamily extends Family<AsyncValue<PlanDetail>> {
  /// See also [_reviewPlan].
  const _ReviewPlanFamily();

  /// See also [_reviewPlan].
  _ReviewPlanProvider call(
    String planId,
  ) {
    return _ReviewPlanProvider(
      planId,
    );
  }

  @override
  _ReviewPlanProvider getProviderOverride(
    covariant _ReviewPlanProvider provider,
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
  String? get name => r'_reviewPlanProvider';
}

/// See also [_reviewPlan].
class _ReviewPlanProvider extends AutoDisposeFutureProvider<PlanDetail> {
  /// See also [_reviewPlan].
  _ReviewPlanProvider(
    String planId,
  ) : this._internal(
          (ref) => _reviewPlan(
            ref as _ReviewPlanRef,
            planId,
          ),
          from: _reviewPlanProvider,
          name: r'_reviewPlanProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$reviewPlanHash,
          dependencies: _ReviewPlanFamily._dependencies,
          allTransitiveDependencies:
              _ReviewPlanFamily._allTransitiveDependencies,
          planId: planId,
        );

  _ReviewPlanProvider._internal(
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
    FutureOr<PlanDetail> Function(_ReviewPlanRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: _ReviewPlanProvider._internal(
        (ref) => create(ref as _ReviewPlanRef),
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
    return _ReviewPlanProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is _ReviewPlanProvider && other.planId == planId;
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
mixin _ReviewPlanRef on AutoDisposeFutureProviderRef<PlanDetail> {
  /// The parameter `planId` of this provider.
  String get planId;
}

class _ReviewPlanProviderElement
    extends AutoDisposeFutureProviderElement<PlanDetail> with _ReviewPlanRef {
  _ReviewPlanProviderElement(super.provider);

  @override
  String get planId => (origin as _ReviewPlanProvider).planId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
