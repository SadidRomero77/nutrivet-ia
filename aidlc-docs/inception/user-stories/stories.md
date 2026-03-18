# User Stories — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10
**Estado**: Draft — Gate 2 pendiente

---

## Epic 1 — Gestión de Identidad

---

### US-01: Registro de owner

**Como** owner (Valentina / Carolina)
**Quiero** crear una cuenta con email y contraseña
**Para** acceder a la app y registrar a mis mascotas

**Criterios de Aceptación:**
- [ ] El owner puede registrarse con email + contraseña
- [ ] El sistema valida formato de email y contraseña mínimo 8 caracteres
- [ ] Se envía email de confirmación
- [ ] Al confirmar email, el owner accede al onboarding de mascota
- [ ] Un email solo puede tener una cuenta activa

**INVEST Check:**
- Independent: sí — no depende de otras stories
- Negotiable: sí — mecanismo de confirmación puede variar
- Valuable: sí — sin cuenta no hay app
- Estimable: sí — auth estándar
- Small: sí
- Testable: sí — `behaviors/auth.feature`

**Gherkin asociado:** `behaviors/auth.feature` — Scenario: Owner crea cuenta exitosamente
**Prioridad:** CRÍTICA
**Epic:** Epic 1

---

### US-02: Login y sesión

**Como** owner o vet
**Quiero** iniciar sesión con mis credenciales
**Para** acceder a mi dashboard y datos de mis mascotas

**Criterios de Aceptación:**
- [ ] Login con email + contraseña retorna JWT access (15min) + refresh rotativo
- [ ] Refresh token renueva la sesión automáticamente sin pedir contraseña
- [ ] Intento fallido × 5 → bloqueo temporal de 15 minutos
- [ ] El rol (owner / vet) determina la vista que se muestra al entrar

**INVEST Check:**
- Independent: sí
- Negotiable: sí — biometría puede ir en v2
- Valuable: sí — punto de entrada a toda la app
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/auth.feature` — Scenario: Login exitoso con JWT
**Prioridad:** CRÍTICA
**Epic:** Epic 1

---

### US-03: Registro de veterinario

**Como** veterinario (Dr. Andrés / Lady Carolina)
**Quiero** crear una cuenta con mi rol y datos de clínica
**Para** acceder al dashboard clínico y revisar/crear planes

**Criterios de Aceptación:**
- [ ] El vet puede registrarse seleccionando rol "Veterinario"
- [ ] El vet ingresa nombre, email, número de matrícula profesional y clínica
- [ ] El sistema asigna tier Vet FREE por defecto al activar la cuenta
- [ ] El vet de plataforma (Lady Carolina) tiene tier Vet BÁSICO asignado manualmente

**INVEST Check:**
- Independent: sí
- Negotiable: sí — verificación de matrícula puede ser manual en MVP
- Valuable: sí — habilita el flujo HITL
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/auth.feature` — Scenario: Veterinario crea cuenta
**Prioridad:** CRÍTICA
**Epic:** Epic 1

---

## Epic 2 — Perfil de Mascota

---

### US-04: Creación de perfil de mascota (wizard 6 pasos)

**Como** owner (Valentina / Carolina)
**Quiero** registrar a mi mascota con todos sus datos en un wizard paso a paso
**Para** que el agente tenga la información necesaria para generar un plan personalizado

**Criterios de Aceptación:**
- [ ] El wizard tiene 6 pasos con barra de progreso visible
- [ ] Los 13 campos obligatorios son recolectados: nombre, especie, raza, sexo, edad, peso, talla (perros), estado reproductivo, nivel de actividad, BCS, condiciones médicas, alergias, alimentación actual
- [ ] El selector de BCS muestra imágenes de silueta por escala (1-9)
- [ ] El campo de talla solo aparece para perros (5 categorías con rangos kg)
- [ ] El nivel de actividad es diferente para perros (sedentario/moderado/activo/muy_activo) y gatos (indoor/indoor_outdoor/outdoor)
- [ ] Los datos se guardan localmente en Hive hasta que los 13 campos están completos
- [ ] Al completar el wizard, el perfil se sincroniza con el backend
- [ ] Antes del campo de condiciones médicas, se muestra consentimiento explícito (Ley 1581/2012)

