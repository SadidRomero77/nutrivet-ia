# Business Rules — unit-09-mobile-app
**Unidad**: unit-09-mobile-app
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Mobile App

### BR-MOB-01: Wizard Draft — No Enviar Hasta 13 Campos
- El `PetWizardDraft` se almacena localmente en Hive.
- El botón "Crear mascota" solo se habilita cuando `draft.isComplete == true`.
- Si el usuario cierra la app durante el wizard → el borrador persiste en Hive y se restaura.
- Si el usuario desinstala la app → el borrador se pierde (dato local, no en cloud).

### BR-MOB-02: BCS — Selector Visual
- El selector de BCS muestra 9 imágenes de siluetas de mascotas (1–9).
- El usuario selecciona la silueta que más se parece a su mascota.
- Las imágenes deben ser distinguibles por especie (perro vs. gato).
- El BCS es un campo obligatorio del wizard.

### BR-MOB-03: JWT Refresh Automático
- El `Dio interceptor` verifica la expiración del access token antes de cada request.
- Si el token expira en < 60 segundos → hacer refresh antes del request.
- Si el refresh falla → redirigir al login screen.
- El refresh token se almacena en `flutter_secure_storage` (keychain iOS / keystore Android).

### BR-MOB-04: Polling del Job de Plan
- Después de `POST /plans/generate` → iniciar timer de polling cada 3 segundos.
- Polling a `GET /plans/jobs/{job_id}` hasta que `status == "completed"` o `"failed"`.
- Timeout del polling: 60 segundos → si no completa, mostrar "La generación está tomando más tiempo de lo esperado".
- En background: el push notification notifica cuando el plan está listo.

### BR-MOB-05: SSE Chat — Streaming en Tiempo Real
- El chat usa Dio con `responseType: ResponseType.stream` para consumir SSE.
- Cada chunk SSE se agrega al `streamingBuffer` del `ChatState`.
- Al recibir el evento `done` → el buffer completo se convierte en mensaje final.
- El mensaje del usuario se muestra inmediatamente (optimistic UI).

### BR-MOB-06: Offline — Plan y Chat en Hive
- El plan activo se cachea en Hive al descargarlo.
- Las últimas 10 conversaciones se cachean en Hive.
- En modo offline → el usuario puede ver el plan cacheado y el historial de chat.
- En modo offline → no puede enviar nuevos mensajes (indicador "Sin conexión").

### BR-MOB-07: Scanner — Solo Selección de Tipo de Imagen
- El usuario debe indicar si la imagen es "Tabla nutricional" o "Lista de ingredientes".
- No se puede enviar la imagen sin seleccionar el tipo.
- Botón "Cámara" y botón "Galería" para obtener la imagen.
- Max size: 10MB — si supera, la app redimensiona antes de enviar.

### BR-MOB-08: Upgrade Prompt
- Cuando el agente retorna `upgrade_required: true` → mostrar dialog de upgrade.
- El dialog muestra los beneficios del siguiente tier.
- El botón "Actualizar" lleva a la pantalla de suscripción (post-MVP: in-app purchase).
- No se puede cerrar el dialog sin hacer acción (upgrade o "más tarde").

### BR-MOB-09: Disclaimer Visible en Vista del Plan
- La vista del plan siempre muestra el disclaimer al final.
- El disclaimer no se puede ocultar ni desplazar fuera de la pantalla.
- Es parte del diseño, no una alerta dismissable.

### BR-MOB-10: Soporte iOS 15+ / Android API 26+
- La app requiere iOS 15.0 o superior.
- La app requiere Android API 26 (Android 8.0) o superior.
- Estas son las versiones mínimas para flutter_secure_storage y otras dependencias.
