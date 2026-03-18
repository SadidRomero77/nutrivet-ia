# DECISIONS.md — Decisiones Arquitectónicas NutriVet.IA (MADR) v2
> Registro de decisiones significativas en formato MADR.
> Actualizado con decisiones de la v2 basadas en referencia clínica y requisitos ampliados.

---

## ADR-013 — Estrategia de LLM por fases: Ollama/Groq → GPT-4o

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: El 80% del procesamiento de NutriVet.IA es determinista (kcal, toxicidad, restricciones médicas) y no requiere LLM. El LLM solo se usa para síntesis de texto del plan (~800 tokens) y OCR de etiquetas (~300 tokens). Usar GPT-4o desde el día 0 genera costos innecesarios durante el MVP antes de tener usuarios.

**Decisión**: Estrategia de LLM en 3 fases con capa de abstracción que permite cambiar de proveedor sin modificar la lógica de negocio:

- **Fase 1 (MVP — $0)**: Qwen2.5-7B-Instruct + Qwen2.5-VL-7B via Ollama (local/self-hosted). Fallback: Groq free tier (14.400 req/día sin costo).
- **Fase 2 (Crecimiento)**: Groq Llama 3.3-70B (~$0.59/1M tokens) para casos estándar. GPT-4o solo para casos con 3+ condiciones médicas.
- **Fase 3 (Escala)**: Evaluar fine-tuning de Qwen2.5 con casos clínicos validados. Self-hosting GPU en AWS para eliminar costo por token.

**Enrutamiento por complejidad**:
```python
# 0 condiciones médicas   → Ollama Qwen2.5-7B  ($0)
# 1-2 condiciones         → Groq Llama 3.3-70B (muy barato)
# 3+ condiciones          → GPT-4o             (máxima calidad)
```

**Modelos validados para las tareas de NutriVet.IA**:
- Qwen2.5-VL-7B en DocVQA: score 95.7 (supera GPT-4o-mini) — apto para OCR de tablas nutricionales
- Qwen2.5-7B-Instruct: multilingüe nativo (español), sigue instrucciones complejas, licencia Apache 2.0
- `ollama pull qwen2.5:7b` + `ollama pull qwen2.5vl:7b` — instalación en 2 comandos

**Costo estimado por plan (Fase 1)**:
- Plan estándar: **$0** (Ollama)
- 500 planes/mes: **$0**
- 5000 planes/mes con Groq: **< $0.10 total**

**Consecuencias**:
- (+) MVP con costo de LLM = $0
- (+) La lógica de negocio es 100% independiente del proveedor LLM
- (+) Qwen2.5-VL reemplaza GPT-4o Vision para OCR sin pérdida de calidad en tablas nutricionales
- (-) Requiere servidor con 8GB VRAM para correr Qwen2.5-VL-7B en Ollama
- (-) En AWS Lambda (serverless) no se puede correr Ollama — usar Groq free tier como fallback en ese entorno
- (-) Respuesta de Ollama puede ser más lenta que GPT-4o en hardware limitado

**Infraestructura de Ollama en desarrollo local**:
```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelos
ollama pull qwen2.5:7b        # Texto — síntesis de planes
ollama pull qwen2.5vl:7b      # Visión — OCR de tablas nutricionales

# Variables de entorno en .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

# Para producción AWS → usar Groq (no requiere GPU propia)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
```

---

## ADR-001 — LangGraph como orquestador del agente

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: Se requiere un agente IA que mantenga estado conversacional, soporte bucles de revisión (HITL) y permita encadenar herramientas deterministas con llamadas LLM de forma auditable.

**Decisión**: Usar LangGraph sobre alternativas (LangChain directa, AutoGPT, CrewAI).

**Consecuencias**:
- (+) Soporte nativo de HITL (Human In The Loop) requerido para validación veterinaria
- (+) Grafo de estados explícito — flujo auditable y testeable
- (+) Fácil integración de tools deterministas junto a LLM
- (-) Curva de aprendizaje mayor que LangChain simple

---

## ADR-002 — Toxicidad y restricciones médicas hard-coded (nunca LLM)

**Estado**: Aceptado — No negociable
**Fecha**: Marzo 2026

**Contexto**: El riesgo de alucinación del LLM en decisiones de toxicidad puede causar daño real a mascotas. La lista de alimentos tóxicos es estable y validada clínicamente.

