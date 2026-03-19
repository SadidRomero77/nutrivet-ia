"""
WeightTrackingUseCase — Casos de uso de seguimiento de peso.
Append-only: solo se puede agregar, nunca modificar registros existentes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from backend.application.interfaces.pet_repository import IPetRepository
from backend.application.interfaces.weight_repository import IWeightRepository
from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.value_objects.bcs import BCS


class WeightTrackingUseCase:
    """
    Seguimiento de peso de mascotas.

    Los registros son inmutables (append-only). No existe update ni delete.
    """

    def __init__(
        self,
        weight_repo: IWeightRepository,
        pet_repo: IPetRepository,
    ) -> None:
        self._weight_repo = weight_repo
        self._pet_repo = pet_repo

    async def add_weight_record(
        self,
        pet_id: uuid.UUID,
        requester_id: uuid.UUID,
        weight_kg: float,
        bcs: Optional[BCS],
    ) -> uuid.UUID:
        """
        Agrega un nuevo registro de peso para una mascota.

        Args:
            pet_id: ID de la mascota.
            requester_id: ID del usuario que registra (owner o vet).
            weight_kg: Peso en kilogramos (debe ser positivo).
            bcs: BCS opcional al momento del registro.

        Returns:
            UUID del registro creado.

        Raises:
            DomainError: Si el peso es inválido o el acceso está denegado.
        """
        if weight_kg <= 0:
            raise DomainError(
                f"El peso debe ser mayor a 0 kg. Valor recibido: {weight_kg}."
            )

        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is not None and pet.owner_id != requester_id:
            raise DomainError("Acceso denegado: no puedes registrar peso de esta mascota.")

        record_id = await self._weight_repo.append(
            pet_id=pet_id,
            weight_kg=weight_kg,
            bcs=bcs,
            recorded_by=requester_id,
            recorded_at=datetime.now(timezone.utc),
        )
        return record_id

    async def get_weight_history(
        self,
        pet_id: uuid.UUID,
        requester_id: uuid.UUID,
        limit: int = 30,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Retorna el historial de peso de una mascota.

        Args:
            pet_id: ID de la mascota.
            requester_id: ID del usuario solicitante.
            limit: Máximo de registros (default 30).
            offset: Desplazamiento para paginación.

        Returns:
            Lista de registros ordenados por fecha descendente.

        Raises:
            DomainError: Si el acceso está denegado.
        """
        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is not None and pet.owner_id != requester_id:
            raise DomainError(
                "Acceso denegado: no puedes ver el historial de peso de esta mascota."
            )

        return await self._weight_repo.list_by_pet(
            pet_id=pet_id, limit=limit, offset=offset
        )
