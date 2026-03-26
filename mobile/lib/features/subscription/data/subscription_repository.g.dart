// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'subscription_repository.dart';

// **************************************************************************
// RiverpodGenerator
// **************************************************************************

String _$subscriptionRepositoryHash() =>
    r'subscription_repository_hash_placeholder';

@ProviderFor(subscriptionRepository)
final subscriptionRepositoryProvider =
    AutoDisposeProvider<SubscriptionRepository>.internal(
  subscriptionRepository,
  name: r'subscriptionRepositoryProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$subscriptionRepositoryHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
typedef SubscriptionRepositoryRef
    = AutoDisposeProviderRef<SubscriptionRepository>;

String _$subscriptionStatusHash() =>
    r'subscription_status_hash_placeholder';

@ProviderFor(subscriptionStatus)
final subscriptionStatusProvider =
    AutoDisposeFutureProvider<SubscriptionStatus>.internal(
  subscriptionStatus,
  name: r'subscriptionStatusProvider',
  debugGetCreateSourceHash: const bool.fromEnvironment('dart.vm.product')
      ? null
      : _$subscriptionStatusHash,
  dependencies: null,
  allTransitiveDependencies: null,
);

@Deprecated('Will be removed in 3.0. Use Ref instead')
typedef SubscriptionStatusRef
    = AutoDisposeFutureProviderRef<SubscriptionStatus>;
