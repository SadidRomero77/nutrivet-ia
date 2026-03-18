# NFR Design Patterns — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Pet Service

### Patrón 1: Encriptación Transparente en el Repositorio
La encriptación AES-256 de condiciones médicas ocurre en el repositorio, no en el caso de uso.
- El caso de uso trabaja con `list[MedicalConditionVO]` en texto claro.
- El repositorio encripta antes de persistir y desencripta al leer.
- El caso de uso nunca ve bytes — transparencia completa.

```python
async def save(self, pet: PetProfile) -> None:
    encrypted = self._encryptor.encrypt([c.condition for c in pet.condiciones_medicas])
    model = PetModel(
        condiciones_medicas_encrypted=encrypted,
        ...  # resto de campos
    )
    await self._session.add(model)
```

### Patrón 2: Append-Only para WeightRecord (Auditabilidad)
`WeightRecord` es inmutable una vez insertado. El historial de peso es el audit trail de salud.
- No hay endpoint PATCH ni DELETE para weight records.
- Si un peso fue registrado incorrectamente → el owner registra una corrección como nuevo registro con nota.
- El peso "actual" es siempre el último registro por timestamp.

### Patrón 3: Soft Delete con Borrado Lógico
Las mascotas no se eliminan físicamente — `is_active = False`.
- Preserva historial de planes y conversaciones.
- Útil para auditoría veterinaria.
- Las queries de listado siempre filtran `WHERE is_active = TRUE`.

### Patrón 4: Claim Code con TTL y Single-Use
El claim code es un token de vida corta (30 días) y uso único.
- Generado con `secrets.token_urlsafe(6).upper()` — criptográficamente seguro.
- Una vez usado, `is_used = True` previene re-uso.
- TTL en la base de datos — job de limpieza borra expirados periódicamente.

### Patrón 5: Validación de Negocio en Application Layer
Los límites de tier se validan en el caso de uso, no en el repositorio.
- El repositorio no conoce el tier del usuario.
- El caso de uso recibe el tier del JWT y verifica antes de persistir.
```python
async def create_pet(self, owner: CurrentUser, request: CreatePetRequest) -> PetProfile:
    count = await self._pet_repo.count_active_by_owner(owner.user_id)
    limit = TIER_LIMITS[owner.tier]["mascotas"]
    if limit != "ilimitado" and count >= limit:
        raise TierLimitExceededError(f"Límite de mascotas para tier {owner.tier}: {limit}")
    ...
```

### Patrón 6: Eventos de Dominio para Side Effects
Cuando `condiciones_medicas` cambia, se emite un `MedicalConditionAddedEvent`.
- El event handler en application layer transiciona el plan a `UNDER_REVIEW`.
- Desacoplamiento: el pet service no llama directamente al plan service.
- Los eventos se despachan dentro de la misma transacción para consistencia.

### Patrón 7: índices PostgreSQL para Consultas Frecuentes
- `idx_pets_owner`: acceso a mascotas por owner en O(log n).
- `idx_weight_pet`: historial de peso ordenado — los últimos registros son los más consultados.
- Partial index `WHERE is_active = TRUE` reduce el tamaño del índice.
