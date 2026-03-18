# Plan: NFR Requirements — Unit 09: mobile-app

**Unidad**: unit-09-mobile-app
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del mobile-app

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| App startup (cold start) | < 2s | Flutter AOT compiled |
| ChatScreen: primer token visible | < 1s | SSE streaming — StreamBuilder |
| PlanScreen: plan desde Hive cache | < 100ms | Lectura offline de Hive box |
| WizardScreen: paso navigation | < 100ms | Solo state update local |
| Plan polling: response en pantalla | < 3s por poll | GET job_id cada 3s |
| Plan polling: timeout total | 60s (20 intentos) | Barra de progreso visible |
| OCR result display | < 25s | Upload + gpt-4o + evaluación |

### Offline-First

**Plan y chat DEBEN ser legibles sin red**:
- `PlanNotifier`: si no hay red → servir desde `plan_box` de Hive.
- `ChatNotifier`: si no hay red → mostrar historial local de `chat_box`.
- Nuevos mensajes y nuevos planes REQUIEREN red → indicador visual de "sin conexión".

**Wizard draft**:
- Guardado automáticamente en `wizard_box` en cada cambio de step.
- Si usuario cierra app y vuelve → wizard retoma desde el paso donde quedó.
- Draft se elimina al completar exitosamente el wizard.

### Seguridad

**JWT tokens en flutter_secure_storage**:
- Access token y refresh token almacenados en `flutter_secure_storage` (AES-256 en dispositivo).
- Nunca en SharedPreferences ni en Hive no-encriptado.

**Refresh automático via Dio interceptor**:
- El interceptor captura 401, ejecuta refresh automáticamente, reintenta el request original.
- Transparente para el usuario — no ve ni un parpadeo.
- Si el refresh falla → logout automático → AuthScreen.

**Hive boxes por feature**:
- `auth_box`: encriptado (flutter_secure_storage como kms).
- `wizard_box`, `plan_box`, `chat_box`, `weight_box`: cajas separadas por feature.
- Datos médicos en Hive: no encriptar localmente (ya encriptados en backend) — ok.

### UX — Guías de Cámara (OCR)

- Overlay de guía en OCRScreen: borde rectangular con instrucción clara.
- La app no envía la imagen hasta que el usuario confirma.
- Mensaje de rechazo claro si imagen es frontal/logo.

### Mantenibilidad

- Effective Dart style.
- Cobertura mínima: widget tests para las 7 interacciones críticas.
- No hay cobertura mínima % definida para Flutter — pero los 7 widget tests son obligatorios.
- Integration test: flujo completo registro → wizard → plan → chat.

## Checklist NFR mobile-app

- [ ] App cold start < 2s (medido en dispositivo físico)
- [ ] JWT en flutter_secure_storage (verificar, no SharedPreferences)
- [ ] Refresh interceptor: 401 → refresh → retry transparente
- [ ] Plan legible offline (Hive) — test en modo avión
- [ ] Chat historial legible offline — test en modo avión
- [ ] Wizard draft persiste entre sesiones (cerrar y reabrir app)
- [ ] talla oculta para gatos en wizard (widget test)
- [ ] SSE StreamBuilder muestra tokens progressivamente
- [ ] Free quota counter visible en ChatScreen
- [ ] UpgradeGateScreen modal aparece al agotar cuota
- [ ] PENDING_VET primero en VetDashboard (widget test)
- [ ] Vet: botón Devolver deshabilitado si comentario vacío

## Referencias

- Global: `_shared/nfr-requirements.md`
- Unit spec: `inception/units/unit-09-mobile-app.md`
- ADR-021: SSE streaming
- Constitution: REGLA 8 (disclaimer en toda vista del plan)
