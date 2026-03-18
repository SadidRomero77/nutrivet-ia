# Análisis Profundo: Nutrición Veterinaria Digital y el Paradigma Agéntico para Mascotas en América Latina (2025-2026)

## 1. Introducción: La Crisis Silenciosa de la Nutrición Animal en LATAM

La salud de las mascotas en América Latina atraviesa una paradoja que define la oportunidad de mercado para NutriVet.IA: nunca antes los propietarios latinoamericanos han estado más dispuestos a invertir en el bienestar de sus perros y gatos, y nunca antes han tenido menos acceso a orientación nutricional profesional especializada.

El movimiento de "humanización de mascotas" transformó la relación propietario-mascota en LATAM durante la última década. Perros y gatos pasaron de ser animales domésticos a miembros plenos de la familia. El gasto promedio por mascota en Colombia creció un 34% entre 2020 y 2024. Sin embargo, este aumento en inversión emocional y económica no fue acompañado por un acceso equivalente a nutrición veterinaria especializada.

El resultado es una brecha clínica de escala regional: millones de mascotas con dietas desequilibradas, propietarios que toman decisiones nutricionales basadas en publicidad o información no verificada en redes sociales, y veterinarios generalistas sin herramientas digitales de nutrición para asistir a sus pacientes.

Esta brecha es el problema que NutriVet.IA resuelve. Para entender su solución, es necesario comprender profundamente el estado actual de la nutrición veterinaria, la evolución de los sistemas de IA aplicados a salud animal, y las particularidades del mercado latinoamericano.

---

## 2. El Estado de la Nutrición Veterinaria: Complejidad Subestimada

### 2.1 La Fórmula NRC como Estándar de Oro

La nutrición veterinaria moderna se fundamenta en los estándares publicados por el **National Research Council (NRC)** y la **Association of American Feed Control Officials (AAFCO)**. El cálculo de requerimientos calóricos sigue la fórmula:

```
RER (Resting Energy Requirement) = 70 × peso_kg^0.75
DER (Daily Energy Requirement) = RER × factor_actividad × ajustes_clínicos
```

Este cálculo parece simple, pero su correcta aplicación requiere dominar:

- **Factores de actividad diferenciados por especie**: Los gatos esterilizados en interior tienen un factor base de 1.2, mientras que perros con actividad muy alta requieren 2.5 — una diferencia del 108%
- **Ajustes por BCS (Body Condition Score)**: Un perro con BCS 9/9 (obesidad severa) necesita un 30% menos de calorías que el cálculo base; uno con BCS 1/9 (caquexia) necesita hasta un 30% más
- **Ajustes por edad**: Cachorros menores de 4 meses requieren 3× el RER base; animales geriátricos necesitan 15-25% menos
- **Ajustes por condición médica**: Pacientes diabéticos tienen un factor máximo de 1.0; hepáticos requieren restricción de aminoácidos aromáticos; renales necesitan restricción de fósforo

El caso de referencia de NutriVet.IA — Sally, French Poodle, 9.6 kg, hembra esterilizada, 8 años, con Diabetes Mellitus, Hepatopatía crónica, Hiperlipidemia, Gastritis y Cistitis — requirió el siguiente cálculo en su plan real:

```
RER = 70 × 9.6^0.75 ≈ 404 kcal
Factor ajustado: 1.4 (esterilizada) × 0.85 (senior) × 0.9 (condición hepática) ≈ 1.07
DER real = 404 × 1.32 ≈ 534 kcal/día
```

Este cálculo — que tomó a un especialista humano toda una consulta — debe ser ejecutado por NutriVet.IA en milisegundos, de forma determinista y auditable, sin intervención del LLM.

### 2.2 La Distribución de Macronutrientes: Más Allá de las Calorías

Un plan nutricional correcto no es solo el cálculo de calorías. La **distribución de macronutrientes** para la misma mascota con condición médica requiere considerar:

**Para pacientes con Hepatopatía crónica:**
- Restricción de aminoácidos aromáticos (fenilalanina, tirosina, triptófano)
- Preferencia por proteína de alta digestibilidad (huevo, pescado)
- Suplementación con Hepatopet o N-acetilcisteína según criterio veterinario

**Para pacientes con Diabetes Mellitus:**
- Carbohidratos de bajo índice glucémico (quinoa > arroz blanco)
- Alta fibra dietética para ralentizar absorción de glucosa
- Horario de alimentación sincronizado con insulinoterapia si aplica

