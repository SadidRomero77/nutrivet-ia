# Plan: NFR Design — Unit 03: pet-service

**Unidad**: unit-03-pet-service
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a pet-service

### Patrón: AES-256 para Campos Sensibles (Fernet)

**Contexto**: `medical_conditions` y `allergies` son datos médicos sensibles que deben
estar encriptados en reposo en PostgreSQL (Constitution REGLA 6).

**Diseño**:
```python
# infrastructure/encryption/fernet_encryptor.py
from cryptography.fernet import Fernet
import os

class FernetEncryptor:
    """Encriptación AES-256 via Fernet para campos sensibles en DB."""

    def __init__(self):
        key = os.environ["FERNET_KEY"]
        self._fernet = Fernet(key.encode())

    def encrypt(self, data: dict) -> bytes:
        """Serializa a JSON y encripta. Retorna bytes para almacenar en BYTEA."""
        import json
        return self._fernet.encrypt(json.dumps(data).encode())

    def decrypt(self, data: bytes) -> dict:
        """Desencripta y deserializa de JSON. Retorna dict."""
        import json
        return json.loads(self._fernet.decrypt(data))
```

**Integración en repository**:
```python
# En PostgreSQLPetRepository.save():
pet_row["medical_conditions"] = encryptor.encrypt(pet.medical_conditions)
pet_row["allergies"] = encryptor.encrypt(pet.allergies)

# En PostgreSQLPetRepository.find_by_id():
medical_conditions = encryptor.decrypt(row["medical_conditions"])
allergies = encryptor.decrypt(row["allergies"])
```

### Patrón: Append-Only Weight Records

**Contexto**: El historial de peso debe ser inmutable para trazabilidad clínica.

**Diseño**:
- `IWeightRepository` solo expone `add(record)` y `list_by_pet(pet_id, limit, offset)`.
- No existe método `update()` ni `delete()` en la interfaz.
- La tabla `weight_records` no tiene columna `updated_at`.
- El router nunca expone `PATCH /pets/{id}/weight/{record_id}`.

```python
# application/interfaces/weight_repository.py
from abc import ABC, abstractmethod

class IWeightRepository(ABC):
    """Repositorio de registros de peso — append-only por diseño."""

    @abstractmethod
    async def add(self, record: WeightRecord) -> WeightRecord:
        """Agrega registro de peso. Nunca modifica registros existentes."""
        ...

    @abstractmethod
    async def list_by_pet(
        self, pet_id: UUID, limit: int = 30, offset: int = 0
    ) -> list[WeightRecord]:
        """Lista historial de peso paginado, ordenado por fecha DESC."""
        ...
    # No hay update() ni delete() — por diseño
```

### Patrón: Claim Code Criptográficamente Seguro

**Contexto**: Los claim codes se comparten por canales informales (WhatsApp, papel).
Deben ser difíciles de adivinar pero cortos y legibles.

**Diseño**:
```python
# application/use_cases/pet_claim_use_case.py
import secrets
import string

def generate_claim_code() -> str:
    """Genera código de 8 caracteres alfanumérico seguro (excluye O, 0, I, l)."""
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + \
               string.digits.replace("0", "")
    return "".join(secrets.choice(alphabet) for _ in range(8))
    # Entropía: ~40 bits — adecuado para TTL 30 días
```

**Garantía de single-use via transacción atómica**:
```sql
-- En claim_code_repository.claim():
BEGIN;
SELECT * FROM claim_codes WHERE code = $1 FOR UPDATE;  -- lock row
-- verificar TTL y used_at IS NULL
UPDATE claim_codes SET used_at = NOW(), used_by = $2 WHERE code = $1;
UPDATE pets SET owner_id = $2, claimed_at = NOW() WHERE pet_id = $3;
COMMIT;
```

### Patrón: Paginación para Weight History

**Contexto**: El historial de peso puede crecer significativamente en mascotas mayores.

**Diseño**:
- Default: últimos 30 registros.
- Max por request: 90 registros (3 meses de registros diarios).
- Cursor-based en el futuro si necesario — keyset pagination por `recorded_at`.

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `use_cases/pet_profile_use_case.py` | 90% | Unit tests — 13 invariantes |
| `use_cases/pet_claim_use_case.py` | 90% | Unit tests — TTL + single-use |
| `use_cases/weight_tracking_use_case.py` | 80% | Unit tests — append-only |
| `infrastructure/db/pet_repository.py` | 80% | Integration tests (testcontainers) |
| `infrastructure/encryption/fernet_encryptor.py` | 100% | Unit tests |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- Constitution: REGLA 6 (AES-256 en reposo)
- Unit spec: `inception/units/unit-03-pet-service.md`
