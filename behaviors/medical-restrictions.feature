# language: es

Feature: Restricciones Médicas y Seguridad Alimentaria
  Como sistema de guardarraíles deterministas
  Quiero garantizar que ningún plan nutricional contenga alimentos perjudiciales
  Para proteger la salud de mascotas con condiciones médicas o alergias

  # ─── TOXICIDAD ────────────────────────────────────────────────────────────────

  Scenario: Uvas bloqueadas para perros (TOXIC_DOGS)
    Given una mascota es un "perro" sin condiciones médicas
    And el agente LLM propone "uvas" como ingrediente del plan
    When el food_toxicity_checker evalúa el plan
    Then "uvas" es eliminado del plan
    And el incidente queda en agent_traces con nivel "WARNING"
    And el plan se regenera sin ese ingrediente

  Scenario: Lilium bloqueado para gatos (TOXIC_CATS)
    Given una mascota es un "gato"
    And el agente LLM propone "extracto de lilium" en el plan
    When el food_toxicity_checker evalúa el plan
    Then el ingrediente es eliminado
    And el plan continúa sin lilium

  Scenario: Chocolate bloqueado para ambas especies
    Given una mascota puede ser perro o gato
    When el plan propuesto incluye "chocolate"
    Then el food_toxicity_checker bloquea el chocolate para ambas especies
    And registra la detección como evento crítico

  Scenario: Ajo bloqueado en cualquier cantidad para perros y gatos
    Given una mascota de cualquier especie
    And el plan propone "ajo" como condimento
    When el food_toxicity_checker verifica
    Then "ajo" es eliminado — es tóxico para perros y gatos en cualquier dosis
    And se registra en agent_traces

  # ─── RESTRICCIONES POR CONDICIÓN MÉDICA ─────────────────────────────────────

  Scenario: Dieta renal — fósforo y proteína restringidos
    Given una mascota tiene la condición "renal"
    When se genera el plan
    Then el plan no contiene ingredientes con alto contenido de fósforo
    And la proteína se limita al rango permitido por NRC para condición renal
    And estas restricciones se aplican ANTES de que el LLM genere el plan

  Scenario: Dieta diabética — carbohidratos simples restringidos
    Given una mascota tiene la condición "diabético"
    When se genera el plan
    Then el plan no contiene azúcares simples ni carbohidratos de alto índice glucémico
    And prioriza fuentes de proteína magra y fibra soluble

  Scenario: Pancreatitis — grasa severamente restringida
    Given una mascota tiene la condición "pancreático"
    When se genera el plan
    Then el contenido de grasa del plan es inferior al 10% de la materia seca
    And no contiene carnes grasas (cerdo, cordero graso, piel de pollo)
    And incluye advertencia sobre riesgo de recaída con grasas

  Scenario: Hepatopatía/hiperlipidemia — proteína moderada y sin grasas saturadas
    Given una mascota tiene la condición "hepático/hiperlipidemia"
    When se genera el plan
    Then el plan limita proteína de alta densidad
    And elimina grasas saturadas
    And prioriza carbohidratos de fácil digestión

  Scenario: Condición cancerígena — sin azúcares fermentables
    Given una mascota tiene la condición "cancerígeno"
    When se genera el plan
    Then el plan elimina azúcares fermentables
    And aumenta el contenido de omega-3 antiinflamatorio
    And requiere revisión veterinaria obligatoria (PENDING_VET)

  Scenario: Múltiples condiciones — restricciones acumulativas
    Given una mascota tiene las condiciones "diabético" y "renal" y "gastritis"
    When el food_toxicity_checker aplica las restricciones
    Then se aplican las restricciones de las 3 condiciones simultáneamente
    And si hay conflicto entre restricciones, se aplica la más restrictiva
    And el modelo LLM seleccionado es "gpt-4o" (3+ condiciones)

  # ─── ALERGIAS ────────────────────────────────────────────────────────────────

  Scenario: Alergia conocida excluye el alérgeno del plan
    Given una mascota tiene alergia registrada a "pollo"
    When se genera el plan
    Then "pollo" no aparece en ningún ingrediente del plan
    And tampoco aparecen derivados de pollo (caldo de pollo, harina de pollo)

  Scenario: Alerta cuando no se conocen alergias
    Given una mascota tiene alergia registrada como "no sabe"
    When el owner solicita el plan
    Then el sistema muestra alerta obligatoria antes de continuar
    And la alerta recomienda realizar prueba de alérgenos
    And el owner debe confirmar explícitamente ("Entiendo el riesgo, continuar")
    And el plan generado incluye nota de advertencia sobre alergias desconocidas

  # ─── GARANTÍA DE GUARDARRAÍLES ───────────────────────────────────────────────

  Scenario: LLM no puede sobrescribir restricciones hard-coded
    Given el food_toxicity_checker prohíbe "fósforo alto" para condición renal
    And el LLM sugiere "sardinas" (alto en fósforo) en su respuesta
    When el sistema valida el output del LLM
    Then "sardinas" es removido del plan
    And se registra el intento en agent_traces
    And el plan se finaliza con ingredientes permitidos

  Scenario: Verificación post-LLM garantiza cero toxinas
    Given cualquier plan generado por cualquier modelo LLM
    When el plan pasa por la verificación final de toxicidad
    Then el plan no contiene ningún ingrediente de TOXIC_DOGS (si es perro)
    And el plan no contiene ningún ingrediente de TOXIC_CATS (si es gato)
    And el plan no contiene ningún ingrediente prohibido para las condiciones de la mascota
