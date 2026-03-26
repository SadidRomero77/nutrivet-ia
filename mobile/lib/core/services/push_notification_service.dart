/// PushNotificationService — gestión de FCM tokens y notificaciones entrantes.
///
/// Responsabilidades:
///   1. Solicitar permisos de notificación al usuario.
///   2. Obtener el FCM token del dispositivo y registrarlo en el backend.
///   3. Escuchar notificaciones en foreground y mostrar snackbar.
///   4. Al refrescar el token, re-registrarlo en el backend.
///   5. Eliminar el token del backend al hacer logout.
///
/// Setup requerido:
///   - Android: agregar google-services.json en android/app/
///   - iOS: agregar GoogleService-Info.plist en ios/Runner/
///   - Seguir guía: https://firebase.google.com/docs/flutter/setup
library;

import 'package:dio/dio.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../storage/secure_storage.dart';

/// Handler de mensajes en background (función de nivel superior — requerido por FCM).
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // No hacer nada en background — el sistema operativo muestra la notificación.
  // Si necesitas procesar datos en background, inicializa Firebase aquí.
  debugPrint('[FCM] Mensaje en background: ${message.messageId}');
}

class PushNotificationService {
  PushNotificationService._();

  static final PushNotificationService instance = PushNotificationService._();

  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final Dio _dio = Dio(BaseOptions(
    baseUrl: const String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'http://10.0.2.2:8000',
    ),
    headers: {'Content-Type': 'application/json'},
    connectTimeout: const Duration(seconds: 10),
  ));
  final SecureStorageService _storage = SecureStorageService();

  bool _initialized = false;

  /// Inicializa Firebase y configura FCM.
  ///
  /// Llamar una vez desde main() ANTES de runApp():
  /// ```dart
  /// await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  /// await PushNotificationService.instance.initialize();
  /// ```
  Future<void> initialize() async {
    if (_initialized) return;

    // Registrar handler de background
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // Solicitar permisos (iOS muestra diálogo, Android 13+ también)
    final settings = await _fcm.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      debugPrint('[FCM] Permisos de notificación denegados por el usuario.');
      _initialized = true;
      return;
    }

    // Escuchar refrescos del token
    _fcm.onTokenRefresh.listen((newToken) async {
      await _registerToken(newToken);
    });

    // Escuchar mensajes en foreground (mostrar banner en app)
    FirebaseMessaging.onMessage.listen((message) {
      debugPrint(
        '[FCM] Mensaje en foreground: ${message.notification?.title} — '
        '${message.notification?.body}',
      );
      // Notificar a la capa de UI via el notifier
      _onForegroundMessage?.call(message);
    });

    _initialized = true;
    debugPrint('[FCM] PushNotificationService inicializado.');
  }

  /// Registra el token FCM del dispositivo en el backend.
  ///
  /// Llamar después de login exitoso.
  Future<void> registerCurrentToken() async {
    try {
      // En web no hay token FCM nativo
      if (kIsWeb) return;

      final token = await _fcm.getToken();
      if (token == null) {
        debugPrint('[FCM] No se pudo obtener token FCM.');
        return;
      }

      await _registerToken(token);
    } catch (e) {
      // No interrumpir el flujo principal si FCM falla
      debugPrint('[FCM] Error obteniendo token: $e');
    }
  }

  /// Elimina el token FCM del backend al hacer logout.
  Future<void> unregisterCurrentToken() async {
    try {
      if (kIsWeb) return;

      final token = await _fcm.getToken();
      if (token == null) return;

      final authToken = await _storage.readAccessToken();
      await _dio.delete(
        '/v1/devices/token',
        data: {'token': token},
        options: Options(headers: {'Authorization': 'Bearer $authToken'}),
      );
      debugPrint('[FCM] Token eliminado del backend.');
    } catch (e) {
      debugPrint('[FCM] Error eliminando token: $e');
    }
  }

  Future<void> _registerToken(String token) async {
    try {
      final platform = defaultTargetPlatform == TargetPlatform.iOS ? 'ios' : 'android';
      final authToken = await _storage.readAccessToken();
      await _dio.post(
        '/v1/devices/token',
        data: {'token': token, 'platform': platform},
        options: Options(headers: {'Authorization': 'Bearer $authToken'}),
      );
      debugPrint('[FCM] Token registrado en backend: ...${token.substring(token.length - 8)}');
    } catch (e) {
      debugPrint('[FCM] Error registrando token en backend: $e');
    }
  }

  // Callback para mensajes en foreground — la UI puede suscribirse
  void Function(RemoteMessage)? _onForegroundMessage;

  void setForegroundMessageHandler(void Function(RemoteMessage) handler) {
    _onForegroundMessage = handler;
  }
}