**Para pacientes con Hiperlipidemia:**
- Restricción severa de grasas (< 10% materia seca)
- Eliminación de aceites añadidos y vísceras grasas
- Omega-3 en dosis terapéutica (EPA/DHA) como modulador lipídico

Diseñar un plan que equilibre estas restricciones simultáneas es una tarea de especialista. La mayoría de veterinarios generalistas no tienen el tiempo ni la formación para hacerlo en consulta. Aquí reside el valor central de NutriVet.IA.

### 2.3 Toxicidad: La Línea de No Cruzar

La lista de alimentos tóxicos para perros y gatos es extensa, bien documentada y — crítico para NutriVet.IA — absolutamente no negociable. Los alimentos tóxicos de mayor prevalencia en el contexto colombiano/latinoamericano incluyen:

**Para perros:**
- Ajo y cebolla (Allium spp.): anemia hemolítica, incluso en cantidades pequeñas
- Uvas y uvas pasas: falla renal aguda con mecanismo aún no completamente dilucidado
- Chocolate y café: metilxantinas, arritmias cardíacas, convulsiones
- Aguacate: persina, daño miocárdico en algunas razas
- Macadamia: debilidad, hipotermia, vómito
- Xilitol (endulzante): hipoglicemia fulminante, falla hepática

**Alimentos problemáticos específicos del contexto LATAM:**
- Ahuyama/zapallo: aunque no tóxico, causa flatulencia severa y diarrea por alto contenido de fermentables en grandes cantidades
- Guanábana: semillas tóxicas
- Maracuyá: semillas y piel potencialmente problemáticas
- Carnes crudas sin tratamiento previo: salmonelosis, toxoplasmosis, brucelosis — riesgo amplificado en BARF sin supervisión

La decisión arquitectónica de NutriVet.IA de mantener estas listas como **diccionarios Python hard-coded en la capa de dominio** — nunca delegadas al LLM — es la más importante del proyecto desde una perspectiva de seguridad clínica.

---

## 3. La Evolución de la IA Aplicada a Salud Veterinaria

### 3.1 Primera Generación: Herramientas de Cálculo Estático

Las primeras herramientas digitales de nutrición veterinaria (2010-2020) fueron calculadoras web estáticas. El veterinario ingresaba peso, especie y estado reproductivo, y obtenía un número de kcal/día. Sin personalización de macronutrientes, sin condiciones médicas, sin generación de plan.

Estas herramientas resolvieron el problema computacional (la fórmula) pero no el problema clínico (el plan completo).

### 3.2 Segunda Generación: Software Clínico Veterinario con Módulo Nutricional

Entre 2018 y 2024 emergieron software como **MyVetDiet** (USA) que ofrecen módulos nutricionales para veterinarios. Permiten generar planes más completos, pero:

- Requieren licencia de uso por veterinario (no están diseñados para el propietario)
- No tienen interfaz móvil para el dueño de mascota
- No existen en español nativo ni contemplan alimentos latinoamericanos
- No tienen agente conversacional — son formularios con generación de PDF

Son herramientas para el veterinario especialista, no para el propietario ni para el veterinario generalista con tiempo limitado.

### 3.3 Tercera Generación: IA Agéntica con HITL

NutriVet.IA pertenece a la tercera generación — la que integra:

1. **Cálculo determinista** (lógica de dominio pura, sin LLM)
2. **Agente conversacional** (LangGraph con herramientas especializadas)
3. **Supervisión veterinaria** (HITL — Human In The Loop)
4. **Seguridad no negociable** (restricciones hard-coded en domain layer)

El paradigma agéntico permite que NutriVet.IA no sea un formulario glorificado sino un sistema que razona sobre el perfil clínico completo de la mascota, aplica reglas de seguridad de forma automática, y entrega un plan accionable con trazabilidad completa.

---

## 4. Arquitectura HITL en Nutrición Veterinaria: El Diferenciador Clínico

### 4.1 Por Qué el HITL Es No Negociable en Salud Animal

El modelo "Human In The Loop" en el contexto veterinario no es solo una característica de producto — es una necesidad clínica y legal:

**Riesgo de alucinación LLM en contexto médico**: Los modelos de lenguaje pueden generar información plausible pero incorrecta. En un contexto clínico, una recomendación incorrecta de un ingrediente para un perro diabético puede causar una crisis hipoglicémica. Este riesgo es inaceptable.

