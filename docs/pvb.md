# Product Vision Board — NutriVet.IA
**Versión**: 2.0 · **Fecha**: Marzo 2026
**Autores**: Sadid Romero (AI Engineer) · Lady Carolina Castañeda (MV, BAMPYSVET)

---

## VISIÓN

> **Democratizar la nutrición veterinaria personalizada en LATAM**, haciendo accesible a cualquier dueño de mascota la calidad de un plan elaborado por un especialista en nutrición animal, a través de un agente IA que opera bajo supervisión clínica veterinaria — con seguridad no negociable, sin importar el nivel socioeconómico ni la ciudad.

---

## GRUPO OBJETIVO

### Primario — Dueño de Mascota
- Hombres y mujeres, 25-45 años, Colombia y LATAM
- Tienen uno o más perros o gatos
- Cuentan con smartphone y acceso a internet
- Motivación: mejorar la salud y calidad de vida de su mascota
- Dispuestos a pagar por un servicio confiable y personalizado
- Subcategoría activa: **practicantes de BARF o dieta natural** sin guía técnica

### Secundario — Médico Veterinario Generalista
- Veterinarios en ejercicio en clínicas o consulta independiente
- Sin especialización formal en nutrición
- Necesitan herramienta digital para complementar su práctica clínica
- Quieren ofrecer valor nutricional a sus pacientes sin derivar a especialista
- Primera adopción: clínica BAMPYSVET (Bogotá)

### Terciario — Clínicas y Pet Shops
- Clínicas veterinarias que quieren ofrecer planes nutricionales como servicio adicional
- Pet shops interesados en recomendar concentrados de forma técnica y confiable
- Canal B2B2C para escalar adopción sin marketing directo masivo

---

## NECESIDADES (Problemas que Resuelve)

| # | Problema | Segmento | Severidad |
|---|---------|---------|-----------|
| 1 | Dueños practican BARF sin conocer balances nutricionales — riesgo de déficit o exceso | Primario | 🔴 Alta |
| 2 | Selección de concentrados basada en precio o publicidad, no en composición nutricional | Primario | 🔴 Alta |
| 3 | Mascotas con diabetes, hepatopatía o enfermedad renal reciben dietas genéricas no adaptadas | Primario/Secundario | 🔴 Crítica |
| 4 | Veterinarios generalistas no tienen herramienta de nutrición clínica digital | Secundario | 🟠 Media-Alta |
| 5 | El acceso a un especialista en nutrición veterinaria es costoso y de baja disponibilidad | Primario | 🟠 Media-Alta |
| 6 | No existe forma fácil de verificar si un concentrado comercial es apto para una mascota con condición médica | Primario | 🟠 Media |
| 7 | Riesgo de intoxicación por alimentos prohibidos en dietas caseras sin guía (uvas, cebolla, chocolate, etc.) | Primario | 🔴 Crítica |

---

## PRODUCTO

### Propuesta de Valor Central
Un agente IA conversacional que genera planes nutricionales 100% personalizados para cada mascota, basados en su perfil clínico completo, con validación veterinaria integrada y reglas de seguridad no negociables.

### Capacidades Clave

#### Registro y Perfil Completo
- Cuenta de usuario (nombre, email, ciudad, país)
- Una o varias mascotas por cuenta
- Perfil clínico de cada mascota:
  - Especie, raza, sexo, edad, peso
  - Talla (mini / pequeño / mediano / grande / gigante)
  - Estado reproductivo (esterilizado / sin esterilizar / no sabe)
  - Nivel de actividad (perro: nulo→muy alto · gato: indoor/outdoor)
  - Condición corporal BCS 1-9 con guía visual de imágenes
  - Antecedentes médicos (diabético, hepático, renal, cancerígeno, articular, pancreático, neurodegenerativo, bucal, piel, gastritis)
  - Alergias alimentarias (lista por especie) + opción "no sé" con alerta y aceptación de responsabilidad

#### Dos Modalidades de Plan
- **Tipo A — Dieta Natural**: plan con ingredientes frescos, porciones en gramos, preparación, snacks, transición 7 días y protocolo de emergencia digestiva
- **Tipo B — Concentrado Comercial**: perfil nutricional ideal para seleccionar un concentrado apto; sponsors verificados con tag "Patrocinado" cuando estén disponibles

#### Cálculo Nutricional Determinista
- Fórmula NRC: RER = 70 × peso^0.75 · DER = RER × factor
- Ajustes por especie, estado reproductivo, actividad, edad, BCS y condición médica
- Sin LLM en el cálculo — reproducible y auditable

#### Seguridad Clínica No Negociable
- Lista de alimentos tóxicos hard-coded por especie (nunca editable por el usuario)
- Restricciones automáticas por condición médica registrada
- Alerta y bloqueo si se solicita un alimento contraindicado

#### Escáner OCR de Etiquetas
- Foto de tabla nutricional o lista de ingredientes (nunca marca/logo — imparcialidad)
- Evaluación automática vs perfil de la mascota
- Resultado en semáforo: verde / amarillo / rojo