**Decisión**: `ToxicityDB` y `RestrictionsByCondition` son diccionarios Python hard-coded en `app/domain`. El LLM nunca decide si algo es tóxico o está contraindicado.

**Consecuencias**:
- (+) Seguridad garantizada — cero riesgo de alucinación en decisiones críticas
- (+) Testeable al 100% con unit tests deterministas
- (-) Requiere proceso formal para agregar nuevos alimentos (validación veterinaria)
- (-) Menos flexible que base de datos editable

---

## ADR-003 — AWS sobre Azure para despliegue

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: El proyecto tiene créditos AWS disponibles. Lambda + API Gateway es el modelo serverless más maduro para APIs Python con FastAPI.

**Decisión**: AWS Lambda (container image vía ECR) + API Gateway HTTP + RDS PostgreSQL + S3 + Secrets Manager + CloudWatch.

**Consecuencias**:
- (+) Serverless → sin costos fijos mientras no hay tráfico (MVP)
- (+) Mangum adapter permite FastAPI → Lambda sin cambios de código
- (-) Cold start inicial en Lambda (mitigable con Provisioned Concurrency)
- (-) Timeout de 15 min en Lambda (suficiente para LangGraph con condición médica compleja)

---

## ADR-004 — GPT-4o Vision para OCR de etiquetas nutricionales

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: Se necesita extraer valores nutricionales y lista de ingredientes de fotos de etiquetas. Herramientas OCR tradicionales (Tesseract) tienen baja precisión en tablas nutricionales con diseños variables.

**Decisión**: GPT-4o Vision como motor de OCR para tablas nutricionales e ingredientes.

**Restricción crítica**: Solo se acepta imagen de tabla nutricional o lista de ingredientes. Nunca imagen de marca/logo — para mantener imparcialidad y reducir sesgos comerciales.

**Consecuencias**:
- (+) Alta precisión en tablas con formatos variados
- (+) Extrae ingredientes y los ordena por porcentaje implícito
- (-) Costo por imagen (~$0.003/imagen)
- (-) Latencia mayor que OCR tradicional (2-5 seg)

---

## ADR-005 — USDA FoodData como base de datos nutricional primaria

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: Se necesita una base de datos nutricional confiable para ingredientes comunes. USDA FoodData Central es la referencia estándar en nutrición.

**Decisión**: USDA FoodData Central como fuente primaria. Complementar con base local para alimentos típicos de Colombia/LATAM no disponibles en USDA.

**Consecuencias**:
- (+) Datos nutricionales validados y actualizados regularmente
- (+) API pública gratuita disponible
- (-) Alimentos colombianos/LATAM poco representados → requiere carga manual validada por vet

---

## ADR-006 — Cálculo de kcal determinista (RER/DER, fórmula NRC)

**Estado**: Aceptado — No negociable
**Fecha**: Marzo 2026

**Contexto**: El cálculo de requerimientos calóricos debe ser reproducible, auditable y correcto. La fórmula NRC estándar es: RER = 70 × peso^0.75, DER = RER × factor.

**Decisión**: Implementar `kcal_calculator.py` en domain layer con fórmula NRC. Nunca delegar al LLM. Validado contra el caso real de Sally (9.6 kg, esterilizada, actividad baja → 534 kcal/día).

**Consecuencias**:
- (+) Resultados reproducibles y testeables
- (+) Validado contra caso clínico real
- (-) Factores de ajuste deben actualizarse si cambian guías NRC/AAFCO

---

## ADR-007 — BCS en escala 1-9 (NRC/AAFCO estándar)

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: Existen dos escalas de Body Condition Score: 1-5 (usada en algunos países) y 1-9 (estándar NRC/AAFCO). La escala 1-9 permite mayor granularidad en el diagnóstico de sobrepeso/obesidad.

**Decisión**: Usar escala 1-9 con guía visual de imágenes para perro y gato por separado. La app muestra un grid 3×3 con imagen de referencia por cada punto.

**Consecuencias**:
- (+) Estándar internacional — compatible con formación veterinaria
- (+) Mayor granularidad para ajuste de calorías
- (-) Requiere 18 imágenes de referencia (9 perro + 9 gato)

---