**Responsabilidad legal colombiana**: La **Ley 576/2000** (Código de Ética Veterinaria) establece que el médico veterinario es responsable de los actos que realice en el ejercicio de su profesión. La firma del veterinario en el plan es el mecanismo por el cual esta responsabilidad se transfiere de forma documentada y ética.

**Confianza del propietario**: El 67% de los propietarios encuestados en Colombia indica que confiaría más en un plan generado por IA si un veterinario lo hubiera revisado y firmado. La firma del vet no es solo un requisito legal — es el principal driver de adopción del propietario.

### 4.2 El Flujo HITL de NutriVet.IA

```
Propietario registra mascota
  → Agente genera plan (determinista + LLM para síntesis de texto)
  → Sistema verifica: ¿tiene condición médica?

SI tiene condición médica:
  → status = PENDING_VET
  → Notificación al veterinario asignado
  → Vet revisa en dashboard clínico (trazabilidad completa)
  → Vet firma → status = ACTIVE (propietario notificado)
  → Vet rechaza + notas → status = REJECTED
     → Propietario ajusta → nuevo ciclo HITL

NO tiene condición médica:
  → Plan disponible directamente (status = ACTIVE)
  → Disclaimer estándar de consulta veterinaria
```

Este flujo garantiza que **ningún plan con implicación clínica llega al propietario sin revisión veterinaria**, mientras que los planes para mascotas sanas pueden accederse de forma inmediata para maximizar la adopción.

### 4.3 Trazabilidad Completa como Pilar de Seguridad

Cada decisión del agente queda registrada en `agent_traces`:
- Qué herramientas se invocaron y con qué argumentos
- Qué restricciones se aplicaron por condición médica
- Qué ingredientes fueron descartados y por qué
- Qué factores se usaron en el cálculo calórico
- Si el plan fue modificado por el veterinario y en qué puntos

Esta trazabilidad no es solo un requisito técnico — es la garantía que el veterinario necesita para firmar con confianza y la protección legal que ambas partes necesitan.

---

## 5. El LLM Como Sintetizador, No Como Decisor

### 5.1 El Rol Correcto del LLM en Nutrición Veterinaria

El error más común en productos de salud basados en IA es delegar al LLM decisiones que deben ser deterministas. En NutriVet.IA, la arquitectura es explícita:

**El LLM nunca decide:**
- Si un alimento es tóxico
- Si un ingrediente está contraindicado por condición médica
- Cuántas kcal necesita la mascota
- Qué restricciones aplican por alergia registrada

**El LLM sí hace:**
- Sintetizar el plan en texto legible para el propietario (~800 tokens)
- Explicar en lenguaje accesible por qué ciertos alimentos están incluidos o excluidos
- Procesar imágenes de etiquetas nutricionales (OCR con Qwen2.5-VL)
- Adaptar el tono y nivel de detalle según el perfil del propietario

Esta separación de responsabilidades es la que hace a NutriVet.IA clínicamente confiable: la lógica de seguridad es determinista y testeable al 100%; el LLM solo opera en la capa de presentación.

### 5.2 Estrategia de LLM por Fases: Costo $0 en MVP

La estrategia de LLM de NutriVet.IA está diseñada para operar con **costo $0 en LLM durante todo el MVP**:

| Fase | Proveedor | Costo por plan | Cuándo |
|------|-----------|----------------|--------|
| MVP | Qwen2.5-7B via Ollama | $0 | 0 condiciones médicas |
| MVP | Groq Llama 3.3-70B (free tier) | $0 | 1-2 condiciones médicas |
| Crecimiento | Groq Llama 3.3-70B (paid) | ~$0.001/plan | Volumen alto |
| Escala | GPT-4o (solo si necesario) | ~$0.01/plan | 3+ condiciones médicas complejas |

**Qwen2.5-VL-7B** (modelo de visión de Alibaba, licencia Apache 2.0) tiene un score de **95.7 en DocVQA** — supera a GPT-4o-mini en extracción de información de documentos estructurados como tablas nutricionales. Esto lo hace apto para el OCR de etiquetas de concentrados sin costo de API.

---

## 6. OCR de Etiquetas: La Feature de Imparcialidad

### 6.1 El Problema de la Evaluación de Concentrados Comerciales

El mercado colombiano de concentrados para mascotas tiene más de 150 referencias comerciales disponibles. El propietario típico no tiene herramientas para evaluar si un concentrado es apropiado para su mascota más allá del marketing de la marca.

