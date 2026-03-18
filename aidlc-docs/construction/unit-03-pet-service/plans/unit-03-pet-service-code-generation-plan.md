# Plan: Code Generation — Unit 03: pet-service

**Unidad**: unit-03-pet-service
**Fase AI-DLC**: C4/C5 — Code Generation Plan
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Implementar el pet-service completo con TDD: PetProfile CRUD (13 campos), ClinicPet,
claim code, weight tracking append-only, encriptación AES-256 de campos médicos.

**Regla**: TDD obligatorio — tests PRIMERO, luego implementación.

---

## Pasos de Implementación

### Paso 1 — Estructura de Carpetas

- [ ] `backend/application/interfaces/pet_repository.py` — IPetRepository ABC
- [ ] `backend/application/interfaces/weight_repository.py` — IWeightRepository ABC
- [ ] `backend/application/interfaces/claim_code_repository.py` — IClaimCodeRepository ABC
- [ ] `backend/application/use_cases/pet_profile_use_case.py`
- [ ] `backend/application/use_cases/weight_tracking_use_case.py`
- [ ] `backend/application/use_cases/pet_claim_use_case.py`
- [ ] `backend/infrastructure/db/pet_repository.py`
- [ ] `backend/infrastructure/db/weight_repository.py`
- [ ] `backend/infrastructure/db/claim_code_repository.py`
- [ ] `backend/infrastructure/encryption/fernet_encryptor.py`
- [ ] `backend/presentation/routers/pet_router.py`
- [ ] `backend/presentation/schemas/pet_schemas.py`
- [ ] `tests/pet/test_pet_profile_use_case.py` (vacío)
- [ ] `tests/pet/test_weight_tracking_use_case.py` (vacío)
- [ ] `tests/pet/test_pet_claim_use_case.py` (vacío)

### Paso 2 — Tests RED: PetProfile Use Case

- [ ] Escribir `tests/pet/test_pet_profile_use_case.py`:
  - `test_crear_mascota_valida` — owner crea mascota con 13 campos → pet_id retornado
  - `test_free_tier_no_puede_crear_segunda_mascota` → 403
  - `test_premium_puede_crear_hasta_3_mascotas`
  - `test_talla_solo_requerida_para_perros` — perro sin talla → error
  - `test_gato_sin_talla_es_valido`
  - `test_activity_level_valido_por_especie` — indoor solo gatos
  - `test_bcs_fuera_de_rango_falla` — BCS 0 o BCS 10 → error
  - `test_peso_negativo_falla`
  - `test_condicion_medica_invalida_falla`
  - `test_condicion_medica_agrega_a_plan_activo_dispara_pending_vet`
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 3 — Tests RED: ClinicPet y Claim Code

- [ ] Escribir `tests/pet/test_pet_claim_use_case.py`:
  - `test_create_clinic_pet` — vet crea ClinicPet → claim_code generado (8 chars)
  - `test_vet_free_no_puede_crear_clinic_pet` → 403
  - `test_claim_code_expira_30_dias` — código expirado → 410 Gone
  - `test_claim_code_un_solo_uso` — segundo claim → 409 Conflict
  - `test_claim_convierte_clinic_pet_en_app_pet` — owner_id actualizado
  - `test_claim_code_8_chars_alfanumerico`
  - `test_claim_code_no_contiene_cero_ni_O`
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 4 — Tests RED: Weight Tracking

- [ ] Escribir `tests/pet/test_weight_tracking_use_case.py`:
  - `test_peso_append_only` — agregar registro → ID retornado
  - `test_peso_negativo_rechazado`
  - `test_historial_paginado_default_30`
  - `test_no_existe_metodo_update_weight` — verificar que IWeightRepository no tiene update()
  - `test_owner_puede_ver_historial_propio`
  - `test_owner_no_puede_ver_historial_ajeno` → 403
- [ ] Verificar que todos los tests FALLAN (RED)

### Paso 5 — GREEN: Interfaces y Use Cases