**INVEST Check:**
- Independent: sí
- Negotiable: sí — orden de pasos es negociable
- Valuable: sí — sin perfil no hay plan
- Estimable: sí
- Small: relativamente grande — puede dividirse en sub-stories por paso si necesario
- Testable: sí — `behaviors/pet-profile.feature`

**Gherkin asociado:** `behaviors/pet-profile.feature` — Scenario: Owner completa wizard de mascota
**Prioridad:** CRÍTICA
**Epic:** Epic 2

---

### US-05: Actualización de peso desde perfil

**Como** owner (Valentina)
**Quiero** actualizar el peso de Max desde su perfil en cualquier momento
**Para** mantener actualizada la curva de seguimiento

**Criterios de Aceptación:**
- [ ] El owner puede editar el campo peso desde el perfil de la mascota
- [ ] Cada actualización de peso genera un registro histórico (no sobreescribe)
- [ ] El peso actualizado aparece reflejado en la gráfica del dashboard
- [ ] La actualización es disponible offline (Hive) y se sincroniza al recuperar conexión

**INVEST Check:**
- Independent: sí
- Negotiable: sí
- Valuable: sí — alimenta el dashboard de seguimiento
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/dashboard.feature` — Scenario: Owner actualiza peso manualmente
**Prioridad:** ALTA
**Epic:** Epic 2

---

## Epic 3 — Generación de Plan Nutricional

---

### US-06: Generación de plan para mascota sana

**Como** owner (Carolina)
**Quiero** que el agente genere un plan nutricional para Luna
**Para** asegurarme de que come correctamente sin necesitar un vet

**Criterios de Aceptación:**
- [ ] Con el perfil completo, el owner puede iniciar la generación del plan
- [ ] El owner selecciona modalidad: dieta natural o concentrado comercial
- [ ] El agente muestra indicador de progreso durante la generación (máx 60s)
- [ ] Para mascota sana, el plan queda en estado ACTIVE directamente (sin HITL)
- [ ] El plan incluye ingredientes con nombre canónico + alias regional entre paréntesis
- [ ] El plan incluye disclaimer obligatorio
- [ ] Si la modalidad del plan difiere de la alimentación actual → el plan incluye protocolo de transición de 7 días

**INVEST Check:**
- Independent: depende de US-04 (perfil completo)
- Negotiable: sí
- Valuable: sí — core value de la app
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/plan-generation.feature`

**Gherkin asociado:** `behaviors/plan-generation.feature` — Scenario: Generación plan mascota sana
**Prioridad:** CRÍTICA
**Epic:** Epic 3

---

### US-07: Generación de plan para mascota con condición médica

**Como** owner (Valentina)
**Quiero** que el agente genere un plan nutricional para Max (diabético + sobrepeso)
**Para** que Lady Carolina lo revise y apruebe antes de que yo lo siga

**Criterios de Aceptación:**
- [ ] El plan se genera con las restricciones hard-coded de las condiciones aplicadas
- [ ] El LLM usado es el correcto según el número de condiciones (ADR-013)
- [ ] El plan queda en estado PENDING_VET automáticamente
- [ ] El owner recibe notificación: "Tu plan será revisado por nuestro equipo clínico"
- [ ] El agente genera además un set de ingredientes sustitutos válidos por ingrediente principal
- [ ] Ningún ingrediente tóxico para la especie aparece en el plan
- [ ] RER y DER son calculados determinísticamente, nunca por el LLM

**INVEST Check:**
- Independent: depende de US-04
- Negotiable: sí
- Valuable: sí — caso de mayor urgencia clínica
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/plan-generation.feature` + `behaviors/golden-cases/sally.feature`

**Gherkin asociado:** `behaviors/plan-generation.feature` — Scenario: Mascota con condición médica → PENDING_VET
**Prioridad:** CRÍTICA
**Epic:** Epic 3

---

### US-08: Ajuste de ingrediente dentro del set pre-aprobado

**Como** owner (Valentina)
**Quiero** cambiar un ingrediente del plan de Max por uno del set pre-aprobado
**Para** adaptarlo a lo que consigo en el mercado sin necesitar aprobación del vet

**Criterios de Aceptación:**
- [ ] El owner puede ver el set de sustitutos aprobados por ingrediente
- [ ] Al seleccionar un sustituto del set aprobado, el cambio se aplica directamente sin PENDING_VET
- [ ] El agente bloquea ingredientes incompatibles con las condiciones médicas del perfil
- [ ] Si el owner elige un ingrediente fuera del set, el agente ofrece alternativas y, si el owner acepta una fuera del set, el plan vuelve a PENDING_VET

**INVEST Check:**
- Independent: depende de US-07 y US-09 (plan aprobado con set de sustitutos)
- Negotiable: sí
- Valuable: sí — reduce fricción post-aprobación
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/plan-generation.feature` — Scenario: Owner ajusta ingrediente dentro del set aprobado
**Prioridad:** ALTA
**Epic:** Epic 3