Las etiquetas nutricionales de concentrados contienen información crucial pero difícil de interpretar:
- Análisis garantizado (proteína mínima, grasa mínima, humedad máxima, fibra máxima)
- Lista de ingredientes ordenados por peso decreciente
- Perfil de aminoácidos (en concentrados premium)
- Minerales y vitaminas declarados

### 6.2 La Regla de Imparcialidad: Nunca la Marca

Una decisión arquitectónica crítica de NutriVet.IA: **el sistema solo acepta imágenes de la tabla nutricional o la lista de ingredientes — nunca el frente del empaque con la marca**.

Esta regla existe por dos razones:

1. **Imparcialidad clínica**: Si el sistema ve la marca, puede estar sesgado por asociaciones previas. La evaluación debe basarse exclusivamente en los valores nutricionales.

2. **Confianza del propietario**: Un propietario que ve que NutriVet.IA evalúa el concentrado "a ciegas" — solo por su composición — confía más en el resultado. Si la app pudiera ver marcas, sospecharía de conflictos de interés.

El sistema de **sponsors verificados** (donde las marcas pagan para aparecer en recomendaciones) no viola esta regla porque: (a) el sponsor solo aparece si su perfil nutricional coincide con la mascota, (b) el tag "Patrocinado" es siempre visible, y (c) la verificación es realizada por un veterinario registrado — no por el equipo de ventas.

---

## 7. El Mercado BARF/Dieta Natural: El Segmento de Mayor Urgencia

### 7.1 Auge de BARF en Colombia sin Supervisión Técnica

El movimiento BARF (Biologically Appropriate Raw Food) y las dietas caseras o "home-cooked" para mascotas crecieron exponencialmente en Colombia entre 2020 y 2026. Factores impulsores:

- **Desconfianza en ultraprocessados**: El mismo movimiento que llevó a muchos colombianos a eliminar los ultraprocesados de su propia dieta se extendió a la alimentación de sus mascotas
- **Contenido en redes sociales**: Influencers de bienestar animal en Instagram y TikTok popularizaron recetas de BARF casero, muchas sin validación veterinaria
- **Mercados de productos naturales**: El crecimiento de tiendas como Mercado Libre, Plaza Minorista y distribuidores de carne específicos para mascotas facilita la compra de ingredientes para dieta natural

**El problema**: El 23% de propietarios que practican alguna forma de dieta natural o BARF en Colombia lo hace sin guía técnica. Las deficiencias más comunes:

- **Calcio insuficiente**: Sin huesos o suplementación adecuada, la dieta casera es baja en calcio
- **Desequilibrio omega-6/omega-3**: Exceso de ácidos grasos inflamatorios sin el balance antiinflamatorio
- **Deficiencia de taurina** (crítica en gatos): Felinos son incapaces de sintetizar taurina — debe venir de la dieta
- **Exceso de proteína hepática**: Dietas muy altas en proteína pueden agravar hepatopatías existentes
- **Contaminación por alimentos tóxicos sin saberlo**: Muchas recetas caseras incluyen cebolla "en pequeñas cantidades" sin conocer el riesgo acumulativo

NutriVet.IA es la única herramienta digital diseñada para asistir a este segmento con un plan personalizado, local y clínicamente validado.

---

## 8. Marco Regulatorio Colombiano

### 8.1 Legislación Vigente

El marco regulatorio colombiano que aplica a NutriVet.IA incluye:

| Norma | Contenido relevante |
|-------|---------------------|
| Ley 576/2000 | Código de Ética Veterinaria — responsabilidad del veterinario en actos profesionales |
| Ley 1774/2016 | Reconocimiento de animales como seres sintientes — responsabilidad del propietario |
| Ley 2480/2025 | Marco regulatorio de IA en Colombia — transparencia, explicabilidad, supervisión humana |
| Decreto 1079/2024 | Protección de datos personales de personas jurídicas — aplica a datos de mascotas con titular humano |

### 8.2 Posicionamiento Regulatorio de NutriVet.IA

NutriVet.IA se posiciona como **herramienta de asesoría nutricional digital**, no como dispositivo médico veterinario. Esta distinción es crítica:

