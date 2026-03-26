// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'admin_user_detail_screen.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$adminUserDetailHash() => r'181f38b31faad1a017ad37fedfca97b9324a37e1';

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

/// See also [_adminUserDetail].
@ProviderFor(_adminUserDetail)
const _adminUserDetailProvider = _AdminUserDetailFamily();

/// See also [_adminUserDetail].
class _AdminUserDetailFamily extends Family<AsyncValue<AdminUser>> {
  /// See also [_adminUserDetail].
  const _AdminUserDetailFamily();

  /// See also [_adminUserDetail].
  _AdminUserDetailProvider call(
    String userId,
  ) {
    return _AdminUserDetailProvider(
      userId,
    );
  }

  @override
  _AdminUserDetailProvider getProviderOverride(
    covariant _AdminUserDetailProvider provider,
  ) {
    return call(
      provider.userId,
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
  String? get name => r'_adminUserDetailProvider';
}

/// See also [_adminUserDetail].
class _AdminUserDetailProvider extends AutoDisposeFutureProvider<AdminUser> {
  /// See also [_adminUserDetail].
  _AdminUserDetailProvider(
    String userId,
  ) : this._internal(
          (ref) => _adminUserDetail(
            ref as _AdminUserDetailRef,
            userId,
          ),
          from: _adminUserDetailProvider,
          name: r'_adminUserDetailProvider',
          debugGetCreateSourceHash:
              const bool.fromEnvironment('dart.vm.product')
                  ? null
                  : _$adminUserDetailHash,
          dependencies: _AdminUserDetailFamily._dependencies,
          allTransitiveDependencies:
              _AdminUserDetailFamily._allTransitiveDependencies,
          userId: userId,
        );

  _AdminUserDetailProvider._internal(
    super._createNotifier, {
    required super.name,
    required super.dependencies,
    required super.allTransitiveDependencies,
    required super.debugGetCreateSourceHash,
    required super.from,
    required this.userId,
  }) : super.internal();

  final String userId;

  @override
  Override overrideWith(
    FutureOr<AdminUser> Function(_AdminUserDetailRef provider) create,
  ) {
    return ProviderOverride(
      origin: this,
      override: _AdminUserDetailProvider._internal(
        (ref) => create(ref as _AdminUserDetailRef),
        from: from,
        name: null,
        dependencies: null,
        allTransitiveDependencies: null,
        debugGetCreateSourceHash: null,
        userId: userId,
      ),
    );
  }

  @override
  AutoDisposeFutureProviderElement<AdminUser> createElement() {
    return _AdminUserDetailProviderElement(this);
  }

  @override
  bool operator ==(Object other) {
    return other is _AdminUserDetailProvider && other.userId == userId;
  }

  @override
  int get hashCode {
    var hash = _SystemHash.combine(0, runtimeType.hashCode);
    hash = _SystemHash.combine(hash, userId.hashCode);

    return _SystemHash.finish(hash);
  }
}

@Deprecated('Will be removed in 3.0. Use Ref instead')
// ignore: unused_element
mixin _AdminUserDetailRef on AutoDisposeFutureProviderRef<AdminUser> {
  /// The parameter `userId` of this provider.
  String get userId;
}

class _AdminUserDetailProviderElement
    extends AutoDisposeFutureProviderElement<AdminUser>
    with _AdminUserDetailRef {
  _AdminUserDetailProviderElement(super.provider);

  @override
  String get userId => (origin as _AdminUserDetailProvider).userId;
}
// ignore_for_file: type=lint
// ignore_for_file: subtype_of_sealed_class, invalid_use_of_internal_member, invalid_use_of_visible_for_testing_member, deprecated_member_use_from_same_package
