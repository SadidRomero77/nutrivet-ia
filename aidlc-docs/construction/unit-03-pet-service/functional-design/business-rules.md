# Business Rules — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Pet Service

### BR-PET-01: 13 Campos Obligatorios
- Los 13 campos del PetProfile son obligatorios para crear un perfil válido.
- El wizard guarda borrador localmente en Hive (Flutter) hasta que los 13 campos estén completos.
- El borrador NUNCA se envía al backend hasta que todos los campos estén presentes.
- El backend valida la completitud del perfil en el endpoint de creación.

### BR-PET-02: Consistencia de Especie
- `talla` SOLO se acepta para especie == "perro". Para gatos: debe ser null/ausente.
- `nivel_actividad` para perros: sedentario/moderado/activo/muy_activo.
- `nivel_actividad` para gatos: indoor/indoor_outdoor/outdoor.
- Validación en Pydantic schema + invariante de dominio.

### BR-PET-03: Condiciones Médicas — AES-256
- El campo `condiciones_medicas` se encripta con AES-256 en reposo en PostgreSQL.
- En tránsito: siempre sobre HTTPS.
- En logs: NUNCA se incluyen las condiciones médicas en texto plano.
- Solo se usa el `pet_id (UUID)` en trazas de agente.

### BR-PET-04: Límites de Tier para Mascotas
- Free: máximo 1 mascota activa.
- Básico: máximo 1 mascota activa.
- Premium: máximo 3 mascotas activas.
- Vet: ilimitadas (pacientes de la clínica).
- Validado en `PetProfileUseCase.create_pet()` contra el tier del JWT.

### BR-PET-05: Historial de Peso — Append-Only
- `WeightRecord` es append-only. No existe UPDATE ni DELETE de registros de peso.
- Cada peso registrado crea un nuevo `WeightRecord`.
- El peso actual del pet es el último `WeightRecord.peso_kg`.
- Mínimo 1 registro de peso (el del wizard de creación).

### BR-PET-06: Claim Code — TTL 30 Días
- Un vet puede generar un `ClaimCode` para vincular una mascota a un owner.
- El código expira a los 30 días de creación.
- Solo se puede usar una vez (`is_used = True` tras el claim).
- El código es 8 caracteres alfanumérico, generado con `secrets.token_urlsafe(6)`.

### BR-PET-07: Borrado Lógico
- Las mascotas nunca se eliminan de la base de datos.
- `is_active = False` marca la mascota como inactiva.
- Los planes existentes de una mascota inactiva permanecen accesibles para histórico.

### BR-PET-08: Condición Médica Agregada a Plan Activo
- Si un owner agrega una condición médica a un `PetProfile` que ya tiene un plan `ACTIVE`:
  - El plan `ACTIVE` cambia a `UNDER_REVIEW`.
  - El sistema crea una alerta para que el owner genere un nuevo plan con la condición.
  - El vet debe revisar antes de que el plan vuelva a `ACTIVE`.

### BR-PET-09: "Ninguno conocido" en Condiciones
- Si el owner selecciona "Ninguno conocido" → `condiciones_medicas = []`.
- No se pueden combinar "Ninguno conocido" con otras condiciones.

### BR-PET-10: Alergias "No Sabe"
- Si `alergias = ["no_sabe"]` → alerta obligatoria en el flujo de plan.
- La alerta recomienda test de alérgenos antes de proceder.
- No bloquea la creación del perfil, solo alerta en el plan.
