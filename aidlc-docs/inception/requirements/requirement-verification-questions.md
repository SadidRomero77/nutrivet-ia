# Requirement Verification Questions — NutriVet.IA

**Generado**: 2026-03-10 | **Modo**: Brownfield | **Framework**: AI-DLC awslabs

Completa cada `[Answer]:` y confirma cuando termines.
Opciones múltiples: escribe la letra. "X" = otra opción, descríbela después del tag.

---

## SECCIÓN A — Ya Decidido (referencia)

Estos temas NO requieren respuesta — están resueltos en la documentación existente.

| Tema | Decisión | Fuente |
|------|----------|--------|
| Stack tecnológico | Python+FastAPI / Flutter / LangGraph / PostgreSQL / Hetzner+Coolify (ver ADR-022) | `CLAUDE.md` |
| Perfil mascota | 13 campos obligatorios + wizard 6 pasos | `domain/aggregates/pet-profile.md` |
| Condiciones médicas | 13 condiciones soportadas hard-coded | `domain/invariants.md` |
| LLM Routing | 0 cond→Ollama / 1-2→Groq / 3+→GPT-4o / OCR→Qwen-VL local | `decisions/ADR-013` |
| HITL | Solo mascotas con condición médica → PENDING_VET | `domain/invariants.md` INV-09 |
| Plan states | PENDING_VET → ACTIVE → UNDER_REVIEW → ARCHIVED | `domain/aggregates/nutrition-plan.md` |
| Freemium | Free/Básico/Premium/Vet con límites definidos | `CLAUDE.md` |
| OCR | Solo tabla nutricional o ingredientes, nunca logos | `decisions/ADR-010` |
| Tallas perro | 5 categorías MINI/S/M/L/XL con rangos kg | `decisions/ADR-014` |
| Actividad gatos | indoor/indoor_outdoor/outdoor | `decisions/ADR-015` |
| Estado reproductivo | esterilizado/no_esterilizado | `domain/aggregates/pet-profile.md` |
| PDF export | Solo planes ACTIVE, con disclaimer | `decisions/ADR-017` |
| Sin estado RECHAZADO | Vet edita+aprueba o devuelve con comentario | `decisions/ADR-016` |

---

## SECCIÓN B — Preguntas Abiertas

---

### BLOQUE 1 — Gestión de Veterinarios

---

## Q-01: ¿Cómo se conecta un owner con un veterinario en la plataforma?

A) El owner busca y selecciona un vet del directorio de la plataforma (marketplace de vets)
B) El owner ingresa un código de clínica que le da el vet (modelo invitación)
C) La plataforma asigna automáticamente el vet disponible más cercano
D) El owner registra el email de su vet y la plataforma lo invita a crear cuenta
X) Otra — describe después del [Answer]:

[Answer]: X — Modelo por fases:
- MVP: Vet de plataforma único (Lady Carolina) — todos los planes con condición médica van a ella automáticamente. El owner no selecciona vet.
- v1.1: Código de clínica — el vet registrado entrega un código a sus clientes. Owner lo ingresa en el wizard para vincularse. Si no tiene código → fallback al vet de plataforma.
- v2: Marketplace con búsqueda por ciudad/especialidad.

---

## Q-02: ¿Puede un owner tener más de un vet asignado?

A) No — un owner tiene exactamente un vet asignado a todas sus mascotas
B) Sí — cada mascota puede tener un vet diferente
C) Sí — el owner puede tener un vet primario y uno de respaldo
X) Otra

[Answer]: B — Cada mascota puede tener un vet diferente. Un owner con 3 mascotas puede tener cada una en una clínica distinta. Si la mascota no tiene vet asignado → vet de plataforma como fallback.

---

## Q-03: ¿Qué pasa si el owner no tiene vet y su mascota tiene condición médica?

A) El sistema bloquea la generación del plan hasta que el owner asigne un vet
B) El plan se genera y queda en PENDING_VET indefinido — el owner gestiona el vet por fuera
C) La plataforma ofrece un servicio de vet on-demand (vet de guardia en la plataforma)
D) El owner puede continuar con una advertencia y el plan se activa después de 72h sin respuesta del vet
X) Otra

