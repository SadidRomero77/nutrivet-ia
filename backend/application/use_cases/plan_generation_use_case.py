"""
PlanGenerationUseCase — Encola jobs de generación y expone polling de estado.

No ejecuta la generación directamente — delega al ARQ worker.
El worker corre de forma asíncrona y actualiza el job QUEUED → READY/FAILED.
"""
from __future__ import annotations

import uuid
from typing import Any

from backend.application.interfaces.agent_trace_repository import IAgentTraceRepository
from backend.application.interfaces.pet_repository import IPetRepository
from backend.application.interfaces.plan_job_repository import IPlanJobRepository
from backend.application.interfaces.plan_repository import IPlanRepository
from backend.domain.aggregates.user_account import TIER_PLAN_LIMITS, UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.domain.value_objects.plan_job import PlanJob, PlanJobStatus
from backend.infrastructure.config.feature_flags import MVP_FREEMIUM_DISABLED


class PlanGenerationUseCase:
    """
    Casos de uso de generación de planes nutricionales.

    Implementa:
    - enqueue: Valida prerrequisitos y crea el PlanJob. La generación real
      ocurre en PlanGenerationWorker (ARQ).
    - get_job: Polling de estado del job (QUEUED → PROCESSING → READY/FAILED).
    """

    def __init__(
        self,
        plan_repo: IPlanRepository,
        job_repo: IPlanJobRepository,
        pet_repo: IPetRepository,
        trace_repo: IAgentTraceRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._job_repo = job_repo
        self._pet_repo = pet_repo
        self._trace_repo = trace_repo

    async def enqueue(
        self,
        pet_id: uuid.UUID,
        owner_id: uuid.UUID | None,
        user_tier: UserTier,
        modality: str,
        requester_vet_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        """
        Valida prerrequisitos y encola un job de generación de plan.

        Args:
            pet_id: ID de la mascota para la que se genera el plan.
            owner_id: ID del owner que solicita el plan (None si es vet).
            user_tier: Tier del solicitante (para validar límite de planes).
            modality: Modalidad del plan ('concentrado' o 'natural').
            requester_vet_id: ID del vet solicitante (None si es owner).
                Si se provee, se omite el chequeo de propiedad y se verifica
                que el vet está asignado a la mascota.

        Returns:
            job_id: UUID del PlanJob creado para polling.

        Raises:
            DomainError: Si la mascota no existe, el solicitante no tiene acceso,
                         o se supera el límite de planes del tier.
        """
        # Verificar que la mascota existe
        pet = await self._pet_repo.find_by_id(pet_id)
        if pet is None:
            raise DomainError(f"Mascota con ID '{pet_id}' no encontrada.")

        if requester_vet_id is not None:
            # Acceso como veterinario: verificar que está asignado a la mascota
            if pet.vet_id != requester_vet_id:
                raise DomainError("Acceso denegado: no eres el veterinario asignado a esta mascota.")
            # Usar owner_id real del pet; si el paciente no está vinculado, usar el vet como propietario del job
            effective_owner_id: uuid.UUID = pet.owner_id if pet.owner_id is not None else requester_vet_id
        else:
            # Acceso como owner: verificar propiedad
            if pet.owner_id != owner_id:
                raise DomainError("Acceso denegado: no eres el dueño de esta mascota.")
            effective_owner_id = owner_id  # type: ignore[assignment]

        # Verificar límite de planes por tier (desactivado en MVP — piloto sin restricciones)
        if not MVP_FREEMIUM_DISABLED:
            plan_limit = TIER_PLAN_LIMITS[user_tier]
            if plan_limit is not None:
                current_count = await self._plan_repo.count_active_by_owner(effective_owner_id)
                if current_count >= plan_limit:
                    raise DomainError(
                        f"Has alcanzado el límite de planes para tu plan "
                        f"({plan_limit} plan{'es' if plan_limit > 1 else ''}). "
                        "Actualiza tu suscripción para generar más planes."
                    )

        # Crear job y persistir
        job = PlanJob(
            job_id=uuid.uuid4(),
            pet_id=pet_id,
            owner_id=effective_owner_id,
            modality=modality,
            status=PlanJobStatus.QUEUED,
        )
        await self._job_repo.save(job)

        # En producción aquí se encolaría en ARQ:
        # await arq_pool.enqueue_job("generate_plan", job_id=str(job.job_id))
        # Por ahora el worker se invoca externamente.

        return job.job_id

    async def get_job(
        self,
        job_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Retorna el estado actual del job de generación.

        Args:
            job_id: ID del job a consultar.
            requester_id: ID del usuario que consulta (puede ser el owner).

        Returns:
            Dict con status, plan_id (si READY) y error_message (si FAILED).

        Raises:
            DomainError: Si el job no existe.
        """
        job = await self._job_repo.find_by_id(job_id)
        if job is None:
            raise DomainError(f"Job con ID '{job_id}' no encontrado.")

        result: dict[str, Any] = {
            "job_id": job.job_id,
            "status": job.status.value if isinstance(job.status, PlanJobStatus) else job.status,
            "plan_id": job.plan_id,
            "error_message": job.error_message,
            "progress_step": job.progress_step,
            "progress_message": job.progress_message,
        }
        return result
