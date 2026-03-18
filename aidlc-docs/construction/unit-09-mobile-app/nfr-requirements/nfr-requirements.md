# NFR Requirements — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Mobile App

### NFR-MOB-01: Offline — Plan y Historial de Chat
- El plan activo y las últimas 10 conversaciones deben estar disponibles sin conexión.
- Datos cacheados en Hive al momento de cargarlos online.
- Indicador de "modo offline" visible en la UI cuando no hay conexión.
- Verificado en test de integración: desactivar red → abrir plan → visible correctamente.

### NFR-MOB-02: Wizard Draft Persiste entre Cierres
- El borrador del wizard sobrevive cierre de app (force close, reboot).
- Verificado en test: completar 3 pasos → cerrar app → reabrir → borrador restaurado.
- El borrador se almacena en Hive con typeId único.

### NFR-MOB-03: TTFT del Chat < 1 Segundo (percibido)
- El usuario ve el primer chunk de texto en < 1 segundo (percibido, optimistic UI).
- El mensaje del usuario aparece inmediatamente (0ms percibido).
- El primer chunk del LLM típicamente llega en 200-500ms.

### NFR-MOB-04: JWT en Keychain / Keystore
- Los tokens JWT se almacenan en `flutter_secure_storage` (iOS Keychain, Android Keystore).
- NUNCA se almacenan en `SharedPreferences` ni en Hive sin encriptación.
- Verificado: el código de almacenamiento de tokens usa exclusivamente `flutter_secure_storage`.

### NFR-MOB-05: iOS 15+ / Android API 26+
- `minSdkVersion 26` en `android/app/build.gradle`.
- `platform :ios, '15.0'` en `ios/Podfile`.
- Verificado en CI: `flutter build apk` y `flutter build ipa` sin errores de versión.

### NFR-MOB-06: BCS — 9 Siluetas por Especie
- El selector de BCS muestra siluetas específicas por especie (perro / gato).
- Las siluetas del 1 al 9 deben ser visualmente distinguibles.
- Verificado en test de widget: 9 siluetas visibles, tappable, valor correcto al seleccionar.

### NFR-MOB-07: Disclaimer Siempre Visible en Plan
- La pantalla del plan siempre muestra el disclaimer al final de la vista.
- No es dismissable. No está fuera del viewport inicial sin scroll.
- Verificado en widget test: buscar texto del disclaimer en el árbol de widgets.

### NFR-MOB-08: Compresión de Imagen < 10MB
- La app comprime imágenes > 10MB antes de enviarlas al scanner.
- Verificado en test: imagen de 15MB → comprimida a < 10MB antes del multipart upload.

### NFR-MOB-09: flutter analyze sin Errores
- `flutter analyze` sin errores en CI.
- `flutter test` pasa con ≥ 70% cobertura (meta para MVP — no tan estricta como backend).
- Se verifica en cada PR antes de merge.

### NFR-MOB-10: App Size Razonable
- APK release < 50MB (después de obfuscation y tree-shaking).
- IPA release < 60MB.
- No incluir assets innecesarios en el bundle.
- Imágenes de BCS en formato WebP para reducir tamaño.
