# Requisito: Exportación PDF y Compartir Plan

## Problema que resuelve
El owner necesita compartir el plan nutricional aprobado con otros miembros de la familia, cuidadores, o llevarlo impreso a la consulta veterinaria. Sin exportación, el plan solo es accesible dentro de la app.

## Usuarios afectados
- [x] Owner (descarga y comparte el plan)
- [x] Vet (puede exportar el plan aprobado para el expediente clínico)

## Motivación clínica
Un plan nutricional en formato PDF con apariencia de informe veterinario profesional aumenta la adherencia del owner al tratamiento y facilita la comunicación con otros profesionales de salud animal.

## Comportamientos esperados

```gherkin
Scenario: Owner descarga plan activo como PDF
  Given el plan está en estado "ACTIVE"
  When el owner selecciona "Descargar PDF"
  Then el sistema genera un PDF con formato de informe veterinario
  And el PDF incluye el disclaimer en la primera página
  And el PDF incluye: nombre mascota, especie, raza, DER, ingredientes, porciones, instrucciones

Scenario: Owner comparte plan por WhatsApp
  Given el plan está en estado "ACTIVE"
  When el owner selecciona "Compartir" → "WhatsApp"
  Then el sistema abre WhatsApp con el PDF adjunto listo para enviar

Scenario: Plan PENDING_VET no es exportable
  Given el plan está en estado "PENDING_VET"
  When el owner intenta exportar
  Then el sistema muestra "Tu plan está en revisión veterinaria — podrás descargarlo cuando sea aprobado"
```

## Criterios de aceptación
- [ ] PDF generado en < 5 segundos para planes estándar.
- [ ] PDF incluye disclaimer en primera página (INV-37).
- [ ] PDF tiene aspecto de informe veterinario profesional (logo NutriVet.IA, tipografía legible, secciones claras).
- [ ] Compartir disponible para: WhatsApp, Telegram, correo electrónico, y "Copiar enlace" (link temporal 72h).
- [ ] Solo planes `ACTIVE` son exportables (INV-36).
- [ ] El PDF NO incluye datos sensibles del owner (solo nombre de la mascota y datos nutricionales).

## Lo que NO incluye
- Generación de PDF para planes en PENDING_VET, UNDER_REVIEW o ARCHIVED.
- Impresión directa desde la app (el owner imprime desde su dispositivo después de descargar).
- Sincronización con sistemas veterinarios externos (fuera del scope del MVP).

## Referencia PRD
Sección: Funcionalidades del plan nutricional — Exportación y compartición.

## Impacto en arquitectura
- Backend: endpoint `POST /api/v1/plans/{plan_id}/export` → genera PDF con WeasyPrint o ReportLab.
- Frontend (Flutter): `Share` plugin para WhatsApp/Telegram/email. Deep link temporal para "Copiar enlace".
- Solo planes `ACTIVE` responden al endpoint — los demás retornan 403.
