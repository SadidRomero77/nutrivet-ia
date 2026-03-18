# language: es
# ═══════════════════════════════════════════════════════════════════════════════
# GOLDEN CASE — CASO SALLY
# Validado por: Lady Carolina Castañeda (MV, BAMPYSVET)
# Este escenario es BLOQUEANTE de release (Quality Gate G8)
# NO modificar sin validación veterinaria explícita
# ═══════════════════════════════════════════════════════════════════════════════

Feature: Golden Case — Sally (French Poodle, 5 condiciones médicas)
  Como sistema de nutrición veterinaria
  Quiero reproducir exactamente el caso clínico de Sally
  Para garantizar que el motor de cálculo y el agente funcionan correctamente

  Background:
    Given el sistema tiene el perfil de Sally cargado:
      | campo               | valor                                      |
      | nombre              | Sally                                      |
      | especie             | perro                                      |
      | raza                | French Poodle                              |
      | sexo                | hembra                                     |
      | edad                | 96 meses (8 años)                          |
      | peso                | 9.6 kg                                     |
      | talla               | pequeño S (4-9 kg)                         |
      | estado_reproductivo | esterilizado                               |
      | nivel_actividad     | sedentario                                 |
      | bcs                 | 6                                          |
      | alimentacion_actual | concentrado                                |
      | condiciones         | diabético, hepático/hiperlipidemia, gastritis, cistitis/enfermedad_urinaria, hipotiroideo |
      | alergias            | ninguna conocida                           |

  # ─── CÁLCULO RER/DER ─────────────────────────────────────────────────────────

  Scenario: RER de Sally calculado correctamente
    When el NRC Calculator calcula el RER para Sally
    Then RER = 70 × 9.6^0.75
    And el resultado es aproximadamente 396 kcal (tolerancia ±0.5 kcal)
    And el cálculo lo realiza Python — no el LLM

  Scenario: DER de Sally calculado correctamente
    Given RER ≈ 396 kcal
    And Sally es adulta senior esterilizada sedentaria con BCS 6
    When el NRC Calculator aplica los factores
    Then DER ≈ 534 kcal/día (tolerancia ±0.5 kcal)
    And el factor total aplicado es aproximadamente 1.35
    And la fase del plan es "mantenimiento" (BCS 6 → rango 4-6)

  # ─── LLM ROUTING ─────────────────────────────────────────────────────────────

  Scenario: GPT-4o seleccionado para Sally (5 condiciones)
    Given Sally tiene 5 condiciones médicas registradas
    When el orquestador determina el modelo LLM
    Then el modelo seleccionado es "gpt-4o"
    And el routing_key es 5 (≥ 3 → GPT-4o)

  # ─── HITL ────────────────────────────────────────────────────────────────────

  Scenario: Plan de Sally inicia en PENDING_VET
    Given Sally tiene condiciones médicas registradas
    When el agente genera el plan nutricional
    Then el plan.status es "PENDING_VET"
    And se notifica al veterinario asignado
    And el owner NO recibe el plan hasta aprobación veterinaria

  # ─── RESTRICCIONES ACUMULATIVAS ──────────────────────────────────────────────

  Scenario: Restricciones de 5 condiciones aplicadas simultáneamente en Sally
    When el food_toxicity_checker aplica las restricciones para Sally
    Then se aplican TODAS las restricciones acumulativamente:
      | condición                   | restricción principal                              |
      | diabético                   | sin azúcares simples, carbohidratos complejos solo |
      | hepático/hiperlipidemia     | sin grasas saturadas, proteína moderada            |
      | gastritis                   | sin irritantes (especias, ácidos), sin ayunos      |
      | cistitis/enfermedad_urinaria| sin fósforo alto, sin sodio excesivo               |
      | hipotiroideo                | sin bociogens (soya, col, brócoli crudo en exceso) |
    And donde hay conflicto entre restricciones, se aplica la más restrictiva
    And el LLM recibe solo la lista de ingredientes PERMITIDOS tras aplicar todas las restricciones

  Scenario: Ingredientes tóxicos bloqueados para Sally (perro)
    When el plan es verificado contra TOXIC_DOGS
    Then el plan no contiene: uvas, pasas, cebolla, ajo, xilitol, chocolate, macadamia, aguacate
    And esta verificación ocurre antes y después de la generación del LLM

  # ─── FORMATO DEL PLAN ────────────────────────────────────────────────────────

  Scenario: Plan de Sally incluye protocolo de transición
    Given la alimentación actual de Sally es "concentrado"
    And el plan generado es de modalidad "Natural"
    When el plan es generado
    Then incluye protocolo de transición de 7 días
    And el día 1-2: 75% concentrado + 25% natural
    And el día 3-4: 50% concentrado + 50% natural
    And el día 5-6: 25% concentrado + 75% natural
    And el día 7+:  100% natural

  # ─── TRAZABILIDAD ────────────────────────────────────────────────────────────

  Scenario: Trazabilidad completa del plan de Sally en agent_traces
    When el plan de Sally es generado
    Then agent_traces registra:
      | campo             | valor esperado                    |
      | pet_id            | UUID anónimo (sin nombre "Sally") |
      | model_used        | gpt-4o                            |
      | conditions_count  | 5                                 |
      | routing_decision  | gpt-4o                            |
      | der_kcal          | ~534 (±0.5)                       |
      | rer_kcal          | ~396 (±0.5)                       |
      | toxic_check_pass  | true                              |
      | restrictions_applied | 5 condiciones                  |
    And el registro es inmutable (no permite UPDATE posterior)
