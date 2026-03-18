# language: es

Feature: Generación de Plan Nutricional
  Como owner registrado
  Quiero generar un plan nutricional para mi mascota
  Para recibir una guía personalizada basada en el perfil clínico de mi mascota

  Background:
    Given un owner autenticado con tier "Premium"
    And una mascota registrada con perfil completo de 12 campos

  # ─── HAPPY PATH — Mascota Sana ───────────────────────────────────────────────

  Scenario: Plan generado directamente activo para mascota sana
    Given la mascota no tiene condiciones médicas registradas
    And el BCS es 5 (mantenimiento)
    When el owner solicita un plan de tipo "Natural"
    Then el plan se genera con status "ACTIVE"
    And no requiere revisión veterinaria
    And el DER calculado usa la fórmula "RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs"
    And el plan contiene ingredientes sin toxinas para la especie
    And el plan muestra el disclaimer "NutriVet.IA es asesoría nutricional digital"

  Scenario: Plan de tipo Concentrado generado para mascota sana
    Given la mascota no tiene condiciones médicas
    And la modalidad seleccionada es "Concentrado"
    When el owner solicita el plan
    Then el plan contiene un perfil nutricional ideal con porcentajes de proteína, grasa y fibra
    And contiene criterios de selección de concentrado
    And si hay sponsors, cada uno tiene el tag "Patrocinado" visible
    And no hay más de 3 sponsors en los resultados

  # ─── HAPPY PATH — Mascota Con Condición Médica ───────────────────────────────

  Scenario: Plan pasa a PENDING_VET para mascota con condición médica
    Given la mascota tiene la condición "diabético"
    When el owner solicita un plan
    Then el plan se genera con status "PENDING_VET"
    And se notifica al veterinario asignado
    And el owner recibe notificación "Tu plan está en revisión veterinaria"
    And el modelo LLM utilizado es "groq-llama-70b" (1 condición)

  Scenario: GPT-4o se activa para mascota con 3 o más condiciones
    Given la mascota tiene las condiciones "diabético", "renal", "gastritis"
    When el owner solicita un plan
    Then el modelo LLM utilizado es "gpt-4o"
    And el plan se genera con status "PENDING_VET"

  # ─── CÁLCULO CALÓRICO ────────────────────────────────────────────────────────

  Scenario: DER calculado correctamente para fase de reducción (BCS ≥ 7)
    Given la mascota tiene peso 12 kg y BCS 8
    And el peso ideal estimado es 9 kg
    When se genera el plan
    Then el RER se calcula sobre el peso ideal estimado (9 kg), no el real (12 kg)
    And el DER incluye el factor de reducción 0.8
    And el DER final es "RER(9kg) × factores × 0.8"

  Scenario: DER calculado correctamente para fase de aumento (BCS ≤ 3)
    Given la mascota tiene BCS 2
    When se genera el plan
    Then el DER incluye el factor de aumento 1.2

  # ─── SEGURIDAD ALIMENTARIA ────────────────────────────────────────────────────

  Scenario: Ingrediente tóxico nunca aparece en el plan
    Given la mascota es un "perro"
    And el agente LLM propone un plan con "uvas" como ingrediente
    When el food_toxicity_checker verifica el plan
    Then "uvas" es removido del plan (está en TOXIC_DOGS)
    And se registra un warning en agent_traces
    And el plan final no contiene ningún ingrediente de TOXIC_DOGS

  Scenario: Restricción por condición médica aplicada correctamente
    Given la mascota tiene la condición "renal"
    When se genera el plan
    Then el plan no contiene ingredientes con alto contenido de fósforo
    And el plan no contiene proteína de alta densidad (restringida para renal)
    And esta restricción fue aplicada antes de que el LLM generara el plan

  # ─── EDGE CASES ──────────────────────────────────────────────────────────────

  Scenario: Owner en tier Free intenta generar segundo plan
    Given el owner tiene tier "Free"
    And ya tiene 1 plan generado
    When el owner solicita un segundo plan
    Then el sistema responde con error "SubscriptionLimitError"
    And se muestra información sobre el tier "Básico" como upgrade sugerido

  Scenario: Alerta cuando la mascota tiene alergias desconocidas
    Given la mascota tiene alergia "no sabe"
    When el owner solicita el plan
    Then el sistema muestra alerta obligatoria
    And recomienda test de alérgenos antes de proceder
    And el owner debe confirmar explícitamente para continuar