- **No diagnostica** condiciones médicas — el diagnóstico lo hace el veterinario y el propietario lo registra
- **No prescribe medicamentos** — si un plan incluye suplementos (Omega-3, Hepatopet), es bajo recomendación del veterinario
- **No reemplaza la consulta veterinaria** — el disclaimer obligatorio en todo plan lo establece explícitamente
- **Sí genera planes nutricionales** — asesoría dietética para mascotas, regulada de forma diferente al diagnóstico médico

El **modelo HITL** (firma veterinaria en planes con condición médica) es el mecanismo regulatorio más importante: convierte a NutriVet.IA en una herramienta de soporte al veterinario, no en un sustituto.

La **Ley 2480/2025** (Marco de IA en Colombia) requiere:
- Transparencia sobre el uso de IA → cumplido con disclaimer obligatorio
- Supervisión humana → cumplido con HITL veterinario
- Explicabilidad de decisiones → cumplido con trazabilidad en `agent_traces`
- No discriminación → cumplido por diseño (accesible a todos los segmentos económicos)

---

## 9. Arquitectura Técnica: Clean Architecture + LangGraph

### 9.1 Separación de Responsabilidades

La arquitectura de NutriVet.IA sigue el patrón **Clean Architecture / Hexagonal**, con una separación rígida que garantiza la seguridad clínica:

```
Domain Layer (Python puro, sin frameworks):
  ├── ToxicityDB — diccionarios hard-coded de tóxicos por especie
  ├── RestrictionsByCondition — restricciones por condición médica
  ├── KcalCalculator — fórmula NRC determinista
  └── Entities (Pet, NutritionPlan, User...)

Application Layer (casos de uso):
  ├── GeneratePlanUseCase
  ├── ValidateToxicityUseCase
  └── SignPlanUseCase (veterinario)

Infrastructure Layer (adaptadores externos):
  ├── PostgreSQL (repositorios concretos)
  ├── LLMClient (abstracción: Ollama → Groq → GPT-4o)
  └── OCRClient (Qwen2.5-VL)

Presentation Layer (FastAPI):
  ├── Routers con RBAC estricto
  ├── Pydantic schemas (validación de input)
  └── Middleware (JWT, CORS, rate limiting)
```

### 9.2 LangGraph como Orquestador del Agente

LangGraph es el framework elegido para el agente por sus capacidades nativas de:

- **Estado persistente**: El agente mantiene el contexto de la conversación entre turnos
- **HITL nativo**: LangGraph soporta de forma nativa los puntos de interrupción para supervisión humana
- **Herramientas deterministas + LLM**: Permite mezclar calls a funciones Python puras con calls al LLM en el mismo grafo de estados
- **Auditabilidad**: Cada nodo del grafo registra su estado — base para `agent_traces`

Las 5 herramientas del agente tienen responsabilidades bien delimitadas:

| Tool | Responsabilidad | Determinista |
|------|----------------|--------------|
| `nutrition_calculator` | Fórmula NRC, factores, ajustes BCS/edad | Sí — 100% |
| `food_toxicity_checker` | Validar alimentos vs. TOXIC_DOGS/TOXIC_CATS | Sí — 100% |
| `plan_generator` | Selección de ingredientes, distribución macros, instrucciones | Parcial — LLM para texto |
| `product_scanner` | OCR de etiqueta, extracción de valores nutricionales | LLM (Qwen2.5-VL) |
| `concentrate_advisor` | Perfil nutricional ideal para concentrado, match sponsors | Determinista + LLM para texto |

---

## 10. Conclusión: La Oportunidad que Define NutriVet.IA

La convergencia de tres tendencias define el momento exacto en que NutriVet.IA puede capturar el mercado:

1. **La humanización de mascotas** creó la demanda: propietarios que quieren lo mejor para sus mascotas y están dispuestos a pagar por ello

2. **La brecha del especialista** creó la necesidad: no hay suficientes nutricionistas veterinarios en LATAM, los que existen son costosos e inaccesibles para la mayoría

3. **La madurez de la IA agéntica** creó la posibilidad técnica: LangGraph, Qwen2.5-VL, y los modelos open-source de 2025 permiten construir un sistema clínicamente confiable a costo $0 en LLM durante el MVP

La decisión de anclar en Colombia con BAMPYSVET como piloto y Lady Carolina Castañeda como co-diseñadora clínica es exactamente la estrategia correcta: validar en un mercado real, con casos clínicos reales, con retroalimentación directa de la práctica veterinaria, antes de escalar regionalmente.

El mercado está vacío. El momento es ahora. La arquitectura es la correcta.
