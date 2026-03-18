# NFR Requirements — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Pet Service

### NFR-PET-01: AES-256 para Datos Médicos
- Las condiciones médicas DEBEN encriptarse con AES-256 (Fernet) en reposo en PostgreSQL.
- La clave AES se provee exclusivamente via variable de entorno `AES_ENCRYPTION_KEY`.
- Nunca se almacena ni loggea la clave ni los datos desencriptados.
- Verificado en test: el campo `condiciones_medicas_encrypted` en DB es `bytes`, no `text`.

### NFR-PET-02: Límites de Tier Aplicados
- Los límites de mascotas por tier se validan antes de cada creación.
- Verificado con tests parametrizados: free(1), básico(1), premium(3), vet(∞).
- Retorna HTTP 402 con mensaje específico si se excede el límite.

### NFR-PET-03: WeightRecord Append-Only
- No debe existir ningún endpoint PATCH/DELETE para `weight_records`.
- El repositorio no tiene método `update()` ni `delete()` para WeightRecord.
- Verificado en test: intentar UPDATE en weight_records → error de dominio.

### NFR-PET-04: 0 PII en Logs del Pet Service
- Logs no contienen: nombre de mascota, condiciones médicas, alergias, peso.
- Solo se loggea: `pet_id (UUID)`, `event`, `owner_id (UUID)`.
- Verificado en code review de los handlers y repositorios.

### NFR-PET-05: Cobertura de Tests ≥ 80%
- `pytest --cov=app/application/pets tests/pets/ --cov-fail-under=80`
- Tests obligatorios: crear pet (happy), crear pet tier excedido, actualizar con condición nueva, registrar peso, claim code flujo completo.

### NFR-PET-06: Validación de Consistencia de Especie
- `talla` para gatos → HTTP 422 (siempre).
- `nivel_actividad` de gato para perro → HTTP 422 (siempre).
- Verificado en test con casos edge por especie.

### NFR-PET-07: Latencia de CRUD ≤ 200ms (p95)
- Los endpoints CRUD de pet deben responder en ≤ 200ms en p95 (sin generación de plan).
- Depende de: índice en `owner_id`, pool de conexiones SQLAlchemy, sin llamadas externas.

### NFR-PET-08: Borrado Lógico Siempre
- Nunca DELETE físico de un PetProfile.
- Verificado en test: deactivate_pet → is_active=False, pet sigue en DB.

### NFR-PET-09: Claim Code — Single Use
- Un claim code solo puede usarse una vez.
- Intentar reusar un código → HTTP 410 Gone.
- Verificado en test: claim exitoso → segundo claim con mismo código → 410.

### NFR-PET-10: Migración Alembic Obligatoria
- Todo cambio de schema en `pets`, `weight_records`, `claim_codes`, `clinic_pets` → Alembic.
- Nunca `ALTER TABLE` directo en staging o producción.
