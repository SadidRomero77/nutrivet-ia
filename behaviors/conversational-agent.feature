# language: es

Feature: Agente Conversacional Nutricional
  Como owner de mascota
  Quiero interactuar con el agente de inteligencia artificial
  Para resolver dudas sobre nutrición y ajustar el plan de mi mascota

  Background:
    Given el owner está autenticado
    And tiene una mascota con plan nutricional activo

  # ─── CONSULTAS NUTRICIONALES — AGENTE RESPONDE ───────────────────────────────

  Scenario: Owner pregunta por alternativa a un ingrediente
    Given el plan incluye "quinoa" como fuente de carbohidrato
    When el owner pregunta "No consigo quinoa, ¿qué puedo usar?"
    Then el agente sugiere alternativas nutricionalmente equivalentes (ej. arroz integral, avena)
    And verifica que las alternativas no están en TOXIC_DOGS/TOXIC_CATS
    And verifica que las alternativas no están prohibidas por condiciones médicas de la mascota
    And explica la equivalencia nutricional en lenguaje simple

  Scenario: Owner pregunta por cantidades del plan
    Given el plan indica 80g de pollo por ración
    When el owner pregunta "¿Puedo dar 100g de pollo en vez de 80g?"
    Then el agente evalúa si el ajuste mantiene el DER dentro del rango aceptable (±10%)
    And responde con el impacto calórico del cambio
    And recomienda si es viable o no

  Scenario: Owner pregunta sobre nutrición básica
    When el owner pregunta "¿Por qué los perros necesitan taurina?"
    Then el agente responde con información nutricional precisa basada en literatura NRC/AAFCO
    And no hace recomendaciones de cambio al plan sin que el owner lo solicite

  Scenario: Owner solicita ajuste dentro del rango permitido
    When el owner dice "Mi perro no quiere comer brócoli, ¿puedo cambiarlo?"
    Then el agente sugiere un vegetal alternativo de valor nutricional similar
    And registra el ajuste en el historial conversacional
    And si el plan tiene condición médica y el ajuste es significativo → notifica al vet asignado

  # ─── LÍMITE CONVERSACIONAL — AGENTE DERIVA ───────────────────────────────────

  Scenario: Owner hace pregunta médica — agente deriva al vet
    When el owner pregunta "Mi perro está vomitando mucho, ¿qué hago?"
    Then el agente clasifica la intención como "médica"
    And NO responde la pregunta médica
    And emite un mensaje estructurado de derivación:
      "Esta pregunta está fuera del alcance de la asesoría nutricional. Te recomiendo contactar a tu veterinario de confianza."
    And ofrece el contacto del vet asignado si el owner tiene plan con condición médica

  Scenario: Owner pregunta sobre medicamentos — agente deriva al vet
    When el owner pregunta "¿Puedo darle metformina con la comida?"
    Then el agente reconoce que es una consulta sobre medicamentos
    And NO responde
    And deriva al vet con mensaje de urgencia moderada

  Scenario: Owner describe síntoma grave — agente emite alerta de emergencia
    When el owner dice "Mi gato no ha comido en 2 días y está muy decaído"
    Then el agente reconoce señal de emergencia clínica
    And emite alerta: "Esto puede ser urgente. Lleva a tu mascota al veterinario lo antes posible."
    And proporciona el contacto del vet asignado
    And registra el evento como "medical_emergency_detected" en agent_traces

  Scenario: Owner pregunta sobre diagnóstico — agente deriva
    When el owner pregunta "¿Mi perro podría tener diabetes?"
    Then el agente deriva al vet
    And explica: "El diagnóstico de enfermedades es responsabilidad del médico veterinario"

  # ─── LÍMITES DEL PLAN FREE ───────────────────────────────────────────────────

  Scenario: Owner Free agota sus preguntas diarias
    Given el owner tiene tier "Free"
    And ya realizó 3 preguntas hoy
    When el owner intenta hacer una cuarta pregunta
    Then el agente responde: "Has alcanzado el límite de preguntas del plan gratuito para hoy"
    And muestra información sobre el plan Básico y sus beneficios
    And no procesa la pregunta

  Scenario: Owner Free agota los 3 días de acceso
    Given el owner tiene tier "Free"
    And ya usó el agente durante 3 días
    When el owner intenta hacer cualquier pregunta el cuarto día
    Then el agente responde únicamente con mensaje de upgrade
    And bloquea cualquier interacción hasta que el owner actualice su plan

  # ─── CONTEXTO DEL PLAN ACTIVO ────────────────────────────────────────────────

  Scenario: Agente siempre tiene contexto del plan activo
    Given la mascota tiene un plan activo con ingredientes específicos
    When el owner hace una pregunta sobre el plan
    Then el agente responde considerando el plan activo completo
    And no sugiere ingredientes que ya están prohibidos por el plan
    And no contradice las restricciones médicas del plan

  Scenario: Agente recuerda el historial de la conversación
    Given el owner en la misma sesión preguntó por alternativa a "pollo" y recibió "pavo"
    When el owner pregunta "¿Y cuánto pavo le doy?"
    Then el agente usa el contexto de la conversación previa
    And calcula la cantidad equivalente en gramos para la ración del plan
