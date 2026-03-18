# Business Logic Model — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos de Lógica del Pet Service

### Flujo 1: Crear PetProfile (Wizard Completo)

```
POST /pets { 13 campos }
  ↓
1. Validar Pydantic schema (CreatePetRequest) — 13 campos obligatorios
2. Validar consistencia especie:
   - gato + talla → error 422
   - perro + nivel_actividad de gato → error 422
3. Verificar límite de tier: owner.tier vs TIER_LIMITS[tier]["mascotas"]
   → Si excede: HTTP 402 con mensaje "Actualiza tu plan para agregar más mascotas"
4. Validar condiciones médicas (cada una ∈ VALID_CONDITIONS)
5. Validar alergias (si "no_sabe" no combinar con otros)
6. Encriptar condiciones_medicas con AES-256
7. Crear PetProfile + WeightRecord inicial (peso del wizard)
8. Persistir en PostgreSQL (transacción atómica)
9. Retornar PetProfile + HTTP 201
```

### Flujo 2: Actualizar PetProfile

```
PATCH /pets/{pet_id} { campos a actualizar }
  ↓
1. Verificar ownership: pet.owner_id == current_user.user_id
2. Validar solo campos permitidos (no se puede cambiar especie post-creación)
3. Si condiciones_medicas cambia → detectar condiciones nuevas agregadas
   a. Si nuevo plan ACTIVE existe → transicionar plan a UNDER_REVIEW
   b. Crear alerta para el owner
4. Si alergias cambia a ["no_sabe"] → crear alerta de test de alérgenos
5. Re-encriptar condiciones_medicas si cambian
6. Actualizar updated_at = now()
7. Retornar PetProfile actualizado + HTTP 200
```

### Flujo 3: Registrar Peso

```
POST /pets/{pet_id}/weight { peso_kg, bcs, notes? }
  ↓
1. Verificar ownership o vet vinculado
2. Validar peso_kg > 0
3. Validar bcs en [1, 9]
4. Crear WeightRecord (append-only — nunca UPDATE existente)
5. Actualizar pet_profile.peso_kg y pet_profile.bcs con nuevos valores
6. Evaluar si BCS cambió de fase (reducción/mantenimiento/aumento)
   → Si cambia de fase → notificar al owner (push notification)
7. Retornar WeightRecord + HTTP 201
```

### Flujo 4: Generar Claim Code (vet → owner)

```
POST /pets/{pet_id}/claim-code (requiere rol vet)
  ↓
1. Verificar que el vet está vinculado a la mascota (ClinicPet)
2. Generar código: secrets.token_urlsafe(6).upper() → 8 chars
3. Crear ClaimCode(expires_at = now() + 30 días)
4. Persistir en PostgreSQL
5. Retornar { code, expires_at } + HTTP 201
```

### Flujo 5: Reclamar Mascota (owner usa claim code)

```
POST /pets/claim { code }
  ↓
1. Buscar ClaimCode por code
2. Verificar: no expirado + not is_used
3. Verificar límite de mascotas del owner
4. Crear vínculo: pet.owner_id = current_user.user_id
5. Marcar ClaimCode.is_used = True, ClaimCode.claimed_by = owner_id
6. Crear ClinicPet para mantener relación vet-mascota
7. Retornar PetProfile + HTTP 200
```

### Flujo 6: Listar Mascotas del Owner

```
GET /pets (requiere access token)
  ↓
1. Buscar pets WHERE owner_id = current_user.user_id AND is_active = True
2. Ordenar por created_at DESC
3. Para cada pet: incluir último WeightRecord
4. Retornar list[PetProfile] + HTTP 200
```
