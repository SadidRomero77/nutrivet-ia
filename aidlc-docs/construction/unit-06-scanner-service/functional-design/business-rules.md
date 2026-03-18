# Business Rules — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Scanner Service

### BR-SCAN-01: Solo Tabla Nutricional o Lista de Ingredientes
- SOLO se aceptan imágenes de: tabla nutricional o lista de ingredientes.
- NUNCA se acepta: imagen de marca, logo, empaque frontal, foto del producto completo.
- Si la imagen no corresponde a ningún tipo aceptado → `ScanStatus.REJECTED` con explicación.
- El `ImageValidator` verifica esto antes de hacer OCR.
- Principio: imparcialidad y cautela — no queremos que la marca influya en la evaluación.

### BR-SCAN-02: OCR Siempre con gpt-4o (Vision)
- El modelo OCR es SIEMPRE `openai/gpt-4o` via OpenRouter, para todos los tiers.
- No se puede usar un modelo inferior para OCR, independientemente del tier.
- La precisión del OCR es crítica para la seguridad del paciente.
- Quality Gate G4: ≥85% OCR success rate.

### BR-SCAN-03: Semáforo — Lógica Determinista
El color del semáforo se determina por reglas hard-coded, no por LLM:
- **RED** (inmediato): cualquier ingrediente en TOXIC_DOGS/TOXIC_CATS para la especie del pet.
- **RED** (inmediato): cualquier ingrediente en RESTRICTIONS_BY_CONDITION de las condiciones del pet.
- **RED** (inmediato): alérgeno conocido del pet encontrado en ingredientes.
- **YELLOW**: ingrediente con restricción leve (ej: alto en sodio para cistitis, pero no prohibido).
- **GREEN**: ningún problema encontrado.
- El LLM puede generar el texto de `recommendation` pero NO determina el color del semáforo.

### BR-SCAN-04: Nunca Mostrar Nombre de Marca
- El scanner no muestra ni almacena el nombre de la marca del producto escaneado.
- El resultado se presenta como evaluación nutricional anónima.
- Principio de imparcialidad: NutriVet.IA no promueve ni demuele marcas.
- El vet puede agregar su propio comentario sobre el producto (post-MVP).

### BR-SCAN-05: Evaluación Contra Perfil Completo del Pet
- La evaluación incluye: especie, condiciones médicas, alergias, BCS, nivel de actividad.
- No es una evaluación genérica — es específica para el perfil de la mascota.
- Las condiciones médicas se desencriptan para la evaluación y se re-encriptan al guardar.

### BR-SCAN-06: Imagen Almacenada en R2
- La imagen del escaneo se sube a Cloudflare R2 antes de enviar al OCR.
- R2 key: `scans/{owner_id}/{scan_id}.{ext}`
- La imagen se retiene 90 días en R2, luego se elimina (datos temporales).
- Nunca se almacena la imagen en PostgreSQL (solo la clave R2).

### BR-SCAN-07: OCR Success Rate
- Si el texto extraído tiene < 10 palabras o no tiene estructura de tabla → `ScanStatus.FAILED` con sugerencia de re-intentar con mejor imagen.
- El success rate se monitorea: alerta P2 si cae por debajo de 85%.
