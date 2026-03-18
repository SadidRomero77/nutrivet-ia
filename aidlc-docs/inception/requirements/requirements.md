# Requirements — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10
**Estado**: Aprobado — Gate 1 ✅
**Fuente**: requirement-verification-questions.md (Q-01 a Q-24) + documentación brownfield existente

---

## 1. Requisitos Funcionales

### 1.1 Gestión de Veterinarios

**RF-01 — Conexión owner-vet (por fases)**
- **MVP**: Un único vet de plataforma (Lady Carolina) recibe automáticamente todos los planes con condición médica. El owner no selecciona vet.
- **v1.1**: El vet registrado entrega un código de clínica a sus clientes. El owner lo ingresa en el wizard para vincularse. Sin código → fallback al vet de plataforma.
- **v2**: Marketplace con búsqueda por ciudad/especialidad.

**RF-02 — Vet por mascota**
- Cada mascota puede tener un vet diferente.
- Un owner con múltiples mascotas puede tener cada una vinculada a una clínica distinta.
- Si la mascota no tiene vet asignado → vet de plataforma como fallback automático.

**RF-03 — Safety net clínico**
- El vet de plataforma actúa como receptor de todos los planes sin vet asignado.
- El owner recibe notificación: "Tu plan será revisado por nuestro equipo clínico".
- El vet de plataforma también recibe overflow de vets FREE que superan su límite mensual y de vets que cancelaron suscripción.

**RF-04 — Modelo de suscripción vet**

| Tier | Costo | Capacidades |
|------|-------|-------------|
| Vet FREE | $0 | Revisar planes de owners (máx 10/mes). Sin ClinicPets. Sin dashboard. |
| Vet BÁSICO | $89.000 COP/mes | Revisiones ilimitadas + ClinicPets + dashboard clínico + PDF + invitaciones |
| Vet CLÍNICA | A negociar | Multi-vet + facturación unificada + vista consolidada |

- MVP: Lady Carolina tiene Vet BÁSICO sin costo.

**RF-05 — ClinicPet (vet como creador de planes)**
- El vet puede crear perfiles de pacientes cuyos propietarios no tienen app (ClinicPet).
- El vet ingresa los 13 campos del wizard directamente desde su dashboard.
- El plan generado es aprobado directamente por el vet sin pasar por PENDING_VET.
- El vet comparte el PDF por WhatsApp/email desde su dashboard.
- Si el propietario descarga la app posteriormente → puede reclamar la mascota con un código de reclamación → ClinicPet se convierte en AppPet con historial completo preservado.
- Referencia: ADR-018.

---

### 1.2 Dashboard de Seguimiento del Owner

**RF-06 — Registro de peso**
- El owner puede ingresar el peso de su mascota manualmente en cualquier momento desde el perfil.
- Al generar un nuevo plan, el wizard solicita el peso actual y lo actualiza automáticamente.
- Sin recordatorios push de peso en el MVP.

**RF-07 — Métricas del dashboard (MVP)**
- Gráfica de peso a lo largo del tiempo.
- Gráfica de BCS a lo largo del tiempo.
- Duración del plan activo.
- Estado actual del plan (ACTIVE / PENDING_VET / UNDER_REVIEW).
- Adherencia, historial de planes y alertas van en v2.

**RF-08 — Acceso del vet al dashboard**
- El vet ve el historial completo de seguimiento (peso, BCS, estado del plan, duración) de todas sus mascotas pacientes vinculadas.
- El vet no puede ver pacientes vinculados a otros vets.
- Este acceso forma parte del valor del tier Vet BÁSICO.

---

### 1.3 Comportamiento Offline

**RF-09 — Funcionalidades offline (Hive Flutter)**

Disponible sin conexión:
- Visualización del plan activo
- Historial de conversaciones anteriores (solo lectura)
- Registro de peso/BCS
- Perfil de la mascota
- Dashboard de seguimiento

Requiere conexión obligatoriamente:
- Generación de nuevo plan
- OCR scanner de etiquetas

**RF-10 — Agente conversacional offline**
- No disponible offline.
- Muestra mensaje claro: "El asistente requiere conexión a internet".
- El historial de conversaciones previas es visible en caché pero no se pueden enviar nuevas consultas.