---

## Epic 4 — Revisión Veterinaria (HITL)

---

### US-09: Vet revisa y aprueba plan

**Como** veterinaria (Lady Carolina / Dr. Andrés)
**Quiero** revisar el plan de Max y aprobarlo con una fecha de revisión
**Para** que Valentina pueda empezar a seguirlo con seguridad clínica

**Criterios de Aceptación:**
- [ ] El vet ve todos los planes PENDING_VET asignados a él en su dashboard
- [ ] El vet puede ver el perfil completo de la mascota, el plan generado y el set de sustitutos
- [ ] El vet puede aprobar el plan → estado pasa a ACTIVE
- [ ] Al aprobar, el vet puede definir una `review_date` (obligatorio para planes con condición médica)
- [ ] El vet puede validar o solicitar cambio al set de sustitutos generado por el agente
- [ ] El owner recibe notificación push + email: "Tu plan está listo"

**INVEST Check:**
- Independent: depende de US-07
- Negotiable: sí
- Valuable: sí — cierra el ciclo clínico
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/hitl-workflow.feature`

**Gherkin asociado:** `behaviors/hitl-workflow.feature` — Scenario: Vet aprueba plan con review_date
**Prioridad:** CRÍTICA
**Epic:** Epic 4

---

### US-10: Vet devuelve plan con comentario

**Como** veterinaria (Lady Carolina)
**Quiero** devolver un plan con un comentario de observación
**Para** que el agente lo corrija o el owner aclare información antes de aprobarlo

**Criterios de Aceptación:**
- [ ] El vet puede devolver el plan sin aprobarlo, con comentario obligatorio
- [ ] El plan vuelve a PENDING_VET con el comentario visible para el owner y el agente
- [ ] No existe estado RECHAZADO — el plan siempre regresa a PENDING_VET con comentario
- [ ] El vet no puede eliminar el plan, solo devolverlo con comentario

**INVEST Check:**
- Independent: depende de US-09
- Negotiable: sí
- Valuable: sí — garantiza calidad clínica sin estado terminal
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/hitl-workflow.feature`

**Gherkin asociado:** `behaviors/hitl-workflow.feature` — Scenario: Vet devuelve plan con comentario
**Prioridad:** ALTA
**Epic:** Epic 4

---

## Epic 5 — Agente Conversacional

---

### US-11: Consulta nutricional al agente

**Como** owner (Carolina)
**Quiero** preguntarle al agente si Luna puede comer atún enlatado
**Para** tomar decisiones informadas sobre la alimentación de mi gata

**Criterios de Aceptación:**
- [ ] El agente responde consultas nutricionales usando el perfil de la mascota como contexto
- [ ] La respuesta incluye el nombre del alimento con alias regional si aplica
- [ ] El agente no responde consultas médicas — remite al vet con mensaje estructurado
- [ ] El tier Free está limitado a 3 preguntas/día × 3 días → upgrade obligatorio al agotar
- [ ] El agente está disponible antes, durante y después de tener un plan activo

