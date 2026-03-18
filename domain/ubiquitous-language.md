# Ubiquitous Language — NutriVet.IA

Glosario de términos del dominio. Todo el código, documentación y conversaciones deben usar estos términos exactos.
Fuente de verdad: Lady Carolina Castañeda (MV, BAMPYSVET) + Sadid Romero (AI Engineer).

---

## Actores

| Término | Definición |
|---------|-----------|
| **Owner** | Dueño de la mascota. Usuario que registra la mascota y recibe el plan nutricional. Rol: `owner`. |
| **Vet** | Veterinario firmante. Revisa y aprueba planes de mascotas con condición médica. Rol: `vet`. |
| **Pet** | Mascota registrada en el sistema (perro o gato). |

---

## Entidades del Dominio

| Término | Definición |
|---------|-----------|
| **PetProfile** | Conjunto de los 13 campos que definen a una mascota: nombre, especie, raza, sexo, edad, peso, talla, estado reproductivo, nivel de actividad, BCS, antecedentes médicos, alergias, alimentación actual. |
| **AlimentaciónActual** | Tipo de dieta que consume la mascota en el momento de registrar el perfil: `concentrado`, `natural` o `mixto`. Determina el protocolo de transición alimentaria del plan. |
| **DiétaTransición** | Protocolo de 7 días para cambiar gradualmente la alimentación de la mascota sin causar problemas digestivos. Incluido en todo plan cuando `alimentacion_actual ≠ modalidad_del_plan`. |
| **NutritionPlan** | Plan nutricional generado por el agente para una mascota específica. Tiene tipo, estado, y contenido (ingredientes/porciones o perfil de concentrado). |
| **PlanChange** | Registro inmutable de cualquier modificación a un NutritionPlan. Incluye autor, justificación y timestamp. |
| **AgentTrace** | Registro inmutable de cada ejecución del agente LangGraph: modelo usado, inputs, outputs, tokens, latencia. Append-only. |
| **LabelScan** | Resultado del análisis OCR de una etiqueta nutricional. Incluye imagen procesada y evaluación vs perfil de la mascota. |

---

## Términos Clínicos

| Término | Definición |
|---------|-----------|
| **RER** | Resting Energy Requirement. Energía mínima en reposo. `RER = 70 × peso_kg^0.75` kcal/día. |
| **DER** | Daily Energy Requirement. Energía diaria total. `DER = RER × factores`. Siempre calculado por Python, nunca por LLM. |
| **BCS** | Body Condition Score. Escala visual 1-9 que evalúa la condición corporal de la mascota. 1=emaciado, 5=ideal, 9=obeso. |
| **Especie** | `perro` o `gato`. Determina qué lista de alimentos tóxicos aplica y los estándares NRC/AAFCO. |
| **Talla** | Clasificación por tamaño y rango de peso. Solo aplica a perros. Ver tabla de tallas abajo. |
| **Estado Reproductivo** | `esterilizado` o `no_esterilizado`. Afecta el factor DER. Nomenclatura clínica — no se usa "entero". |
| **Nivel de Actividad (Perros)** | `sedentario` / `moderado` / `activo` / `muy_activo`. Multiplicador DER para perros. |
| **Nivel de Actividad (Gatos)** | `indoor` (vive solo en casa) / `indoor_outdoor` (mixto) / `outdoor` (acceso al exterior). Multiplicador DER para gatos — refleja los estándares NRC para felinos. |
| **Condición Médica** | Una de las 13 condiciones soportadas que afecta el plan nutricional y activa HITL. Ver lista en `domain/aggregates/pet-profile.md`. |
| **Alergia** | Alimento específico al que la mascota tiene alergia o intolerancia conocida. Se excluye del plan. |

---

## Estados del Plan

| Término | Definición |
|---------|-----------|
| **PENDING_VET** | Plan generado para mascota con condición médica. Esperando revisión y firma del vet. |
| **ACTIVE** | Plan aprobado y activo. Mascota sana: directo. Mascota con condición: post-firma vet. |
| **UNDER_REVIEW** | Plan activo que ha alcanzado un trigger de revisión (review_date, milestone de etapa de vida). |
| **ARCHIVED** | Plan anterior reemplazado por uno nuevo. Solo lectura, no editable. |

---

## Tipos de Plan