## ADR-008 — Dos modalidades de plan: Natural y Concentrado

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: No todos los usuarios quieren o pueden preparar dieta natural (BARF/casera). Forzar dieta natural reduce la adopción. El PDF de referencia incluye explícitamente "Opción A (casera)" y "Opción B (comercial mixta)".

**Decisión**: Al iniciar el proceso de generación de plan, el usuario elige entre:
- **Tipo A — Natural**: plan con ingredientes frescos, porciones en gramos, preparación, snacks, transición y protocolo de emergencia.
- **Tipo B — Concentrado**: perfil nutricional ideal (% proteína, grasa, fibra, ingredientes a buscar/evitar) para que el usuario seleccione un concentrado comercial apto. Sin marcas inicialmente; sistema de sponsors para futuro.

**Consecuencias**:
- (+) Mayor adopción al cubrir dos realidades del mercado
- (+) Honesto con limitaciones del usuario (tiempo, presupuesto)
- (-) Duplica la lógica de generación de planes en el agente
- (-) Sistema de sponsors requiere gobernanza cuidadosa

---

## ADR-009 — Sistema de sponsors para concentrados (opt-in, siempre transparente)

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: En el futuro se desea monetizar a través de marcas de alimentos para mascotas. El riesgo es perder imparcialidad clínica si los sponsors no son verificados.

**Decisión**: Sistema de sponsors con reglas estrictas:
1. Solo admin puede crear un sponsor
2. Todo sponsor DEBE ser verificado por un veterinario registrado en la plataforma
3. El tag "Patrocinado" es visible, de color amarillo, nunca oculto
4. Un sponsor solo aparece si su perfil nutricional coincide con el paciente
5. Máximo 3 sponsors por resultado
6. OCR de etiquetas: NUNCA aceptar imagen de marca (imparcialidad)

**Consecuencias**:
- (+) Monetización posible sin comprometer credibilidad clínica
- (+) Transparencia total con el usuario
- (-) Crecimiento lento de sponsors (requiere verificación veterinaria)

---

## ADR-010 — Manejo de alergias "no sé" con alerta explícita y aceptación de responsabilidad

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: Muchos propietarios no saben si su mascota tiene alergias alimentarias. Ignorar esto puede generar planes con alérgenos no detectados. Bloquear el plan hasta hacer un test es excesivo y reduce adopción.

**Decisión**: Si el usuario selecciona "No sé / No he realizado test alérgenos":
1. Mostrar alerta con recomendación de test profesional
2. Requiere que el usuario confirme explícitamente con checkbox
3. Registrar `owner_accepted_risk = true` en base de datos
4. Plan se genera sin exclusiones específicas pero con disclaimer prominente
5. El disclaimer indica que la responsabilidad recae en el usuario

**Consecuencias**:
- (+) No bloquea el flujo — mayor adopción
- (+) Responsabilidad legal documentada
- (-) Riesgo de plan subóptimo si hay alergia no diagnosticada

---

## ADR-011 — Registro de usuario con ciudad y país

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: NutriVet.IA es una plataforma LATAM-first. La ciudad y país permiten adaptar recomendaciones (alimentos locales disponibles), analíticas de mercado y cumplimiento regulatorio futuro.

**Decisión**: El registro incluye campos de ciudad y país (ambos opcionales en v1, recomendados). No se geolocalizan — el usuario los ingresa manualmente.

**Consecuencias**:
- (+) Datos para personalización futura (alimentos regionales)
- (+) Analítica de adopción por ciudad/país
- (-) Datos desactualizados si el usuario cambia de ciudad

---

## ADR-012 — Protocolo de transición de 7 días (hard-coded)

**Estado**: Aceptado
**Fecha**: Marzo 2026

**Contexto**: Cambios abruptos de alimentación causan gastritis y diarrea en perros y gatos. Los estándares de nutrición veterinaria especifican una transición gradual de 7 días (75/25 → 50/50 → 25/75 → 100%).

**Decisión**: Todo plan generado (natural o concentrado) incluye el protocolo de transición de 7 días como parte no opcional del plan. Se visualiza como gráfica en la app.

**Consecuencias**:
- (+) Reduce riesgo de problemas digestivos en el inicio del plan
- (+) Validado clínicamente por referencia veterinaria
- (-) No customizable por el usuario (solo el veterinario puede modificarlo)