**INVEST Check:**
- Independent: sí
- Negotiable: sí
- Valuable: sí — diferenciador frente a búsqueda en Google
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/conversational-agent.feature`

**Gherkin asociado:** `behaviors/conversational-agent.feature` — Scenario: Consulta nutricional respondida
**Prioridad:** CRÍTICA
**Epic:** Epic 5

---

### US-12: Agente detecta emergencia y remite al vet

**Como** owner (Valentina)
**Quiero** que el agente me avise si lo que le pasa a Max parece una emergencia
**Para** saber cuándo debo ir al vet urgentemente

**Criterios de Aceptación:**
- [ ] El agente detecta palabras clave de emergencia (convulsión, desmayo, sangre, no respira, etc.)
- [ ] Ante emergencia detectada, el agente muestra mensaje de acción urgente con datos de contacto del vet
- [ ] El agente nunca diagnostica ni recomienda medicamentos — siempre remite
- [ ] El mensaje de emergencia no cuenta como una de las 3 preguntas del tier Free

**INVEST Check:**
- Independent: depende de US-11
- Negotiable: sí — lista de palabras clave es negociable
- Valuable: sí — responsabilidad clínica de la plataforma
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/conversational-agent.feature`

**Gherkin asociado:** `behaviors/conversational-agent.feature` — Scenario: Agente detecta emergencia
**Prioridad:** CRÍTICA
**Epic:** Epic 5

---

## Epic 6 — Scanner OCR

---

### US-13: Escanear etiqueta nutricional de concentrado

**Como** owner (Carolina)
**Quiero** fotografiar la tabla nutricional del concentrado de Luna
**Para** saber si es adecuado para el perfil de mi gata

**Criterios de Aceptación:**
- [ ] El scanner acepta imagen de tabla nutricional o lista de ingredientes únicamente
- [ ] El scanner rechaza imágenes de logos, marcas o empaques frontales con mensaje claro
- [ ] El OCR es procesado localmente (Qwen2.5-VL-7B via Ollama) — nunca en la nube
- [ ] El resultado muestra un semáforo: verde / amarillo / rojo
- [ ] Si se detecta un ingrediente tóxico, se muestra alerta inmediata
- [ ] Si se detecta un ingrediente incompatible con una condición médica activa, se señala explícitamente
- [ ] La marca del producto nunca se muestra en el resultado (imparcialidad)
- [ ] El scanner requiere conexión (no disponible offline)

**INVEST Check:**
- Independent: sí (puede usarse sin plan activo)
- Negotiable: sí
- Valuable: sí — diferenciador clave para owners de concentrado
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/ocr-scanner.feature`

**Gherkin asociado:** `behaviors/ocr-scanner.feature` — Scenario: Escaneo exitoso tabla nutricional
**Prioridad:** CRÍTICA
**Epic:** Epic 6

---

## Epic 7 — Exportación PDF y Compartición

---

### US-14: Exportar plan como PDF

**Como** owner (Valentina)
**Quiero** exportar el plan de Max como PDF
**Para** tenerlo guardado y compartirlo con la clínica

**Criterios de Aceptación:**
- [ ] Solo los planes en estado ACTIVE son exportables a PDF
- [ ] El PDF incluye: nombre de la mascota, fecha de generación, plan completo, set de sustitutos aprobados, disclaimer obligatorio y nombre del vet que aprobó
- [ ] El PDF se genera server-side (WeasyPrint) y se entrega como link de descarga
- [ ] El link de descarga tiene TTL de 72 horas
- [ ] Exportar PDF es gratuito para todos los tiers

**INVEST Check:**
- Independent: depende de US-06 o US-07 (plan ACTIVE)
- Negotiable: sí — diseño del PDF es negociable
- Valuable: sí — canal de entrega para owners y vets
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/export.feature`

**Gherkin asociado:** `behaviors/export.feature` — Scenario: Owner exporta plan ACTIVE a PDF
**Prioridad:** CRÍTICA
**Epic:** Epic 7

---

### US-15: Compartir plan por WhatsApp / email

**Como** owner (Valentina) o vet (Dr. Andrés)
**Quiero** compartir el PDF del plan por WhatsApp o email directamente desde la app
**Para** enviárselo a la clínica o a un familiar que cuida a la mascota

**Criterios de Aceptación:**
- [ ] Desde la vista del plan ACTIVE, hay botón "Compartir"
- [ ] El botón abre el share sheet nativo del dispositivo con el link del PDF
- [ ] El vet puede compartir desde su dashboard (ClinicPet o AppPet)
- [ ] El link compartido tiene TTL de 72 horas y no requiere cuenta para visualizarse

