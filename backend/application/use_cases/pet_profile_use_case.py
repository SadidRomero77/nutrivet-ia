"""
PetProfileUseCase — Casos de uso de gestión de perfiles de mascotas.
Valida límites de tier, invariantes de dominio, y RBAC de acceso.
"""
from __future__ import annotations

import uuid
from typing import Any

from backend.application.interfaces.pet_repository import IPetRepository
from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.aggregates.pet_profile import MedicalCondition, PetProfile
from backend.domain.aggregates.user_account import UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.config.feature_flags import MVP_FREEMIUM_DISABLED

# Límites de mascotas por tier (None = ilimitado)
_TIER_PET_LIMITS: dict[UserTier, int | None] = {
    UserTier.FREE: 1,
    UserTier.BASICO: 1,
    UserTier.PREMIUM: 3,
    UserTier.VET: None,
}


class PetProfileUseCase:
    """
    Casos de uso de gestión de perfiles de mascotas.

    Implementa:
    - create_pet: Crear mascota validando límite de tier.
    - get_pet: Obtener mascota con validación de acceso.
    - update_pet: Actualizar mascota.
    - list_pets: Listar mascotas del owner.
    - add_medical_condition: Agrega condición médica y señala si requiere revisión vet.
    """

    def __init__(
        self,
        pet_repo: IPetRepository,
        plan_repo: IPlanRepository | None = None,
    ) -> None:
        self._pet_repo = pet_repo
        self._plan_repo = plan_repo

    async def create_pet(
        self,
        owner_id: uuid.UUID,
        pet_data: dict[str, Any],
        user_tier: UserTier,
    ) -> PetProfile:
        """
        Crea un nuevo perfil de mascota para el owner.

        Valida el límite de mascotas por tier antes de crear.

        Args:
            owner_id: ID del usuario dueño.
            pet_data: Diccionario con los 13 campos del perfil.
            user_tier: Tier de suscripción del owner.

        Returns:
            PetProfile creado.

        Raises:
            DomainError: Si se supera el límite del tier o los datos son inválidos.
        """
        # Verificar límite de tier (desactivado en MVP — piloto sin restricciones)
        if not MVP_FREEMIUM_DISABLED:
            current_count = await self._pet_repo.count_by_owner(owner_id)
            limit = _TIER_PET_LIMITS[user_tier]
            if limit is not None and current_count >= limit:
                raise DomainError(
                    f"Has alcanzado el límite de mascotas para tu plan "
                    f"({limit} mascota{'s' if limit > 1 else ''}). "
                    "Actualiza tu suscripción para agregar más."
                )

        # Construir aggregate — las invariantes se validan en __post_init__
        pet = PetProfile(
            pet_id=uuid.uuid4(),
            owner_id=owner_id,
            **pet_data,
        )

        await self._pet_repo.save(pet)
        return pet

    async def get_pet(
        self,
        pet_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
    ) -> PetProfile:
        """
        Obtiene un perfil de mascota validando que el solicitante tiene acceso.

        Args:
            pet_id: ID de la mascota.
            requester_id: ID del usuario que solicita.
            requester_role: Rol del solicitante ('owner' o 'vet').

        Returns:
            PetProfile si el acceso es válido.

        Raises:
            DomainError: Si la mascota no existe o el acceso está denegado.
        """
        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is None:
            raise DomainError(f"Mascota con ID '{pet_id}' no encontrada.")

        # Los vets pueden ver cualquier mascota; owners solo las suyas
        if requester_role != "vet" and pet.owner_id != requester_id:
            raise DomainError("Acceso denegado: no eres el dueño de esta mascota.")

        return pet

    async def update_pet(
        self,
        pet_id: uuid.UUID,
        update_data: dict[str, Any],
        requester_id: uuid.UUID,
    ) -> PetProfile:
        """
        Actualiza los datos de una mascota.

        Args:
            pet_id: ID de la mascota a actualizar.
            update_data: Campos a modificar.
            requester_id: ID del owner (solo el owner puede actualizar).

        Returns:
            PetProfile actualizado.

        Raises:
            DomainError: Si la mascota no existe o el acceso está denegado.
        """
        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is None:
            raise DomainError(f"Mascota con ID '{pet_id}' no encontrada.")
        if pet.owner_id != requester_id:
            raise DomainError("Acceso denegado: no eres el dueño de esta mascota.")

        from backend.domain.aggregates.pet_profile import (
            CatActivityLevel,
            CurrentDiet as CurrentDietEnum,
            DogActivityLevel,
            Species,
        )
        if 'activity_level' in update_data and isinstance(update_data['activity_level'], str):
            al_str = update_data['activity_level']
            species_val = pet.species.value if hasattr(pet.species, 'value') else str(pet.species)
            if species_val == 'perro':
                update_data['activity_level'] = DogActivityLevel(al_str)
            else:
                update_data['activity_level'] = CatActivityLevel(al_str)
        if 'current_diet' in update_data and isinstance(update_data['current_diet'], str):
            update_data['current_diet'] = CurrentDietEnum(update_data['current_diet'])

        for field_name, value in update_data.items():
            if hasattr(pet, field_name):
                object.__setattr__(pet, field_name, value)

        await self._pet_repo.update(pet)
        return pet

    async def delete_pet(
        self,
        pet_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> None:
        """
        Elimina (soft-delete) una mascota. Solo el owner puede eliminarla.
        Bloqueado si la mascota tiene algún plan ACTIVE o PENDING_VET asignado.

        Raises:
            DomainError: Si la mascota no existe, acceso denegado, o tiene planes activos.
        """
        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is None:
            raise DomainError(f"Mascota con ID '{pet_id}' no encontrada.")
        if pet.owner_id != requester_id:
            raise DomainError("Acceso denegado: no eres el dueño de esta mascota.")

        # No se puede eliminar si tiene planes activos o pendientes
        if self._plan_repo is not None:
            plan_activo = await self._plan_repo.find_active_by_pet(pet_id)
            if plan_activo is not None:
                raise DomainError(
                    "No se puede eliminar la mascota porque tiene un plan nutricional "
                    f"en estado '{plan_activo.status.value}'. "
                    "Archiva o elimina el plan antes de continuar."
                )

        await self._pet_repo.deactivate(pet_id)

    async def list_pets(self, owner_id: uuid.UUID) -> list[PetProfile]:
        """Lista todas las mascotas activas del owner."""
        return await self._pet_repo.list_by_owner(owner_id)

    async def add_medical_condition(
        self,
        pet_id: uuid.UUID,
        requester_id: uuid.UUID,
        condition: MedicalCondition,
    ) -> dict[str, Any]:
        """
        Agrega una condición médica a la mascota.

        Si la mascota ya tenía un plan ACTIVE, el caller debe transicionarlo
        a PENDING_VET (ese trigger es responsabilidad del plan-service).

        Args:
            pet_id: ID de la mascota.
            requester_id: ID del owner.
            condition: Condición médica a agregar.

        Returns:
            Dict con pet_id y requires_vet_review.

        Raises:
            DomainError: Si la mascota no existe o el acceso está denegado.
        """
        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is None:
            raise DomainError(f"Mascota con ID '{pet_id}' no encontrada.")
        if pet.owner_id != requester_id:
            raise DomainError("Acceso denegado: no eres el dueño de esta mascota.")

        pet.add_medical_condition(condition)
        await self._pet_repo.update(pet)

        return {
            "pet_id": pet_id,
            "requires_vet_review": pet.requires_vet_review(),
        }