#### Validación Veterinaria (HITL)
- Planes de mascotas con condición médica requieren firma veterinaria
- Vet puede aprobar, rechazar con notas o sugerir ajustes
- Trazabilidad completa de cada decisión del plan

#### Estrategia de Costos LLM
- **MVP**: Qwen2.5-7B + Qwen2.5-VL-7B via Ollama — costo $0
- **Fallback**: Groq free tier (14.400 req/día sin costo)
- **Escala**: Enrutamiento por complejidad del caso hacia modelos de mayor capacidad

---

## OBJETIVOS DE NEGOCIO

### Métricas de Éxito — MVP (Mes 1-6)

| Métrica | Objetivo |
|---------|---------|
| Planes nutricionales generados/mes | 500 |
| % planes aprobados por vet sin cambios | ≥ 70% |
| Retención a 30 días | ≥ 40% |
| Veterinarios activos en la plataforma | ≥ 10 |
| Tasa conversión registro → primer plan | ≥ 60% |
| Costo LLM por plan generado | $0 (Ollama) |

### Métricas de Crecimiento (Mes 7-12)

| Métrica | Objetivo |
|---------|---------|
| Usuarios activos mensuales | 2.000 |
| Break-even (usuarios pagos) | 500 |
| Sponsors verificados activos | ≥ 3 |
| Ciudades con usuarios activos | ≥ 10 |
| NPS (Net Promoter Score) | ≥ 50 |

### Modelo de Monetización

| Canal | Descripción | Fase |
|-------|------------|------|
| Suscripción owner | Plan mensual/anual para dueños de mascotas | MVP |
| Suscripción vet | Acceso clínico, trazabilidad, múltiples pacientes | MVP |
| Sponsors verificados | Marcas de alimento validadas por vet con tag "Patrocinado" | Mes 6+ |
| B2B Clínicas | Licencia para clínicas que ofrecen planes como servicio | Mes 9+ |

---

## VENTAJAS COMPETITIVAS (Por qué NutriVet.IA gana)

| Ventaja | Descripción |
|---------|------------|
| Validación clínica interna | Lady Carolina Castañeda (MV, BAMPYSVET) como co-diseñadora y validadora desde el día 0 |
| Clínica piloto disponible | BAMPYSVET como primer cliente real desde MVP — casos reales, retroalimentación inmediata |
| Arquitectura HITL como diferenciador | El plan de IA + firma del vet genera confianza que ningún competidor ofrece en LATAM |
| LATAM-first | Alimentos locales (Colombia), español nativo, precios en COP, regulación colombiana contemplada |
| Reglas no negociables | La seguridad clínica es hard-coded — no se puede comprometer por presión del usuario |
| Costo $0 en LLM para MVP | Qwen2.5 + Ollama permite operar sin costo de modelo durante la fase de validación |
| Imparcialidad en OCR | No acepta marcas en el escáner — genera confianza vs apps que priorizan sponsors |

---

## COMPETIDORES ANALIZADOS

| Competidor | Brecha que NutriVet.IA cubre |
|-----------|------------------------------|
| MyVetDiet | Sin app móvil, sin agente IA, sin BARF, no está en LATAM |
| PetDesk | Gestión de citas — no es nutrición |
| Pawp | Telemedicina general — no es nutrición especializada |
| NutriPet | Sin validación veterinaria, sin condiciones médicas |
| VetPass | Agenda veterinaria — no es nutrición |

**Brecha confirmada**: ningún competidor cubre el espacio completo — agente IA + validación vet + BARF + concentrado + OCR + móvil + español + LATAM + condiciones médicas integradas.

---

## RIESGOS PRINCIPALES

| Riesgo | Nivel | Mitigación |
|--------|-------|-----------|
| Alucinación LLM → daño a mascota | 🔴 Crítico | Toxicidad y restricciones hard-coded — el LLM nunca decide sobre seguridad |
| Alergia no detectada | 🔴 Alto | Alerta "no sé" + aceptación de responsabilidad documentada |
| Adopción veterinaria lenta | 🟠 Alto | Lady Carolina como embajadora + onboarding < 2 min |
| Responsabilidad legal (Ley 576/2000, Ley 2480/2025) | 🟠 Medio-Alto | Disclaimer obligatorio en todo plan + consultoría legal |
| Calidad OCR en Ollama vs GPT-4o | 🟡 Medio | Qwen2.5-VL-7B tiene score 95.7 DocVQA — validado antes de producción |
| Sponsors que comprometan imparcialidad | 🟡 Medio | Verificación vet obligatoria + tag "Patrocinado" siempre visible |

---

## SUPUESTOS CLAVE

- Los dueños de mascotas en Colombia están dispuestos a pagar por nutrición veterinaria digital personalizada
- Los veterinarios generalistas adoptan herramientas digitales si el onboarding es simple
- Qwen2.5-VL-7B tiene calidad suficiente para OCR de tablas nutricionales en producción (validar en alpha)
- La legislación colombiana permite apps de asesoría nutricional animal con disclaimers apropiados
- BAMPYSVET puede onboardear al menos 5 veterinarios en los primeros 3 meses
