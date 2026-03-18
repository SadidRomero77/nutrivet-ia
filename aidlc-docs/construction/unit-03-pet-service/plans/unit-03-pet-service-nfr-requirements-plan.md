# Plan: NFR Requirements — Unit 03: pet-service

**Unidad**: unit-03-pet-service
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del pet-service

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| GET /v1/pets/{id} | < 50ms p95 | Single row lookup por PK indexado |
| GET /v1/pets | < 100ms p95 | Lista paginada — máx 3 mascotas por owner |
| POST /v1/pets | < 100ms p95 | Insert + encrypt sensitive fields |
| PATCH /v1/pets/{id} | < 100ms p95 | Update + re-encrypt if sensitive changed |
| GET /v1/pets/{id}/weight | < 100ms p95 | Paginado, índice en pet_id + recorded_at |
| POST /v1/pets/{id}/weight | < 50ms p95 | Single INSERT |
| POST /v1/pets/clinic | < 150ms p95 | Insert + claim code generation |
| POST /v1/pets/claim | < 100ms p95 | Lookup claim code + update |

### Seguridad

**Encriptación en reposo (AES-256)**:
- Campos sensibles: `medical_conditions` (JSONB) y `allergies` (JSONB).
- Implementación: Python `cryptography.fernet` (AES-128-CBC con HMAC-SHA256).
- Clave: `FERNET_KEY` en variables de entorno — nunca en código.
- Encriptación/desencriptación en `infrastructure/db/pet_repository.py` — transparente para application layer.

**RBAC**:
- `owner` solo accede a sus propias mascotas (`owner_id == current_user.user_id`).
- `vet` solo accede a mascotas asignadas a su clínica (relación `vet_id` en tabla `pets`).
- Sin excepción: nunca retornar mascota de otro owner.

**Validación**:
- Los 13 campos validados via Pydantic antes de cualquier operación de persistencia.
- `weight_kg > 0` — validado como `PositiveDecimal` value object del domain.
- `bcs` entre 1 y 9 — validado como `BCS` value object del domain.
- `species` determina qué valores de `activity_level` y si `size` es requerido.

### Confiabilidad

- Weight records: append-only — el repository no expone método `update_weight()`.
- Claim codes: single-use garantizado via transacción atómica en DB (SELECT FOR UPDATE).
- Medical conditions: solo los 13 valores válidos aceptados (enum hard-coded en domain).

### Mantenibilidad

- Cobertura mínima: **80%** en módulos de pet-service.
- Type hints obligatorios. Docstrings en español.
- `ruff check` y `bandit -r` sin errores antes de PR.

## Checklist NFR pet-service

- [ ] GET /v1/pets/{id} p95 < 50ms (test de carga con k6 o pytest-benchmark)
- [ ] `medical_conditions` encriptado en DB — verificar con query directa que es ciphertext
- [ ] `allergies` encriptado en DB — mismo criterio
- [ ] Owner no puede ver mascotas de otro owner → 403
- [ ] Vet no puede ver pacientes de otro vet → 403
- [ ] Weight records solo append — no hay endpoint PATCH /weight/{id}
- [ ] Claim code single-use: segundo intento → 409
- [ ] Cobertura ≥ 80% en pet-service modules
- [ ] Ruff + bandit sin errores

## Referencias

- Global: `_shared/nfr-requirements.md`
- Unit spec: `inception/units/unit-03-pet-service.md`
- Constitution: REGLA 6 (AES-256 en reposo para datos médicos)
