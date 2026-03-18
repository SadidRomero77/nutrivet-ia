# Invariantes del Dominio — NutriVet.IA

Reglas de negocio que el sistema debe garantizar en todo momento, sin excepción.
Cambiar cualquiera de estas reglas requiere confirmación de Sadid Romero Y Lady Carolina Castañeda (MV).

---

## Invariantes de Seguridad Alimentaria (BLOQUEANTES)

**INV-01**: Ningún alimento de `TOXIC_DOGS` puede aparecer en un plan para perro.
> Verificación: `food_toxicity_checker` antes de cada generación de plan. El LLM no participa en esta decisión.

**INV-02**: Ningún alimento de `TOXIC_CATS` puede aparecer en un plan para gato.
> Verificación: `food_toxicity_checker` antes de cada generación de plan.

**INV-03**: Ningún alimento prohibido por `RESTRICTIONS_BY_CONDITION[condicion]` puede aparecer en un plan donde la mascota tiene esa condición.
> Verificación: `food_toxicity_checker` aplica restricciones antes de que el LLM genere el plan.

---

## Invariantes de Cálculo Calórico

**INV-04**: `RER` siempre se calcula como `70 × peso_kg^0.75`. Nunca el LLM calcula RER.
> Verificación: `nrc_calculator.py` — Python puro, cobertura 100% en tests.

**INV-05**: `DER` siempre se calcula como `RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs`. Nunca el LLM calcula DER.

**INV-06**: El Caso Sally debe producir `RER ≈ 396 kcal` y `DER ≈ 534 kcal/día` (tolerancia ±0.5 kcal).
> Verificación: `test_sally_golden_case` — bloqueante de release.

**INV-07**: `DER < 200 kcal` es señal de error — el sistema debe detener la generación y alertar.
> Ningún perro o gato adulto tiene DER < 200 kcal. Si ocurre, hay un error en el input.

**INV-08**: Para BCS ≥ 7 (reducción), el RER se calcula sobre el **peso ideal estimado**, no el peso real.
> La fórmula correcta es: `RER(peso_ideal) × factor × 0.8`.

---

## Invariantes del Ciclo de Vida del Plan

**INV-09**: Un plan generado para mascota con condición médica SIEMPRE inicia en estado `PENDING_VET`. Nunca en `ACTIVE`.

**INV-10**: Un plan generado para mascota sana (sin condiciones) SIEMPRE inicia en estado `ACTIVE`. Nunca en `PENDING_VET`.

**INV-11**: Si un owner agrega una condición médica a una mascota con plan `ACTIVE`, ese plan vuelve a `PENDING_VET` automáticamente.

**INV-12**: Un plan `ARCHIVED` es inmutable. No puede ser editado, reactivado ni eliminado.

**INV-13**: `agent_traces` son append-only. No existe UPDATE sobre trazas ya insertadas.

**INV-14**: `plan_changes` son append-only. Cada edición del vet crea un nuevo registro, no modifica el anterior.

---

## Invariantes de Roles y Acceso

**INV-15**: Solo un usuario con rol `vet` puede cambiar el estado de un plan de `PENDING_VET` a `ACTIVE`.

**INV-16**: Un vet solo puede acceder a los planes de sus propios pacientes (mascotas asignadas a su clínica o por el owner). RBAC estricto.

**INV-17**: Un owner con tier `Free` no puede tener más de 1 mascota registrada.

**INV-18**: Un owner con tier `Free` no puede generar más de 1 plan total (incluyendo 1 con condición médica).

---

## Invariantes del Agente LLM

**INV-19**: El agente conversacional NUNCA responde consultas sobre síntomas, medicamentos, diagnósticos o tratamientos. Siempre emite `ReferralMessage`.

**INV-20**: Los prompts enviados a LLMs externos (Groq, OpenAI) NUNCA contienen nombres de mascotas, nombres de owners, ni condiciones médicas en texto libre. Solo IDs anónimos.

**INV-21**: El LLM routing es una función determinista del número de condiciones médicas. El agente no puede seleccionar un modelo distinto al que le corresponde.

---

## Invariantes de la Interfaz

**INV-22**: Cada vista del plan debe mostrar el disclaimer:
> "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."

**INV-23**: El scanner NUNCA acepta imágenes de logos, marcas o empaque frontal. Solo tabla nutricional o lista de ingredientes.

**INV-24**: Los planes de tipo Concentrado que muestren un sponsor SIEMPRE deben llevar el tag "Patrocinado" visible. Máximo 3 sponsors por resultado.

---

## Invariantes de Ayuno

**INV-25**: Ningún plan puede recomendar ayunos mayores a 12 horas. Riesgo hepático, biliar y pancreático.

---

## Invariantes del Perfil (Actualizados)

**INV-26**: El campo `size` (talla) es obligatorio para perros y `None` para gatos. Si `species == GATO` y `size != None` → error de validación.

**INV-27**: El tipo de `activity_level` debe corresponder a la especie: `DogActivityLevel` para perros, `CatActivityLevel` para gatos. El sistema no puede mezclarlos.

**INV-28**: El estado reproductivo solo acepta `esterilizado` o `no_esterilizado`. El término "entero" está prohibido en toda la codebase — es terminología coloquial, no clínica.

**INV-29**: El campo `current_diet` es obligatorio y debe estar definido antes de generar cualquier plan. Sin `current_diet`, el sistema no puede calcular si se necesita protocolo de transición.

**INV-30**: Si `current_diet != modalidad_del_plan`, el plan generado DEBE incluir un protocolo de transición de 7 días. No es opcional.

---

## Invariantes del Agente Conversacional — Free Tier

**INV-31**: Un owner con tier `Free` tiene un límite de 3 preguntas por día al agente conversacional.

**INV-32**: El límite de 3 preguntas/día aplica durante máximo 3 días corridos. Al cuarto día, el agente responde únicamente con un mensaje de upgrade — no procesa más preguntas hasta que el owner actualice su plan.

**INV-33**: El contador de preguntas Free se reinicia a las 00:00 hora de Colombia (UTC-5) cada día.

---

## Invariantes del Estado del Plan (Clarificaciones)

**INV-34**: El estado "RECHAZADO" NO existe en el sistema. Si un vet no está de acuerdo con el plan, tiene dos opciones: (a) editar + aprobar, o (b) devolver al owner con comentario obligatorio → plan vuelve a `PENDING_VET` y el agente regenera cuando el owner actualiza el perfil.

**INV-35**: El estado "BORRADOR" NO existe en el sistema. El wizard guarda localmente en el dispositivo (Hive) hasta que los 13 campos estén completos. Solo cuando el owner confirma todos los campos se crea el registro en el backend.

---

## Invariantes de Exportación

**INV-36**: Solo planes en estado `ACTIVE` pueden exportarse a PDF o compartirse. Planes en `PENDING_VET`, `UNDER_REVIEW` o `ARCHIVED` no son exportables por el owner.

**INV-37**: El PDF exportado debe incluir el disclaimer en la primera página: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
