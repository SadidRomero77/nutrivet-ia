# language: es

Feature: Scanner OCR de Etiquetas Nutricionales
  Como owner de mascota
  Quiero escanear la etiqueta de un alimento concentrado
  Para saber si es adecuado para mi mascota y cuánto darle

  Background:
    Given el owner está autenticado
    And tiene una mascota con perfil completo

  # ─── HAPPY PATH ──────────────────────────────────────────────────────────────

  Scenario: Escaneo exitoso de tabla nutricional
    Given el owner toma una foto de la tabla nutricional de un concentrado
    When envía la imagen al scanner
    Then el agente OCR (Qwen2.5-VL-7B local) extrae: proteína, grasa, fibra, humedad, cenizas
    And calcula la cantidad diaria recomendada en gramos según el DER de la mascota
    And muestra un semáforo de evaluación: verde (apto) / amarillo (revisar) / rojo (no recomendado)
    And el resultado se evalúa contra el perfil completo de la mascota

  Scenario: Escaneo exitoso de lista de ingredientes
    Given el owner toma una foto de la lista de ingredientes del alimento
    When envía la imagen al scanner
    Then el agente extrae los ingredientes en orden de proporción
    And verifica si algún ingrediente está en TOXIC_DOGS o TOXIC_CATS según la especie
    And verifica si algún ingrediente está prohibido por las condiciones médicas de la mascota
    And muestra resultado con ingredientes marcados como seguros, a revisar o problemáticos

  Scenario: Alimento con ingrediente tóxico detectado
    Given la lista de ingredientes contiene "cebolla en polvo"
    And la mascota es un "perro"
    When el scanner analiza los ingredientes
    Then el resultado marca "cebolla en polvo" en rojo
    And muestra alerta: "Este ingrediente es tóxico para perros"
    And el semáforo final es "ROJO — No recomendado"

  Scenario: Alimento medicado detectado
    Given la tabla nutricional o ingredientes indica que es una dieta medicada (ej. "urinary", "renal", "hepatic")
    When el scanner analiza el alimento
    Then el sistema reconoce que es un alimento terapéutico
    And muestra alerta: "Este alimento es una dieta medicada — consulta con tu veterinario antes de usarlo"
    And redirige la consulta al vet si el owner hace preguntas sobre dosificación

  # ─── VALIDACIÓN DE IMAGEN ────────────────────────────────────────────────────

  Scenario: Imagen de logo o marca rechazada
    Given el owner toma una foto del empaque frontal del alimento (logo, marca, imagen del producto)
    When envía la imagen al scanner
    Then el sistema rechaza la imagen con mensaje:
      "Por favor, fotografía únicamente la tabla nutricional o la lista de ingredientes"
    And no realiza análisis de la imagen rechazada
    And no registra ningún dato de marca o logo

  Scenario: Imagen borrosa o de baja calidad rechazada
    Given el owner envía una imagen borrosa donde el texto no es legible
    When el OCR intenta procesar la imagen
    Then el sistema responde: "La imagen no tiene suficiente calidad para el análisis. Por favor, toma una foto más nítida."
    And sugiere condiciones de iluminación para mejor resultado

  Scenario: Imagen válida pero con información incompleta
    Given la imagen muestra solo parte de la tabla nutricional (cortada)
    When el OCR extrae los datos disponibles
    Then el sistema analiza los datos disponibles
    And indica qué nutrientes no pudieron extraerse
    And la evaluación se marca como "Análisis parcial"

  # ─── PRIVACIDAD E IMPARCIALIDAD ──────────────────────────────────────────────

  Scenario: Sistema nunca identifica ni registra marcas
    Given cualquier imagen enviada al scanner
    When el OCR procesa la imagen
    Then el sistema NO extrae ni almacena nombres de marcas
    And NO extrae ni almacena logos
    And el análisis se basa ÚNICAMENTE en composición nutricional e ingredientes
    And el LabelScan almacenado no contiene datos de marca

  Scenario: Resultado evaluado contra perfil completo de la mascota
    Given el owner escanea un concentrado con 28% proteína y 15% grasa
    And la mascota es un perro adulto sedentario con condición "pancreático"
    When el sistema evalúa el alimento
    Then detecta que 15% de grasa excede el límite para condición pancreática
    And el semáforo muestra "ROJO — Alto contenido de grasa, no recomendado para pancreatitis"
    And sugiere buscar un concentrado con < 10% de grasa

  # ─── OCR SIEMPRE LOCAL ───────────────────────────────────────────────────────

  Scenario: OCR siempre usa modelo local Qwen2.5-VL
    Given cualquier imagen enviada al scanner
    When el sistema procesa la imagen
    Then el modelo utilizado es siempre "Qwen2.5-VL-7B" via Ollama (local)
    And la imagen NO se envía a ningún proveedor de LLM externo
    And el LabelScan registra "model_used: qwen2.5-vl-7b-local"