- [ ] Implementar `IPetRepository` ABC
- [ ] Implementar `IWeightRepository` ABC (sin update())
- [ ] Implementar `IClaimCodeRepository` ABC
- [ ] Implementar `PetProfileUseCase`:
  - `create_pet(owner_id, pet_data, user_tier)` — valida límites de tier
  - `get_pet(pet_id, requester_id, requester_role)` — valida RBAC
  - `update_pet(pet_id, update_data, requester_id)` — valida condición médica → plan PENDING_VET
  - `list_pets(owner_id)` — lista mascotas del owner
- [ ] Implementar `WeightTrackingUseCase`:
  - `add_weight_record(pet_id, weight_kg, bcs, recorded_by)`
  - `get_weight_history(pet_id, requester_id, limit, offset)`
- [ ] Implementar `PetClaimUseCase`:
  - `create_clinic_pet(vet_id, pet_data, owner_name, owner_phone)`
  - `claim_pet(code, owner_id)` — transacción atómica

### Paso 6 — Alembic Migrations

- [ ] `alembic revision -m "003_pets"` → crear tabla `pets`
- [ ] `alembic revision -m "004_weight_records"` → crear tabla `weight_records` + índice
- [ ] `alembic revision -m "005_claim_codes"` → crear tabla `claim_codes` + índice
- [ ] Revisar migraciones generadas — verificar que BYTEA, índices y constraints están correctos
- [ ] Confirmar con Sadid antes de `alembic upgrade head` en staging

### Paso 7 — PostgreSQLPetRepository con AES-256

- [ ] Implementar `FernetEncryptor` (encrypt/decrypt JSONB fields)
- [ ] Implementar `PostgreSQLPetRepository` (asyncpg):
  - Encripta `medical_conditions` y `allergies` en `save()`
  - Desencripta en `find_by_id()` y `list_by_owner()`
- [ ] Implementar `PostgreSQLWeightRepository` (append-only)
- [ ] Implementar `PostgreSQLClaimCodeRepository` (SELECT FOR UPDATE en claim)

### Paso 8 — FastAPI Endpoints (8 endpoints)

- [ ] `POST /v1/pets` — crear AppPet (owner)
- [ ] `GET /v1/pets` — listar mascotas del owner
- [ ] `GET /v1/pets/{pet_id}` — obtener mascota
- [ ] `PATCH /v1/pets/{pet_id}` — actualizar mascota
- [ ] `POST /v1/pets/{pet_id}/weight` — agregar registro de peso
- [ ] `GET /v1/pets/{pet_id}/weight` — historial de peso paginado
- [ ] `POST /v1/pets/clinic` — crear ClinicPet (vet only)
- [ ] `POST /v1/pets/claim` — reclamar mascota con código (owner)

### Paso 9 — Cobertura y Calidad

- [ ] `pytest --cov=backend/application/use_cases tests/pet/ --cov-fail-under=80`
- [ ] `ruff check backend/` → 0 errores en pet-service modules
- [ ] `bandit -r backend/` → 0 HIGH/MEDIUM
- [ ] Verificar que `medical_conditions` en DB es BYTEA (ciphertext) — no texto plano
- [ ] Verificar claim code TTL y single-use funcionando

---

## Criterios de Done

- [ ] Los 8 endpoints funcionales con tests de integración
- [ ] AES-256 (Fernet) encriptando campos médicos en DB
- [ ] Claim code: TTL 30 días, single-use, 8 chars alfanumérico seguro
- [ ] Weight tracking append-only — no existe PATCH en el router
- [ ] Límites de tier aplicados (Free: 1, Básico: 1, Premium: 3, Vet: ilimitado)
- [ ] Cobertura ≥ 80% en use cases y repository
- [ ] Ruff + bandit sin errores

## Tiempo Estimado

4-5 días (incluye TDD + Alembic migrations + encriptación)

## Dependencias

- Unit 01 (domain-core): PetProfile aggregate, value objects BCS, PositiveDecimal
- Unit 02 (auth-service): JWT middleware, RBAC decorators

## Referencias

- Unit spec: `inception/units/unit-03-pet-service.md`
- Constitution: REGLA 6 (AES-256)
- Construction rules: `.claude/rules/02-construction.md`
