# Personas — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10
**Fuente**: docs/icp.md + requirements.md + ADR-018

---

## Persona 1 — Valentina

**Rol**: Owner primaria — mascota con condición médica
**Edad**: 31 años | **Ciudad**: Bogotá, Colombia
**Mascota**: Max, Labrador Retriever, 4 años, diabetes mellitus + sobrepeso

**Contexto**:
Valentina trabaja en marketing digital. Max fue diagnosticado hace 6 meses con diabetes mellitus. El vet de la clínica le entregó una dieta general en papel, pero Valentina no sabe cómo adaptarla al día a día ni qué ingredientes usar en Colombia. Busca una solución que le diga exactamente qué darle a Max, cuánto, y que su vet pueda revisar el plan.

**Motivaciones**:
- Que Max esté sano sin tener que ser nutricionista
- Confiar en que el plan es validado por un profesional
- Ajustar ingredientes fácilmente cuando no consigue algo en el mercado

**Frustraciones**:
- Las dietas en papel son genéricas y difíciles de adaptar
- No sabe si lo que compra en el supermercado sirve para un perro diabético
- Le da miedo equivocarse con un perro con condición médica

**Comportamiento digital**: Alta — usa apps diariamente, cómoda con Flutter
**Tier esperado**: Básico o Premium (urgencia clínica real)
**Epic principal**: Epic 3 (Plan) + Epic 4 (HITL) + Epic 8 (Dashboard)

---

## Persona 2 — Dr. Andrés

**Rol**: Veterinario adoptante temprano — BAMPYSVET
**Edad**: 38 años | **Ciudad**: Bogotá, Colombia
**Especialidad**: Medicina general de pequeñas especies

**Contexto**:
Dr. Andrés es el primer vet adoptante del piloto en BAMPYSVET. Atiende ~40 pacientes/mes. Muchos propietarios de sus pacientes no tienen smartphone o no descargan apps. Necesita una herramienta que le ayude a generar planes nutricionales rápido, compartirlos por WhatsApp como PDF, y hacer seguimiento de sus pacientes directamente desde su dashboard.

**Motivaciones**:
- Ofrecer un servicio nutricional diferenciador a sus clientes
- Reducir el tiempo que tarda en diseñar planes manualmente
- Fidelizar pacientes con seguimiento digital

**Frustraciones**:
- Diseñar planes nutricionales manualmente toma demasiado tiempo
- Muchos propietarios no siguen las indicaciones en papel
- No tiene forma de hacer seguimiento del peso de sus pacientes entre consultas

**Comportamiento digital**: Media-alta — usa computador en clínica, menos smartphone
**Tier esperado**: Vet BÁSICO ($89.000 COP/mes)
**Epic principal**: Epic 4 (HITL) + Epic 7 (PDF/Export) + Epic 10 (ClinicPet)

---

## Persona 3 — Carolina

**Rol**: Owner secundaria — mascota sana, optimización nutricional
**Edad**: 27 años | **Ciudad**: Medellín, Colombia
**Mascota**: Luna, gato doméstico, 2 años, indoor, esterilizada, BCS 5/9

**Contexto**:
Carolina adoptó a Luna hace un año. Luna está sana pero Carolina quiere asegurarse de que come bien. Usa concentrado comercial pero no sabe si es el adecuado. Le gustaría saber qué buscar en la etiqueta y si puede complementar con algo natural ocasionalmente.

**Motivaciones**:
- Que Luna esté sana de forma preventiva
- Entender qué ingredientes son buenos/malos para gatos
- Usar el OCR para evaluar el concentrado que compra

**Frustraciones**:
- Información contradictoria en internet sobre nutrición felina
- No sabe leer las etiquetas de los concentrados
- No tiene vet de confianza para consultas nutricionales menores

**Comportamiento digital**: Alta — early adopter, Instagram/TikTok, cómoda con apps
**Tier esperado**: Free → Básico
**Epic principal**: Epic 3 (Plan) + Epic 5 (Agente) + Epic 6 (OCR)

---

## Persona 4 — Lady Carolina (Vet de Plataforma)

**Rol**: Veterinaria de plataforma — safety net clínico del MVP
**Edad**: 34 años | **Ciudad**: Bogotá, Colombia
**Institución**: BAMPYSVET

**Contexto**:
Lady Carolina es co-diseñadora del producto y árbitro clínico. En el MVP actúa como vet de plataforma: recibe automáticamente todos los planes con condición médica de owners sin vet asignado. Valida los golden cases, aprueba los conjuntos de sustitutos generados por el agente y actúa como fallback para vets FREE que superan su límite.

**Motivaciones**:
- Garantizar la calidad clínica de todos los planes generados
- Validar que el agente no cometa errores nutricionales en casos médicos
- Escalar el alcance de su práctica más allá de los pacientes presenciales

**Comportamiento digital**: Alta — usa el dashboard clínico constantemente
**Tier**: Vet BÁSICO proporcionado por la plataforma (sin costo)
**Epic principal**: Epic 4 (HITL) + Epic 10 (ClinicPet)

---

## Persona 5 — Don Roberto (Owner sin app)

**Rol**: Propietario sin smartphone — paciente de ClinicPet
**Edad**: 58 años | **Ciudad**: Bogotá, Colombia
**Mascota**: Toby, Beagle, 10 años, artritis + hipotiroidismo

**Contexto**:
Don Roberto lleva a Toby a BAMPYSVET regularmente. No tiene smartphone ni interés en descargar apps. El Dr. Andrés necesita generar un plan nutricional para Toby y compartírselo como PDF por WhatsApp (el de su hija) o impreso. Don Roberto es el caso de uso central de ClinicPet.

**Motivaciones**:
- Que Toby mejore su condición articular con la alimentación correcta
- Recibir el plan de forma simple (PDF impreso o por WhatsApp de su hija)

**Comportamiento digital**: Nulo — no usa apps
**Tier**: No aplica (es paciente de ClinicPet, no usuario de la app)
**Epic principal**: Epic 10 (ClinicPet)
