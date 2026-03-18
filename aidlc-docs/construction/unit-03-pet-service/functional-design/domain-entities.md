# Domain Entities — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Pet Service

### PetProfile (Aggregate Raíz)
Los 13 campos obligatorios del perfil de mascota.
- `pet_id: UUID`
- `owner_id: UUID` — FK a UserAccount
- `nombre: str` — libre, max 50 chars
- `especie: Literal["perro", "gato"]`
- `raza: str` — texto libre + búsqueda en catálogo
- `sexo: Literal["macho", "hembra"]`
- `edad: AgeVO` — valor + unidad (meses/años)
- `peso_kg: Decimal` — > 0
- `talla: TallaEnum | None` — solo perros: mini_xs/pequeno_s/mediano_m/grande_l/gigante_xl
- `estado_reproductivo: Literal["esterilizado", "no_esterilizado"]`
- `nivel_actividad: ActivityLevelVO` — validado por especie
- `bcs: int` — 1–9 con selector visual en app
- `condiciones_medicas: list[MedicalConditionVO]` — encriptado AES-256 en DB
- `alergias: list[str]` — lista base + campo abierto
- `alimentacion_actual: Literal["concentrado", "natural", "mixto"]`
- `is_active: bool` — borrado lógico
- `created_at: datetime`
- `updated_at: datetime`

### WeightRecord
Historial de peso append-only. Nunca se modifica un registro existente.
- `record_id: UUID`
- `pet_id: UUID` — FK a PetProfile
- `peso_kg: Decimal` — > 0
- `bcs: int` — 1–9 (medido junto al peso)
- `recorded_at: datetime`
- `recorded_by: UUID` — owner_id o vet_id
- `notes: str | None`

### ClaimCode
Código para transferir una mascota de clinic (vet) a owner.
- `claim_id: UUID`
- `pet_id: UUID`
- `vet_id: UUID` — quien genera el claim
- `code: str` — 8 chars alfanumérico, único
- `expires_at: datetime` — TTL 30 días
- `is_used: bool`
- `claimed_by: UUID | None` — owner que reclamó

### ClinicPet
Relación entre una mascota y una clínica/vet.
- `clinic_pet_id: UUID`
- `pet_id: UUID`
- `vet_id: UUID`
- `linked_at: datetime`
- `is_active: bool`

## Value Objects

### TallaEnum (solo perros)
```python
class TallaEnum(str, Enum):
    MINI_XS  = "mini_xs"   # 1-4 kg
    PEQUENO_S = "pequeno_s" # 4-9 kg
    MEDIANO_M = "mediano_m" # 9-14 kg
    GRANDE_L  = "grande_l"  # 14-30 kg
    GIGANTE_XL = "gigante_xl"  # +30 kg
```

### ActivityLevelVO (validado por especie)
```python
ACTIVITY_LEVELS = {
    "perro": ["sedentario", "moderado", "activo", "muy_activo"],
    "gato":  ["indoor", "indoor_outdoor", "outdoor"],
}
```

### MedicalConditionVO
Las 13 condiciones soportadas como frozenset validado en construcción.
```python
VALID_CONDITIONS = frozenset([
    "diabético", "hipotiroideo", "cancerígeno", "articular", "renal",
    "hepático/hiperlipidemia", "pancreático", "neurodegenerativo",
    "bucal/periodontal", "piel/dermatitis", "gastritis",
    "cistitis/enfermedad_urinaria", "sobrepeso/obesidad"
])
```