**INVEST Check:**
- Independent: depende de US-14
- Negotiable: sí
- Valuable: sí — canal de entrega principal para ClinicPet
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/export.feature` — Scenario: Vet comparte PDF de ClinicPet por WhatsApp
**Prioridad:** CRÍTICA
**Epic:** Epic 7

---

## Epic 8 — Dashboard de Seguimiento

---

### US-16: Owner visualiza evolución de peso y estado del plan

**Como** owner (Valentina)
**Quiero** ver la gráfica de peso de Max y el estado de su plan
**Para** saber si está progresando correctamente

**Criterios de Aceptación:**
- [ ] El dashboard muestra gráfica de peso a lo largo del tiempo
- [ ] El dashboard muestra gráfica de BCS a lo largo del tiempo
- [ ] Se muestra el estado actual del plan: ACTIVE / PENDING_VET / UNDER_REVIEW
- [ ] Se muestra la duración del plan activo (días desde activación)
- [ ] El dashboard es accesible offline (caché Hive)

**INVEST Check:**
- Independent: depende de US-05 (registros de peso)
- Negotiable: sí — tipo de gráfica es negociable
- Valuable: sí — motiva la adherencia
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/dashboard.feature`

**Gherkin asociado:** `behaviors/dashboard.feature` — Scenario: Owner visualiza evolución de peso
**Prioridad:** CRÍTICA
**Epic:** Epic 8

---

### US-17: Vet visualiza seguimiento de sus pacientes

**Como** veterinario (Dr. Andrés / Lady Carolina)
**Quiero** ver el historial de peso, BCS y estado del plan de todos mis pacientes
**Para** hacer seguimiento clínico entre consultas sin necesidad de que el propietario me llame

**Criterios de Aceptación:**
- [ ] El dashboard clínico lista todas las mascotas vinculadas al vet (AppPet y ClinicPet)
- [ ] Por cada mascota: peso actual, tendencia, BCS, estado del plan, días activo
- [ ] El vet puede filtrar por estado del plan o por especie
- [ ] Solo los pacientes vinculados al vet son visibles
- [ ] Disponible para tier Vet BÁSICO y Vet CLÍNICA. Vet FREE no tiene dashboard.

**INVEST Check:**
- Independent: depende de US-16
- Negotiable: sí
- Valuable: sí — diferenciador clave del tier Vet BÁSICO
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/dashboard.feature` — Scenario: Vet visualiza seguimiento de pacientes
**Prioridad:** ALTA
**Epic:** Epic 8

---

## Epic 9 — Freemium y Pagos

---

### US-18: Gate de conversión Free → Básico (condición médica)

**Como** owner (Valentina) en tier Free
**Quiero** generar un plan para Max (con condición médica)
**Para** recibir orientación nutricional validada por un vet

**Criterios de Aceptación:**
- [ ] El tier Free puede generar 1 plan total (incluyendo uno con condición médica)
- [ ] Al intentar generar un segundo plan, se muestra el gate de upgrade con opciones Básico/Premium
- [ ] El proceso de upgrade en MVP es manual (email/WhatsApp al equipo)

**INVEST Check:**
- Independent: depende de US-06 / US-07
- Negotiable: sí
- Valuable: sí — gate de mayor conversión esperada
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/freemium.feature` — Scenario: Free agota su único plan con condición médica
**Prioridad:** ALTA
**Epic:** Epic 9

---

### US-19: Gate de conversión Free → Básico (agente conversacional)

**Como** owner (Carolina) en tier Free
**Quiero** seguir haciendo preguntas al agente después de agotar mis 9 preguntas (3×3 días)
**Para** obtener orientación nutricional continua para Luna

**Criterios de Aceptación:**
- [ ] El tier Free tiene 3 preguntas/día por 3 días (9 preguntas total)
- [ ] Al agotar el límite, el agente muestra gate de upgrade con CTA claro
- [ ] Tras los 3 días, el acceso al agente queda bloqueado hasta upgrade

**INVEST Check:**
- Independent: depende de US-11
- Negotiable: sí
- Valuable: sí — gate secundario de conversión
- Estimable: sí
- Small: sí
- Testable: sí

**Gherkin asociado:** `behaviors/freemium.feature` — Scenario: Free agota preguntas al agente
**Prioridad:** ALTA
**Epic:** Epic 9

---