[Answer]: X — El plan se genera y va automáticamente al VET DE PLATAFORMA (Lady Carolina en MVP). El owner recibe notificación: "Tu plan será revisado por nuestro equipo clínico". El vet de plataforma actúa como safety net clínico siempre activo.

---

## Q-04: ¿El vet paga por usar la plataforma o recibe un beneficio económico?

A) El vet paga suscripción ($89.000 COP/mes tier Vet) — acceso completo
B) El vet no paga — recibe ingresos por cobrarle al owner directamente fuera de la app
C) El vet recibe una comisión por cada plan aprobado dentro de la plataforma
D) Modelo mixto — suscripción Vet con comisión por planes de condición médica
X) Otra

[Answer]: X — Modelo por niveles:
- Vet FREE: Revisar planes de owners (hasta 10/mes). Sin ClinicPets. Sin dashboard. Para adopción inicial.
- Vet BÁSICO ($89.000 COP/mes): Revisiones ilimitadas + crear ClinicPets + dashboard clínico + compartir PDF + invitar propietarios.
- Vet CLÍNICA (precio a negociar): Múltiples vets bajo una clínica, facturación unificada, vista consolidada.
- MVP: Lady Carolina tiene Vet BÁSICO proporcionado por la plataforma (sin costo para ella).

FEATURE ADICIONAL APROBADA — Vet como creador de planes (ClinicPet):
- El vet puede crear perfiles de pacientes cuyos propietarios no tienen app.
- El vet ingresa los 13 campos del wizard directamente.
- El plan generado es aprobado directamente por el vet (sin PENDING_VET — él es el aprobador).
- El vet comparte el PDF por WhatsApp/email desde su dashboard.
- Si el propietario descarga la app después → puede reclamar su mascota con un código → ClinicPet se convierte en AppPet con historial completo.
- Ver ADR-018.

---

### BLOQUE 2 — Dashboard de Seguimiento del Owner

---

## Q-05: ¿Cómo registra el owner el seguimiento del peso de su mascota?

A) El owner ingresa el peso manualmente cada vez que quiere registrar
B) El sistema envía recordatorio periódico (ej. cada 2 semanas) para registrar peso
C) El owner hace check-in diario con un registro simple (bien / regular / mal)
D) Solo se registra cuando el owner genera un nuevo plan
X) Otra

[Answer]: A + D — El peso se registra de dos formas: (1) el owner lo ingresa manualmente en cualquier momento desde el perfil de la mascota; (2) al generar un nuevo plan, el wizard solicita el peso actual y lo actualiza automáticamente. Sin recordatorios push en el MVP — el owner decide cuándo registrar fuera del flujo de plan.

---

## Q-06: ¿Qué métricas muestra el dashboard de seguimiento?

A) Solo peso y BCS a lo largo del tiempo (gráfica simple)
B) Peso + BCS + duración del plan + estado del plan actual
C) Peso + BCS + adherencia al plan (¿cuántos días siguió el plan?) + historial de consultas al agente
D) Dashboard completo: peso, BCS, adherencia, historial de planes, alertas, próximas revisiones
X) Otra

[Answer]: B — Peso + BCS a lo largo del tiempo (gráfica) + duración del plan actual + estado del plan (ACTIVE / PENDING_VET / UNDER_REVIEW). Dashboard simple para el MVP. Adherencia e historial de planes van en v2.

---

## Q-07: ¿El vet tiene acceso al dashboard de seguimiento del owner?

A) Sí — el vet ve el historial completo de todas sus mascotas pacientes
B) Sí — pero solo cuando el owner comparte explícitamente
C) Solo para mascotas con condición médica activa
D) No — el vet solo ve los planes para aprobar
X) Otra

[Answer]: A — El vet ve el historial completo de todas sus mascotas pacientes (peso, BCS, estado del plan, duración). Esto refuerza el valor del tier Vet BÁSICO y del dashboard clínico. El vet solo ve pacientes vinculados a él — no puede ver pacientes de otros vets.

