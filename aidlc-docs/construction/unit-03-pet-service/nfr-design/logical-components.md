# Logical Components — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Componentes Lógicos del Pet Service

### PetProfileUseCase
**Responsabilidad**: CRUD de PetProfile — create, update, get, list, soft-delete.
**Capa**: application/pets/
**Dependencias**: PetRepositoryPort, TierLimitsChecker, MedicalDataEncryptor
**Métodos principales**:
```
create_pet(owner_id, create_request) → PetProfile
update_pet(pet_id, owner_id, update_request) → PetProfile
get_pet(pet_id, requester_id) → PetProfile
list_pets(owner_id) → list[PetProfile]
deactivate_pet(pet_id, owner_id) → None
```

### WeightTrackingUseCase
**Responsabilidad**: Gestión append-only del historial de peso.
**Capa**: application/pets/
**Dependencias**: WeightRepositoryPort, PetRepositoryPort
**Métodos**:
```
record_weight(pet_id, peso_kg, bcs, recorded_by) → WeightRecord
get_weight_history(pet_id) → list[WeightRecord]
get_current_weight(pet_id) → WeightRecord
```

### PetClaimUseCase
**Responsabilidad**: Generación y uso de claim codes para vincular mascota vet↔owner.
**Capa**: application/pets/
**Dependencias**: ClaimCodeRepository, PetRepositoryPort, TierLimitsChecker
**Métodos**:
```
generate_claim_code(pet_id, vet_id) → ClaimCode
claim_pet(code, owner_id) → PetProfile
```

### PostgreSQLPetRepository
**Responsabilidad**: Persistencia de PetProfile con encriptación AES-256 de condiciones médicas.
**Capa**: infrastructure/pets/
**Implementa**: PetRepositoryPort

### PostgreSQLWeightRepository
**Responsabilidad**: Persistencia append-only de WeightRecord.
**Capa**: infrastructure/pets/
**Regla crítica**: Nunca UPDATE — solo INSERT.

### MedicalDataEncryptor
**Responsabilidad**: Encriptar/desencriptar `condiciones_medicas` con AES-256.
**Capa**: infrastructure/pets/
**Invocado por**: PostgreSQLPetRepository (transparente para la aplicación)

### PetsRouter
**Responsabilidad**: Endpoints HTTP del pet service.
**Capa**: presentation/pets/
**Endpoints**:
```
POST   /pets                       → 201 PetProfile
GET    /pets                       → 200 list[PetProfile]
GET    /pets/{pet_id}              → 200 PetProfile
PATCH  /pets/{pet_id}              → 200 PetProfile
DELETE /pets/{pet_id}              → 204 (soft delete)
POST   /pets/{pet_id}/weight       → 201 WeightRecord
GET    /pets/{pet_id}/weight       → 200 list[WeightRecord]
POST   /pets/{pet_id}/claim-code   → 201 ClaimCode (vet only)
POST   /pets/claim                 → 200 PetProfile (owner only)
```

## Diagrama de Dependencias

```
PetsRouter (presentation)
    ↓
PetProfileUseCase / WeightTrackingUseCase / PetClaimUseCase (application)
    ↓
PetRepositoryPort ←─── PostgreSQLPetRepository (infrastructure)
                             ↓
                    MedicalDataEncryptor (infrastructure)
                    SQLAlchemy + asyncpg → PostgreSQL
```

## Validaciones de Pydantic en Presentation

```python
class CreatePetRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    especie: Literal["perro", "gato"]
    raza: str = Field(min_length=1)
    sexo: Literal["macho", "hembra"]
    edad_valor: int = Field(gt=0)
    edad_unidad: Literal["meses", "años"]
    peso_kg: Decimal = Field(gt=0)
    talla: TallaEnum | None = None
    estado_reproductivo: Literal["esterilizado", "no_esterilizado"]
    nivel_actividad: str
    bcs: int = Field(ge=1, le=9)
    condiciones_medicas: list[str] = []
    alergias: list[str] = []
    alimentacion_actual: Literal["concentrado", "natural", "mixto"]

    @model_validator(mode="after")
    def validate_especie_consistency(self):
        """Validar que talla y nivel_actividad sean consistentes con especie."""
        if self.especie == "gato" and self.talla is not None:
            raise ValueError("Los gatos no tienen talla")
        return self
```