## Epic 10 — ClinicPet (Vet como Creador de Planes)

---

### US-20: Vet crea perfil de paciente sin app (ClinicPet)

**Como** veterinario (Dr. Andrés) con tier Vet BÁSICO
**Quiero** crear el perfil de Toby (paciente de Don Roberto) desde mi dashboard
**Para** generar un plan nutricional sin que el propietario tenga la app

**Criterios de Aceptación:**
- [ ] El vet puede iniciar "Nuevo Paciente" desde su dashboard (solo Vet BÁSICO y CLÍNICA)
- [ ] El wizard solicita 13 campos del perfil de la mascota + 2 campos del propietario: `owner_name` (nombre) y `owner_phone` (teléfono — para enviar el PDF por WhatsApp)
- [ ] El sistema crea la mascota con `pet_origin = clinic_pet` vinculada al vet
- [ ] El `owner_phone` se usa para compartir el PDF directamente desde el dashboard del vet
- [ ] El plan generado va directamente a revisión del vet creador (no a PENDING_VET de otro vet)
- [ ] El vet aprueba el plan → estado ACTIVE directamente
- [ ] El vet puede compartir el PDF al `owner_phone` registrado desde su dashboard

**INVEST Check:**
- Independent: depende de US-03 (cuenta vet activa)
- Negotiable: sí
- Valuable: sí — habilita vets con pacientes sin app
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/clinic-pet.feature`

**Gherkin asociado:** `behaviors/clinic-pet.feature` — Scenario: Vet crea ClinicPet y aprueba plan
**Prioridad:** ALTA
**Epic:** Epic 10

---

### US-21: Owner reclama su mascota ClinicPet

**Como** owner (hijo de Don Roberto) que acaba de descargar la app
**Quiero** reclamar a Toby con el código que me dio el Dr. Andrés
**Para** ver el historial completo de Toby y gestionar sus planes desde la app

**Criterios de Aceptación:**
- [ ] El vet puede generar un código de reclamación desde el perfil de la ClinicPet (TTL 30 días)
- [ ] El owner crea cuenta y en el onboarding puede ingresar el código de reclamación
- [ ] Al validar el código, el `owner_name` y `owner_phone` del ClinicPet se vinculan a la cuenta creada
- [ ] La ClinicPet se convierte en AppPet con historial completo preservado
- [ ] El vet sigue vinculado como vet asignado de la mascota
- [ ] El código de reclamación expira a los 30 días y puede regenerarse

**INVEST Check:**
- Independent: depende de US-20
- Negotiable: sí
- Valuable: sí — canal de adquisición orgánica de owners vía vets
- Estimable: sí
- Small: sí
- Testable: sí — `behaviors/clinic-pet.feature`

**Gherkin asociado:** `behaviors/clinic-pet.feature` — Scenario: Owner reclama ClinicPet con código
**Prioridad:** MEDIA
**Epic:** Epic 10

---

## Resumen por Prioridad

| Prioridad | Stories |
|-----------|---------|
| CRÍTICA | US-01, US-02, US-03, US-04, US-06, US-07, US-09, US-11, US-12, US-13, US-14, US-15, US-16 |
| ALTA | US-05, US-08, US-10, US-17, US-18, US-19, US-20 |
| MEDIA | US-21 |

## Resumen por Epic

| Epic | Stories | Persona Principal |
|------|---------|-------------------|
| Epic 1 — Identidad | US-01, US-02, US-03 | Todas |
| Epic 2 — PetProfile | US-04, US-05 | Valentina, Carolina |
| Epic 3 — Plan | US-06, US-07, US-08 | Valentina, Carolina |
| Epic 4 — HITL | US-09, US-10 | Lady Carolina, Dr. Andrés |
| Epic 5 — Agente | US-11, US-12 | Carolina, Valentina |
| Epic 6 — OCR | US-13 | Carolina |
| Epic 7 — PDF/Export | US-14, US-15 | Valentina, Dr. Andrés |
| Epic 8 — Dashboard | US-16, US-17 | Valentina, Dr. Andrés |
| Epic 9 — Freemium | US-18, US-19 | Valentina, Carolina |
| Epic 10 — ClinicPet | US-20, US-21 | Dr. Andrés, Don Roberto |