---

### BLOQUE 3 — Comportamiento Offline (Flutter)

---

## Q-08: ¿Qué funcionalidades deben estar disponibles sin conexión a internet?

A) Solo visualización del plan activo (lectura)
B) Visualización del plan + historial de conversaciones anteriores
C) Visualización + registro de peso/BCS + notas del owner
D) Todo excepto generación de nuevo plan y OCR scanner
X) Otra

[Answer]: D — Offline disponible: visualización del plan activo, historial de conversaciones, registro de peso/BCS, perfil de la mascota, dashboard de seguimiento. Solo requieren conexión: generación de nuevo plan y OCR scanner. Implementado con Hive en Flutter.

---

## Q-09: ¿Qué pasa con el agente conversacional sin conexión?

A) No disponible offline — muestra mensaje "Requiere conexión"
B) Responde preguntas básicas con respuestas en caché del historial reciente
C) Funciona con un modelo local pequeño en el dispositivo (on-device LLM)
X) Otra

[Answer]: A — El agente conversacional no está disponible offline. Muestra mensaje claro: "El asistente requiere conexión a internet". El historial de conversaciones anteriores sí es visible (caché Hive), pero no se pueden enviar nuevas consultas.

---

### BLOQUE 4 — Idiomas y Mercado LATAM

---

## Q-10: ¿En qué idiomas estará disponible la app en el lanzamiento?

A) Solo español — toda LATAM usa la misma versión
B) Español (es-CO) como base + inglés para el mercado US latino
C) Español con variantes regionales (es-CO, es-MX, es-AR) en textos de la UI
D) Solo español de Colombia para el piloto — multiidioma en v2
X) Otra

[Answer]: A — Solo español para toda LATAM desde el MVP. Mismo texto para todos los países — sin variantes regionales en UI. Multiidioma (inglés u otros) va en v2.

---

## Q-11: ¿La base de datos de alimentos cubre toda LATAM desde el día 1?

A) Sí — base LATAM completa con aliases regionales desde el MVP
B) No — Colombia primero en el MVP, se expande con retroalimentación de usuarios
C) LATAM en contenido pero Colombia-first en priorización de ingredientes del plan
X) Otra

[Answer]: X — DB con nombre canónico + nombre científico por alimento. El LLM agrega el alias regional entre paréntesis según el país del usuario. Formato en output/PDF: "Calabaza amarilla (Ahuyama)". Simple, con trazabilidad y sin mantenimiento de tablas de aliases.

---

### BLOQUE 5 — Performance y Disponibilidad (NFRs)

---

## Q-12: ¿Cuál es el tiempo máximo aceptable para generación de un plan?

A) 30 segundos (límite actual en RUNBOOK.md)
B) 20 segundos — experiencia más fluida
C) 60 segundos aceptable si hay indicador de progreso claro en la UI
D) Diferenciado: mascota sana < 20s / con condición médica < 60s
X) Otra

[Answer]: C — 60 segundos máximo con indicador de progreso visible en la UI. Se prioriza calidad del plan sobre velocidad — el LLM debe tener tiempo para razonamiento/thinking que evite alucinaciones. El indicador de progreso gestiona la percepción del usuario durante la espera.

---

## Q-13: ¿Cuál es el uptime objetivo para producción?

A) 99.5% (~3.6h downtime/mes) — aceptable para MVP
B) 99.9% (~43min downtime/mes) — objetivo estándar
C) 99.0% (~7.2h downtime/mes) — suficiente para piloto BAMPYSVET
X) Otra

[Answer]: B — 99.9% (~43min downtime/mes). Objetivo estándar de producción — adecuado para una app de salud donde la continuidad importa.

---

## Q-14: ¿Dónde deben residir los datos de los usuarios?

A) AWS us-east-1 (N. Virginia) — más barato, latencia aceptable desde LATAM
B) AWS sa-east-1 (São Paulo) — más cercano a LATAM, cumple algunas regulaciones locales
C) AWS us-east-1 con réplica en sa-east-1 para DR
D) Indiferente para el MVP — optimizar en v2
X) Otra