---

### 1.4 Idiomas y Alimentos

**RF-11 — Idioma de la app**
- Solo español para toda LATAM desde el MVP.
- Un único texto sin variantes regionales en la UI.
- Multiidioma (inglés u otros) va en v2.

**RF-12 — Base de datos de alimentos y regionalización**
- Cada alimento tiene un `nombre_canónico` (nombre común estándar) y un `nombre_científico`.
- Un único registro por alimento en la DB — sin aliases en la tabla principal.
- El LLM agrega el alias regional entre paréntesis en el output según el `country` del perfil del usuario.
- Formato en planes y PDF: `"Calabaza amarilla (Ahuyama)"`.
- El agente puede orientar al usuario usando el nombre regional que conoce (ej. "en Colombia la ahuyama es lo que en el plan llamamos calabaza amarilla").

---

### 1.5 Ajustes Post-Aprobación del Plan

**RF-13 — Modificación de ingredientes (flujo en tres capas)**

**Capa 1 — Filtro automático del agente:**
- Sin condición médica + ingrediente equivalente → el agente permite el cambio directamente, sin vet.
- Con condición médica + ingrediente incompatible → el agente bloquea, explica el motivo y ofrece alternativas seguras.

**Capa 2 — Agente como consejero:**
- Si el owner insiste en un ingrediente diferente, el agente presenta alternativas validadas contra las restricciones de la condición médica del perfil.
- Si el owner elige una alternativa fuera del set pre-aprobado → el cambio vuelve a PENDING_VET.

**Capa 3 — Set de sustitutos pre-aprobados:**
- Al generar el plan inicial, el agente produce automáticamente un set de ingredientes sustitutos válidos para cada ingrediente principal, validados contra restricciones y condiciones de la mascota.
- El vet, al revisar en PENDING_VET, valida que los sustitutos sean clínicamente viables. Si alguno no lo es, solicita al agente un nuevo set.
- Una vez aprobado el set, el owner puede intercambiar libremente dentro de él sin reproceso.

**RF-14 — Sin estado de pausa de plan**
- El plan no tiene estado de pausa.
- Permanece ACTIVE hasta que el owner genera un nuevo plan o el vet define un `review_date` que lo mueve a UNDER_REVIEW.

---

### 1.6 Notificaciones

**RF-15 — Canales de notificación (MVP)**
- Push notifications via FCM (iOS + Android).
- Email.
- WhatsApp Business API va en v2.

**RF-16 — Eventos de notificación al owner (MVP)**
- Plan aprobado por el vet → "Tu plan está listo"
- Plan próximo a expirar (7 días antes) → "Tu plan vence en 7 días"
- Nueva función disponible en la app (marketing)

En v2: recordatorios de peso, recomendaciones proactivas del agente, notificación de devolución del vet con comentario.

---

### 1.7 Pagos y Suscripciones

**RF-17 — Modelo de pagos por fases**
- **MVP**: Sin pagos en la app. El upgrade de tier se gestiona manualmente (email/WhatsApp al equipo).
- **v2**: Pagos con tarjeta directamente en la app usando el SDK nativo de PayU para Flutter. El SDK tokeniza la tarjeta en el dispositivo — la app nunca toca datos de tarjeta en crudo. PayU mantiene la certificación PCI-DSS.
- El módulo de pagos se diseña como servicio independiente desde el inicio para facilitar la integración en v2.
- Proveedor: PayU (líder en Colombia y LATAM, soporte PSE, Efecty, tarjetas crédito/débito).

---

### 1.8 Seguridad y Privacidad

**RF-18 — Consentimiento para datos médicos**
- El consentimiento de registro general (T&C) no cubre datos de salud.
- Antes de registrar condiciones médicas en el wizard, se muestra una pantalla de consentimiento explícito separado (Ley 1581/2012 Colombia).
- Exportación y eliminación de datos médicos va en v2.

---

### 1.9 Scope del MVP — Features Bloqueantes

Todas las siguientes features son obligatorias para el lanzamiento del piloto en BAMPYSVET:

| Feature | Descripción |
|---------|-------------|
| Generación de plan | Plan Natural y Concentrado para perros y gatos |
| HITL veterinario | Revisión y firma de planes con condición médica |
| Agente conversacional | Consultas nutricionales + límites freemium |
| OCR scanner | Lectura de tabla nutricional e ingredientes |
| Exportación PDF | Solo planes ACTIVE con disclaimer |
| Dashboard de seguimiento | Gráfica peso/BCS + estado del plan |
| Notificaciones | Push (FCM) + email para eventos MVP |
| Freemium completo | Free/Básico/Premium/Vet con sus límites |
| Compartir plan | WhatsApp/Telegram/email desde el plan activo |

---

## 2. Requisitos No Funcionales

### 2.1 Performance

| Requisito | Valor |
|-----------|-------|
| Tiempo máximo generación de plan | 60 segundos |
| Indicador de progreso | Obligatorio durante generación de plan |
| Justificación | El LLM debe tener tiempo de razonamiento/thinking para evitar alucinaciones |

### 2.2 Disponibilidad

| Requisito | Valor |
|-----------|-------|
| Uptime objetivo | 99.9% (~43 min downtime/mes) |
| Clasificación de incidentes | P0: tóxico en plan / HITL omitido · P1: generación > 30s · P2: OCR < 85% |

### 2.3 Infraestructura y Datos

| Requisito | Decisión |
|-----------|----------|
| Cloud provider | Hetzner CPX31 (Ashburn VA) + Coolify — ver ADR-022 |
| Región primaria | Ashburn VA (Hetzner) + Cloudflare CDN global |
| Justificación | $13/mes vs ~$190+/mes AWS · sin cold starts · Clean Architecture permite migrar a AWS en 2-3 días si es necesario |
| Base de datos | PostgreSQL 16 (Docker en Hetzner, backups diarios a Cloudflare R2) |
| Almacenamiento PDFs | Cloudflare R2 (S3-compatible, 10GB free/mes) |

### 2.4 Repositorio y CI/CD

| Requisito | Decisión |
|-----------|----------|
| Estructura | Monorepo (backend/ + mobile/ en el mismo repo) |
| CI/CD | GitHub Actions con path filtering por directorio |
| SAST | bandit en cada PR (backend) |
| Dependencias | safety check en cada PR |
| Linter | ruff (Python) + Effective Dart (Flutter) |

### 2.5 Seguridad

- JWT: access tokens 15min + refresh rotativos.
- RBAC: validación de rol en cada endpoint.
- Datos médicos: AES-256 en reposo en PostgreSQL.
- Prompts a LLMs externos: solo IDs anónimos (pet_id), nunca nombres, especie o condición médica.
- Logs: JSON estructurado, sin PII.
- CORS: configurado explícitamente, nunca wildcard en producción.
- HTTPS obligatorio en todos los entornos expuestos.

---

## 3. Decisiones Diferidas (v2)

| Decisión | Versión |
|----------|---------|
| Código de clínica para vinculación vet-owner | v1.1 |
| Marketplace de vets con búsqueda por ciudad | v2 |
| Multiidioma (inglés u otros) | v2 |
| WhatsApp Business API para notificaciones | v2 |
| Recordatorios push de registro de peso | v2 |
| Recomendaciones proactivas del agente | v2 |
| Notificación de devolución del plan con comentario del vet | v2 |
| Exportación/eliminación de datos médicos a petición | v2 |
| Adherencia e historial de planes en dashboard | v2 |
| Pagos en la app (PayU SDK Flutter) | v2 |

---

## 4. Trazabilidad

| Requisito | Fuente |
|-----------|--------|
| RF-01 a RF-05 | Q-01, Q-02, Q-03, Q-04 + ADR-018 |
| RF-06 a RF-08 | Q-05, Q-06, Q-07 |
| RF-09 a RF-10 | Q-08, Q-09 |
| RF-11 a RF-12 | Q-10, Q-11 |
| RF-13 a RF-14 | Q-17, Q-18 |
| RF-15 a RF-16 | Q-19, Q-20 |
| RF-17 | Q-16, Q-21 |
| RF-18 | Q-22 |
| NFR Performance | Q-12 |
| NFR Disponibilidad | Q-13 |
| NFR Infraestructura | Q-14 |
| NFR Repositorio | Q-15 |
| MVP scope | Q-23, Q-24 |
