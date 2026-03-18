# Requirement Clarification Questions — NutriVet.IA

**Fase AI-DLC**: PASO 1 — Requirements Analysis
**Estado**: ✅ Respondido — todas las preguntas resueltas
**Fecha**: 2026-03-10

Este archivo documenta preguntas de clarificación menores identificadas durante
el análisis de requisitos, junto con sus respuestas.

---

## Q-1: Estrategia de Repositorio

**Pregunta**: ¿Monorepo o multi-repo para backend + mobile?

**Contexto**: Afecta la estructura del repositorio GitHub, CI/CD, y la organización del equipo.

A) Monorepo — un solo repositorio `nutrivet-ai/` con `backend/` y `mobile/`
B) Multi-repo — repos separados
C) Monorepo con workspaces

**[Answer]**: A — Monorepo. Equipo pequeño (2 personas), facilita correlación de cambios.

---

## Q-2: Ajuste de Plan Post-Aprobación

**Pregunta**: Si el owner ajusta un ingrediente dentro del set pre-aprobado, ¿requiere re-revisión del vet?

A) No — ajuste dentro del set → plan permanece ACTIVE
B) Sí — cualquier cambio requiere re-revisión
C) Depende de la condición médica de la mascota

**[Answer]**: A — Ajuste dentro del set pre-aprobado → permanece ACTIVE. Ajuste fuera del set → PENDING_VET.

---

## Q-3: Notificaciones Push

**Pregunta**: ¿Qué canales de notificación se implementan en el MVP?

A) Solo push (FCM)
B) Push + email
C) Push + email + WhatsApp

**[Answer]**: B — Push (FCM) + email (Resend). WhatsApp es phase 2.

---

## Q-4: Internacionalización de Idioma

**Pregunta**: ¿La app soporta múltiples idiomas en el MVP?

A) Solo español (Colombia first)
B) Español + Inglés
C) Español + aliased por país (CO/MX/AR/PE)

**[Answer]**: A — Solo español para MVP. La base de alimentos incluye aliases regionales (ahuyama/zapallo/calabaza) pero la UI es solo español.

---

## Q-5: Data Residency

**Pregunta**: ¿Dónde residen los datos de usuarios colombianos?

A) Hetzner Ashburn VA (USA) — simplificación inicial
B) Hetzner Nuremberg (EU) — GDPR-friendly
C) Servidor en Colombia (no disponible en Hetzner)

**[Answer]**: A — Ashburn VA para MVP. Cumplimiento Ley 1581 Colombia mediante política de privacidad y consentimiento explícito. Revisitar si expansión a EU.

---

## Q-6: Política de Datos

**Pregunta**: ¿Retención y eliminación de datos del owner?

A) Retención indefinida
B) Retención 2 años, luego archivado
C) Eliminación por solicitud del usuario (right to be forgotten)

**[Answer]**: C — GDPR/Ley 1581 compliant. Usuario puede solicitar eliminación de cuenta. Retención de agent_traces anonimizados por 90 días (compliance).

---

## Q-7: Modelo de Negocio Vet

**Pregunta**: ¿Cómo paga el vet su suscripción?

A) Pago mensual por suscripción plana ($89.000 COP/mes)
B) Pago por plan revisado ($X por revisión)
C) Freemium con upgrade cuando supera N pacientes

**[Answer]**: A — Suscripción plana $89.000 COP/mes. Ilimitados pacientes y planes.

---

## Q-8: Offline — Qué Funciona Sin Conexión

**Pregunta**: ¿Qué features deben funcionar offline en la app móvil?

A) Solo lectura del plan activo
B) Lectura del plan + historial de chat (últimas 50 conversaciones)
C) Lectura + escritura (mensajes se envían cuando hay conexión)

**[Answer]**: B — Lectura offline: plan activo, historial chat (50), dashboard (último sync). Wizard en progreso guardado en Hive (no enviado hasta completar). Chat requiere conexión para responder.

---

## Q-9: BCS Visual

**Pregunta**: ¿Cómo se implementa el selector visual de BCS?

A) Imágenes estáticas de siluetas 1-9 en assets del app
B) Ilustraciones vectoriales (SVG)
C) Fotos reales de perros/gatos

**[Answer]**: A — Imágenes estáticas de siluetas incluidas en assets Flutter. Lady Carolina provee las imágenes de referencia (BCS escala 1-9, separadas por especie).

---

## Estado de Resolución

Todas las 9 preguntas están resueltas. Los requisitos están completamente especificados en:
- `specs/prd.md` (PRD v2.0)
- `inception/requirements/requirements.md`
- ADRs correspondientes en `decisions/`
