/// Utilidad para decodificar JWT sin validar firma.
/// Solo se usa para extraer el payload (role, tier, user_id).
library;

import 'dart:convert';

class JwtUtils {
  JwtUtils._();

  /// Decodifica el payload de un JWT y retorna el mapa de claims.
  /// Retorna null si el token tiene formato inválido.
  static Map<String, dynamic>? decodePayload(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      var payload = parts[1];
      // Base64URL puede omitir el padding — lo restauramos
      final remainder = payload.length % 4;
      if (remainder != 0) payload += '=' * (4 - remainder);
      final decoded = utf8.decode(base64Url.decode(payload));
      return json.decode(decoded) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  /// Extrae el role del JWT. Retorna 'owner' por defecto si no puede leer.
  static String getRole(String token) {
    final payload = decodePayload(token);
    return payload?['role'] as String? ?? 'owner';
  }

  /// Extrae el tier del JWT. Retorna 'free' por defecto si no puede leer.
  static String getTier(String token) {
    final payload = decodePayload(token);
    return payload?['tier'] as String? ?? 'free';
  }
}
