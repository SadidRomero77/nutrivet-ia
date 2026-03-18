# language: es

Feature: Revisión Veterinaria HITL
  Como veterinario con rol "vet"
  Quiero revisar, editar y aprobar planes nutricionales de mis pacientes
  Para garantizar la seguridad clínica de mascotas con condición médica

  Background:
    Given un veterinario autenticado con rol "vet"
    And un plan en estado "PENDING_VET" para una mascota con condición médica

  # ─── APROBACIÓN ──────────────────────────────────────────────────────────────

  Scenario: Veterinario aprueba el plan directamente
    Given el plan fue generado para una mascota con "gastritis"
    When el veterinario aprueba el plan sin modificaciones
    Then el plan pasa a estado "ACTIVE"
    And se registra "approved_by_vet_id" y "approval_timestamp"
    And el owner recibe notificación push "Tu plan fue aprobado por el veterinario"

  Scenario: Veterinario aprueba plan temporal con review_date
    Given la mascota tiene condición médica activa
    When el veterinario aprueba el plan con review_date "2026-06-01"
    Then el plan pasa a tipo "temporal_medical" con status "ACTIVE"
    And review_date queda registrado como "2026-06-01"
    And el sistema programará revisión automática en esa fecha

  # ─── EDICIÓN CON JUSTIFICACIÓN ───────────────────────────────────────────────

  Scenario: Veterinario edita el plan antes de aprobar
    Given el plan propone "arroz blanco" para una mascota diabética
    When el veterinario reemplaza "arroz blanco" por "arroz integral"
    And agrega la justificación "Menor índice glucémico para control de diabetes"
    Then la edición queda registrada en plan_changes (append-only)
    And el plan pasa a estado "ACTIVE" con la modificación aplicada
    And el plan_changes incluye: vet_id, timestamp, campo modificado, justificación

  Scenario: Veterinario no puede sobrescribir restricciones hard-coded
    Given la mascota tiene condición "renal"
    And el sistema tiene la restricción "sin fósforo alto" para condición renal
    When el veterinario intenta agregar un ingrediente con alto fósforo
    Then el sistema rechaza la modificación con error "RestricciónMédicaBloqueante"
    And muestra el mensaje "Esta restricción es requerida por protocolo clínico NRC para condición renal"

  # ─── ACCESO Y SEGURIDAD ──────────────────────────────────────────────────────

  Scenario: Veterinario solo puede ver sus propios pacientes
    Given existe una mascota asignada a otro veterinario
    When el vet intenta acceder al plan de esa mascota
    Then el sistema responde con error 403 Forbidden
    And no se expone ninguna información de la mascota

  Scenario: Owner no puede aprobar un plan PENDING_VET
    Given el plan está en estado "PENDING_VET"
    When el owner intenta cambiar el estado a "ACTIVE"
    Then el sistema responde con error 403 Forbidden
    And el plan permanece en "PENDING_VET"

  # ─── CICLO DE VIDA POST-APROBACIÓN ──────────────────────────────────────────

  Scenario: Plan vuelve a PENDING_VET cuando owner agrega condición médica
    Given la mascota tiene un plan en estado "ACTIVE" sin condiciones médicas
    When el owner agrega la condición "diabético" al perfil de la mascota
    Then el plan pasa automáticamente a "PENDING_VET"
    And se notifica al veterinario asignado
    And el owner recibe notificación "Tu plan requiere revisión por nueva condición médica"

  Scenario: Plan temporal pasa a UNDER_REVIEW al alcanzar review_date
    Given el plan tiene review_date "2026-06-01"
    And hoy es "2026-06-01"
    When el sistema ejecuta el job de revisión diaria
    Then el plan pasa a "UNDER_REVIEW"
    And se notifica al veterinario para nueva revisión

  Scenario: Plan life_stage pasa a UNDER_REVIEW en milestone de 6 meses
    Given la mascota es un cachorro de 5 meses con plan "life_stage"
    When el cachorro cumple 6 meses
    Then el plan pasa a "UNDER_REVIEW"
    And se notifica al owner "Tu cachorro cumple 6 meses — es momento de actualizar el plan"
