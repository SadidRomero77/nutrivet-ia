/// Almacenamiento seguro para tokens JWT.
///
/// Usa flutter_secure_storage (Keychain en iOS, Keystore en Android).
/// En Linux desktop (desarrollo/WSL2) usa fallback en memoria cuando
/// el keyring del sistema no está disponible.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'secure_storage.g.dart';

const _keyAccess = 'access_token';
const _keyRefresh = 'refresh_token';
const _keyRole = 'user_role';

/// Proveedor del servicio de almacenamiento seguro.
///
/// keepAlive: true — garantiza una única instancia durante toda la vida de la app.
/// Evita que el estado _useMemoryFallback y _memoryFallback se pierdan si el
/// proveedor se auto-destruye y re-crea, lo que causaría lecturas inconsistentes
/// entre el router y los repositorios.
@Riverpod(keepAlive: true)
SecureStorageService secureStorage(Ref ref) => SecureStorageService();

/// Servicio de lectura/escritura de tokens JWT en almacenamiento seguro.
///
/// En Linux sin keyring (WSL2/CI) usa un mapa en memoria como fallback.
class SecureStorageService {
  SecureStorageService()
      : _storage = const FlutterSecureStorage(
          aOptions: AndroidOptions(encryptedSharedPreferences: true),
          lOptions: LinuxOptions(),
        );

  final FlutterSecureStorage _storage;

  // Fallback en memoria para Linux sin keyring (WSL2 / CI)
  final Map<String, String> _memoryFallback = {};
  bool _useMemoryFallback = false;

  Future<String?> readAccessToken() => _read(_keyAccess);
  Future<String?> readRefreshToken() => _read(_keyRefresh);
  Future<String?> readRole() => _read(_keyRole);

  Future<void> writeTokens({
    required String accessToken,
    required String refreshToken,
    String role = 'owner',
  }) async {
    await _write(_keyAccess, accessToken);
    await _write(_keyRefresh, refreshToken);
    await _write(_keyRole, role);
  }

  Future<void> deleteTokens() async {
    // Eliminar siempre de memoria Y del almacenamiento real, incluso si estamos
    // en modo fallback — evita tokens stale que persisten al reiniciar la app.
    _memoryFallback.remove(_keyAccess);
    _memoryFallback.remove(_keyRefresh);
    _memoryFallback.remove(_keyRole);
    try {
      await Future.wait([
        _storage.delete(key: _keyAccess),
        _storage.delete(key: _keyRefresh),
        _storage.delete(key: _keyRole),
      ]);
    } catch (_) {
      // Ignorar errores de almacenamiento — los tokens en memoria ya fueron
      // eliminados; el usuario queda desautenticado en esta sesión.
    }
  }

  Future<bool> hasTokens() async {
    final token = await readAccessToken();
    return token != null;
  }

  // ─── Helpers con fallback ─────────────────────────────────────────────────

  Future<String?> _read(String key) async {
    if (_useMemoryFallback) return _memoryFallback[key];
    try {
      return await _storage.read(key: key).timeout(
        const Duration(seconds: 3),
        onTimeout: () {
          _useMemoryFallback = true;
          return _memoryFallback[key];
        },
      );
    } catch (_) {
      _useMemoryFallback = true;
      return _memoryFallback[key];
    }
  }

  Future<void> _write(String key, String value) async {
    if (_useMemoryFallback) {
      _memoryFallback[key] = value;
      return;
    }
    try {
      await _storage.write(key: key, value: value).timeout(
        const Duration(seconds: 3),
        onTimeout: () {
          _useMemoryFallback = true;
          _memoryFallback[key] = value;
        },
      );
    } catch (_) {
      _useMemoryFallback = true;
      _memoryFallback[key] = value;
    }
  }

}
