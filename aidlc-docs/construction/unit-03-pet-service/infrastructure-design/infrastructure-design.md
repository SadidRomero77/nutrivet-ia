# Infrastructure Design — unit-03-pet-service
**Unidad**: unit-03-pet-service
**Fase**: Construction — Infrastructure Design
**Fecha**: 2026-03-16

## Componentes de Infraestructura

### AES-256 Encryption para Condiciones Médicas

```python
# infrastructure/pets/encrypted_fields.py
from cryptography.fernet import Fernet
import base64, os

class MedicalDataEncryptor:
    """Encripta/desencripta datos médicos con AES-256 (Fernet)."""

    def __init__(self):
        key = os.environ["AES_ENCRYPTION_KEY"]  # 32-byte base64
        self._fernet = Fernet(base64.urlsafe_b64encode(key.encode()[:32]))

    def encrypt(self, conditions: list[str]) -> bytes:
        """Encripta lista de condiciones médicas a bytes."""
        import json
        plaintext = json.dumps(conditions).encode()
        return self._fernet.encrypt(plaintext)

    def decrypt(self, encrypted: bytes) -> list[str]:
        """Desencripta bytes a lista de condiciones médicas."""
        import json
        plaintext = self._fernet.decrypt(encrypted)
        return json.loads(plaintext)
```

### PostgreSQLPetRepository

```python
# infrastructure/pets/pg_pet_repository.py
class PostgreSQLPetRepository(PetRepositoryPort):
    """Repositorio SQLAlchemy async para PetProfile."""

    async def save(self, pet: PetProfile) -> None:
        """Persiste PetProfile con condiciones médicas encriptadas."""
        encrypted = self._encryptor.encrypt(pet.condiciones_medicas_raw)
        # mapear entidad a ORM model, encriptar, insertar
        ...

    async def get_by_id(self, pet_id: UUID) -> PetProfile | None:
        """Obtener y desencriptar condiciones médicas al leer."""
        ...

    async def list_by_owner(self, owner_id: UUID) -> list[PetProfile]:
        """Listar mascotas activas del owner."""
        ...

    async def count_active_by_owner(self, owner_id: UUID) -> int:
        """Contar mascotas activas para verificar límite de tier."""
        ...
```

### SQLAlchemy ORM Models

```python
# infrastructure/pets/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import UUID, String, Numeric, Boolean, LargeBinary, TIMESTAMP

class PetModel(Base):
    __tablename__ = "pets"
    pet_id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.user_id"))
    condiciones_medicas_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary)
    # ... resto de campos
```

### Alembic Migration

```python
# migrations/versions/002_create_pets_tables.py
# alembic revision --autogenerate -m "create pets weight_records claim_codes clinic_pets"
# SIEMPRE revisar el script antes de aplicar en staging/prod
```

### Dependencias Python del Pet Service

```
sqlalchemy[asyncio]==2.0.28
asyncpg==0.29.0
cryptography==42.x.x      # AES-256 Fernet
alembic==1.13.x
pydantic==2.6.x
fastapi==0.110.0
```

## Integración con Domain Layer

```
PetProfileUseCase (application)
    ↓ llama
PetRepositoryPort (domain/ports) ← implementado por PostgreSQLPetRepository
MedicalConditionVO (domain)      ← validación de las 13 condiciones
TierLimitsChecker (domain)       ← verificación de límites de tier
```

## Consideraciones de Seguridad

- La clave AES nunca se loggea ni se incluye en backups sin cifrar.
- Los backups de PostgreSQL (R2) contienen el campo ya encriptado → doble protección.
- La clave AES se rota semestralmente (re-encriptar todos los registros en job nocturno).
- El campo `alergias` (JSONB) no se encripta — no es dato médico sensible.