| Término | Definición |
|---------|-----------|
| **Plan Estándar** | Para mascota sana. Sin expiración. Status → ACTIVE directo. |
| **Plan Temporal Medical** | Para mascota con condición médica activa. Vet define `review_date` al aprobar. |
| **Plan Life Stage** | Para cachorros y gatitos. Con milestones automáticos: 3 meses, 6 meses, 12 meses, 18 meses. |

---

## Modalidades de Plan

| Término | Definición |
|---------|-----------|
| **Dieta Natural (Tipo A)** | Plan con ingredientes LATAM en español, porciones en gramos, protocolo de transición 7 días. BARF/casero. |
| **Concentrado Comercial (Tipo B)** | Perfil nutricional ideal para selección de concentrado + criterios de evaluación + espacio para sponsors verificados. |

---

## Seguridad Alimentaria

| Término | Definición |
|---------|-----------|
| **TOXIC_DOGS** | Lista hard-coded de alimentos tóxicos para perros. Nunca puede aparecer en un plan. |
| **TOXIC_CATS** | Lista hard-coded de alimentos tóxicos para gatos. Nunca puede aparecer en un plan. |
| **RESTRICTIONS_BY_CONDITION** | Mapa hard-coded de alimentos y nutrientes prohibidos o limitados por condición médica. |
| **Guardarrail Determinista** | Cualquier restricción aplicada por código Python, no por el LLM. El LLM no puede sobrescribir guardarraíles. |

---

## Fases del Weight Journey

| Término | Definición |
|---------|-----------|
| **Fase Reducción** | BCS ≥ 7. `DER = RER(peso ideal estimado) × factor × 0.8` |
| **Fase Mantenimiento** | BCS 4-6. `DER = RER × factor` estándar. |
| **Fase Aumento** | BCS ≤ 3. `DER = RER × factor × 1.2` |

---

## Términos del Agente LangGraph

| Término | Definición |
|---------|-----------|
| **Orquestador** | Nodo LangGraph que clasifica la intención del owner y enruta al subgrafo correcto. |
| **Plan Generation Subgraph** | Subgrafo que genera planes nutricionales. |
| **Consultation Subgraph** | Subgrafo que responde consultas nutricionales conversacionales. |
| **Scanner Subgraph** | Subgrafo que procesa imágenes de etiquetas nutricionales (OCR). |
| **Referral Node** | Nodo que maneja consultas médicas — nunca responde, siempre deriva al vet. |
| **NutriVetState** | Estado compartido TypedDict accesible por todos los subgrafos. |
| **HITL** | Human-In-The-Loop. Intervención del vet en el ciclo del agente para mascotas con condición médica. |

---

## Tabla de Tallas — Perros

| Código | Nombre | Rango de Peso | Ejemplos de Razas |
|--------|--------|---------------|-------------------|
| `mini` | MINI XS | 1 – 4 kg | Chihuahua, Yorkshire Terrier, Maltés |
| `pequeño` | PEQUEÑO S | 4 – 9 kg | Poodle Toy, Pomerania, Shih Tzu |
| `mediano` | MEDIANO M | 9 – 14 kg | Beagle, Cocker Spaniel, French Bulldog |
| `grande` | GRANDE L | 14 – 30 kg | Labrador, Golden Retriever, Border Collie |
| `gigante` | GIGANTE XL | +30 kg | Gran Danés, San Bernardo, Mastín |

> Para gatos no aplica clasificación de talla — todos los gatos usan factores NRC de felino estándar.

---

## Modelo de Negocio

| Término | Definición |
|---------|-----------|
| **Free** | Tier gratuito: 1 mascota, 1 plan total (puede incluir 1 con condición médica). Agente conversacional: 3 preguntas/día durante 3 días corridos, luego requiere upgrade. |
| **Básico** | $29.900 COP/mes: 1 mascota, 1 plan nuevo por mes. |
| **Premium** | $59.900 COP/mes: hasta 3 mascotas, planes ilimitados. |
| **Vet** | $89.000 COP/mes: mascotas ilimitadas, dashboard clínico. |
| **Gate de Conversión** | Punto donde el owner debe actualizar de tier. Gate 3: mascota con condición médica agota el plan gratuito. |

---

## Aliases Regionales (Base de Alimentos LATAM)

| Alias Colombia | Alias Argentina/Perú | Alias México | Término estándar |
|----------------|---------------------|--------------|-----------------|
| Ahuyama | Zapallo | Calabaza | Cucurbita maxima |
| Pollo | Pollo | Pollo | Gallus gallus domesticus |
| Maíz | Choclo | Elote | Zea mays |
