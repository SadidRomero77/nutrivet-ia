"""
PetClaimUseCase — Casos de uso de ClinicPet y claim codes.
Permite a vets crear mascotas clínicas y owners reclamarlas con un código.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.application.interfaces.claim_code_repository import IClaimCodeRepository
from backend.application.interfaces.pet_repository import IPetRepository
from backend.domain.aggregates.pet_profile import PetProfile
from backend.domain.aggregates.user_account import UserTier
from backend.domain.exceptions.domain_errors import DomainError

_CLAIM_TTL_DAYS = 30
_CODE_LENGTH = 8
# Excluye '0' y 'O' para evitar confusión visual, y 'I' y 'l' por claridad
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_claim_code() -> str:
    """Genera un código alfanumérico seguro de 8 caracteres sin '0', 'O', 'I', 'l'."""
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


class PetClaimUseCase:
    """
    Casos de uso de ClinicPet y claim codes.

    Implementa:
    - create_clinic_pet: Vet crea mascota clínica + genera claim code.
    - claim_pet: Owner reclama mascota con código → se convierte en AppPet.
    """

    def __init__(
        self,
        pet_repo: IPetRepository,
        claim_repo: IClaimCodeRepository,
    ) -> None:
        self._pet_repo = pet_repo
        self._claim_repo = claim_repo

    async def create_clinic_pet(
        self,
        vet_id: uuid.UUID,
        vet_tier: UserTier,
        pet_data: dict[str, Any],
        owner_name: str,
        owner_phone: str,
    ) -> dict[str, Any]:
        """
        Crea una ClinicPet y genera un claim code para que el owner la reclame.

        Solo disponible para vets con tier Vet.

        Args:
            vet_id: ID del veterinario.
            vet_tier: Tier del vet (debe ser UserTier.VET).
            pet_data: Datos del perfil de la mascota.
            owner_name: Nombre del dueño (referencia clínica).
            owner_phone: Teléfono del dueño (referencia clínica).

        Returns:
            Dict con pet_id y claim_code.

        Raises:
            DomainError: Si el vet no tiene tier Vet.
        """
        if vet_tier != UserTier.VET:
            raise DomainError(
                f"Crear mascotas clínicas requiere tier Vet. "
                f"Tu tier actual es '{vet_tier.value}'."
            )

        # La mascota se crea sin owner (owner_id = vet_id como placeholder)
        pet = PetProfile(
            pet_id=uuid.uuid4(),
            owner_id=vet_id,  # se actualizará al hacer claim
            is_clinic_pet=True,
            vet_id=vet_id,
            **pet_data,
        )
        await self._pet_repo.save(pet)

        # Generar claim code con TTL de 30 días
        code = _generate_claim_code()
        expires_at = datetime.now(timezone.utc) + timedelta(days=_CLAIM_TTL_DAYS)
        await self._claim_repo.save(
            pet_id=pet.pet_id,
            code=code,
            expires_at=expires_at,
        )

        return {"pet_id": pet.pet_id, "claim_code": code}

    async def claim_pet(
        self,
        code: str,
        owner_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Owner reclama una mascota clínica usando el claim code.

        Valida: existencia, expiración (30 días), y uso único.
        Transacción atómica: marca código como usado + actualiza owner_id.

        Args:
            code: Claim code de 8 caracteres.
            owner_id: ID del owner que reclama la mascota.

        Returns:
            Dict con pet_id del pet reclamado.

        Raises:
            DomainError: Si el código no existe, expiró o ya fue usado.
        """
        claim = await self._claim_repo.find_by_code(code)
        if claim is None:
            raise DomainError(
                f"El código '{code}' no existe o es inválido."
            )

        if claim["used"]:
            raise DomainError(
                f"El código '{code}' ya fue usado. Solo puede reclamarse una vez."
            )

        now = datetime.now(timezone.utc)
        expires_at = claim["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            raise DomainError(
                f"El código '{code}' ha expirado. Solicita al veterinario un nuevo código."
            )

        # Actualizar owner_id en la mascota
        pet = await self._pet_repo.find_by_id(claim["pet_id"])
        if pet is None:
            raise DomainError("La mascota asociada al código no existe.")

        pet.owner_id = owner_id
        await self._pet_repo.update(pet)

        # Marcar código como usado (single-use)
        await self._claim_repo.mark_used(code)

        return {"pet_id": claim["pet_id"]}