[Answer]: B — AWS sa-east-1 (São Paulo). Menor latencia para usuarios LATAM, cumple requisitos de residencia de datos de Colombia (Ley 1581/2012) y Brasil (LGPD). Favorece la expansión regional.

---

### BLOQUE 6 — Repositorio y Desarrollo

---

## Q-15: ¿Monorepo o repositorios separados para backend y mobile?

A) Monorepo — backend/ y mobile/ en el mismo repositorio
B) Dos repos separados — uno para backend (Python), uno para mobile (Flutter)
C) Tres repos — backend, mobile, y docs/specs separados
X) Otra

[Answer]: A — Monorepo. backend/ y mobile/ en el mismo repositorio con path filtering en GitHub Actions (cambios en backend/** solo disparan pipeline de backend, mobile/** solo el de mobile). Simplifica coordinación de cambios de API, CI/CD y gestión para equipo pequeño.

---

## Q-16: ¿Cómo se manejan los pagos en la plataforma?

A) Stripe — estándar internacional, disponible en Colombia
B) PayU — líder en Colombia y LATAM
C) MercadoPago — fuerte en Argentina, México, Colombia
D) Sin pagos en el MVP — el upgrade se gestiona manualmente (email/WhatsApp al equipo)
X) Otra

[Answer]: B — PayU. Líder en Colombia y LATAM, soporte PSE (pagos bancarios Colombia), tarjetas crédito/débito y efectivo (Efecty). Mejor opción para el mercado objetivo.

---

### BLOQUE 7 — Ajustes Post-Aprobación del Plan

---

## Q-17: Cuando el owner ajusta un ingrediente del plan (ej. cambia pollo por pavo), ¿requiere re-revisión del vet?

A) No — el owner puede hacer ajustes menores libremente sin re-aprobación
B) Sí siempre — cualquier cambio en plan con condición médica vuelve a PENDING_VET
C) Depende: cambios de ingrediente equivalente NO requieren re-revisión; cambios estructurales SÍ
D) El agente clasifica el cambio y decide si notificar al vet o no
X) Otra

[Answer]: D + X — Flujo en tres capas:

**Capa 1 — Agente como filtro automático:**
- Sin condición médica + ingrediente equivalente → agente permite el cambio directamente, sin vet.
- Con condición médica + ingrediente incompatible → agente bloquea, explica el motivo y ofrece alternativas seguras.

**Capa 2 — Agente como consejero:**
- Si el owner insiste en otro ingrediente, el agente presenta alternativas validadas contra las restricciones de la condición médica.
- Si el owner elige una alternativa fuera del set pre-aprobado → el cambio vuelve a PENDING_VET.

**Capa 3 — Set de sustitutos generado por el agente al crear el plan:**
- Al generar el plan inicial, el agente produce automáticamente un set de ingredientes sustitutos válidos para cada ingrediente principal, validados contra las restricciones y condiciones de la mascota.
- El vet, al revisar el plan en PENDING_VET, solo valida que los sustitutos sean clínicamente viables. Si alguno no lo es, el vet solicita al agente un nuevo set — no los define él manualmente.
- Una vez aprobados, el owner puede intercambiar libremente dentro del set pre-aprobado sin reproceso ni intervención del vet.

---

## Q-18: ¿El owner puede pausar un plan activo (ej. vacaciones, enfermedad)?

A) No — el plan siempre está activo hasta que se genera uno nuevo o expira
B) Sí — puede pausarlo y reanudarlo sin afectar la fecha de expiración
C) Sí — pero la pausa extiende automáticamente la fecha de review_date
X) Otra

[Answer]: A — El plan no se pausa. Permanece ACTIVE hasta que el owner genera un nuevo plan o el vet define una fecha de review_date que lo mueve a UNDER_REVIEW. Sin estado de pausa en el MVP.

---

### BLOQUE 8 — Notificaciones

---

## Q-19: ¿Por qué canales se envían las notificaciones?

A) Solo push notifications (FCM — iOS/Android)
B) Push notifications + email
C) Push + email + WhatsApp Business API
D) Solo push para el MVP — ampliar canales en v2
X) Otra

[Answer]: B — Push notifications (FCM) + email. WhatsApp Business API queda para v2.

---

## Q-20: ¿Qué eventos disparan notificación al owner?

Marca todos los que aplican (ej: "A, C, E"):

A) Plan aprobado por el vet → "Tu plan está listo"
B) Plan próximo a expirar (7 días antes) → "Tu plan vence en 7 días"
C) Recordatorio de registro de peso (configurable por el owner)
D) Nueva función disponible en la app (marketing)
E) Agente tiene una recomendación proactiva basada en el seguimiento
F) El vet devolvió el plan con comentario → "Tu vet tiene observaciones"
X) Otros eventos — describe

[Answer]: A, B, D — Eventos del MVP:
- A: Plan aprobado por el vet → "Tu plan está listo"
- B: Plan próximo a expirar (7 días antes) → "Tu plan vence en 7 días"
- D: Nueva función disponible (marketing push)
Recordatorios de peso, recomendaciones proactivas del agente y notificación de devolución del vet van en v2.

---

### BLOQUE 9 — Seguridad y Privacidad

---

## Q-21: ¿La app requiere cumplimiento con regulación de pagos (PCI-DSS)?

A) Sí — si manejamos pagos con tarjeta directamente en la app
B) No — usamos un proveedor de pagos certificado (Stripe/PayU/MercadoPago) que maneja PCI
C) No aplica en el MVP — no hay pagos en la primera versión
X) Otra

[Answer]: C + X — Sin pagos en el MVP (upgrade gestionado manualmente). Para v2: pagos con tarjeta directamente en la app usando el SDK nativo de PayU para Flutter — el SDK tokeniza la tarjeta en el dispositivo antes de enviarla, la app nunca toca datos de tarjeta en crudo. PayU mantiene la certificación PCI-DSS, nosotros solo operamos con tokens. Módulo de pagos diseñado como servicio independiente desde el inicio para facilitar integración en v2.

---

## Q-22: ¿Los datos médicos de las mascotas requieren consentimiento explícito adicional al registro?

A) El consentimiento de registro cubre todo — términos y condiciones al crear cuenta
B) Sí — consentimiento separado para datos médicos antes de registrar condiciones
C) Sí — consentimiento separado Y posibilidad de exportar/eliminar datos médicos en cualquier momento
X) Otra

[Answer]: B — Consentimiento separado para datos médicos. Antes de registrar condiciones médicas en el wizard, se muestra pantalla de consentimiento explícito (Ley 1581/2012 Colombia). El consentimiento de registro general no cubre datos de salud. Exportación/eliminación de datos médicos va en v2.

---

### BLOQUE 10 — Scope del MVP

---

## Q-23: ¿Cuáles features son obligatorias para el lanzamiento del piloto en BAMPYSVET?

Marca las que son BLOQUEANTES para el piloto (sin estas no se puede lanzar):

A) Generación de plan nutricional (Natural y Concentrado)
B) HITL con revisión veterinaria
C) Agente conversacional
D) OCR scanner de etiquetas
E) Exportación PDF
F) Dashboard de seguimiento con gráfica de peso
G) Sistema de notificaciones push
H) Pagos y subscripciones (freemium completo)
I) Compartir plan por WhatsApp/Telegram

[Answer]: A, B, C, D, E, F, G, H, I — Todas las features son bloqueantes para el piloto BAMPYSVET. Sin alguna de ellas no se puede lanzar.

---

## Q-24: ¿Hay algún requisito que no está cubierto en las preguntas anteriores?

Describe cualquier funcionalidad, restricción o decisión que consideres importante y que no fue preguntada arriba.

[Answer]: Todos los requisitos están cubiertos en las preguntas anteriores.

---

**Cuando hayas completado todas las respuestas, regresa aquí y escribe: "Preguntas completadas"**
