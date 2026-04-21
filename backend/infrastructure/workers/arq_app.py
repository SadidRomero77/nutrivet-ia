"""
ARQ Worker — Entrypoint del worker de jobs asíncronos NutriVet.IA.

Ejecutar con:
    python -m backend.infrastructure.workers.arq_app

O via Docker:
    docker compose -f docker-compose.prod.yml up worker

Jobs registrados:
    - generate_plan: Genera un plan nutricional completo (11 pasos).

Configuración:
    - Redis: REDIS_URL (default redis://localhost:6379/0)
    - Max jobs concurrentes: 5 (ajustar según CPU del VPS)
    - Health check interval: 60s

Constitution REGLAs activas: todas (el worker ejecuta el pipeline completo).
"""
from __future__ import annotations

import logging
import os
import uuid

from dotenv import load_dotenv

# Cargar variables de entorno antes de importar módulos que las usen
load_dotenv(override=False) or load_dotenv(".env.dev", override=False)

from arq import cron, run_worker
from arq.connections import RedisSettings

from backend.domain.aggregates.user_account import UserTier

logger = logging.getLogger(__name__)


def _parse_redis_settings() -> RedisSettings:
    """Parsea REDIS_URL a RedisSettings de arq."""
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Parsear redis://host:port/db
    url = redis_url.replace("redis://", "")
    # Separar host:port/db
    if "/" in url:
        host_port, db_str = url.rsplit("/", 1)
        database = int(db_str) if db_str else 0
    else:
        host_port = url
        database = 0

    if ":" in host_port:
        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)
    else:
        host = host_port
        port = 6379

    # Password: redis://:password@host:port/db
    password = None
    if "@" in host:
        creds, host = host.rsplit("@", 1)
        if creds.startswith(":"):
            password = creds[1:]

    return RedisSettings(host=host, port=port, database=database, password=password)


async def _send_post_generation_notifications(job_uuid: uuid.UUID) -> None:
    """
    Envía push notifications tras la generación de un plan.

    - Owner: notifica que su plan está listo (READY) o falló (FAILED).
    - Vet: si el plan quedó PENDING_VET, notifica al vet vinculado.

    Fire-and-forget: errores se loguean pero nunca bloquean el job.
    """
    from backend.infrastructure.db.session import AsyncSessionLocal
    from backend.infrastructure.db.models import PlanJobModel, NutritionPlanModel, PetModel
    from backend.infrastructure.db.device_token_repository import PostgreSQLDeviceTokenRepository
    from backend.infrastructure.push.fcm_client import PushNotification, send_push_to_tokens
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as session:
            # Cargar el job
            job_q = await session.execute(
                select(PlanJobModel).where(PlanJobModel.id == job_uuid)
            )
            job = job_q.scalar_one_or_none()
            if job is None:
                return

            token_repo = PostgreSQLDeviceTokenRepository(session)

            # Notificar al owner del resultado
            if job.status == "READY" and job.plan_id is not None:
                owner_tokens = await token_repo.get_tokens_for_user(job.owner_id)
                if owner_tokens:
                    await send_push_to_tokens(
                        tokens=owner_tokens,
                        notification=PushNotification(
                            title="¡Tu plan nutricional está listo!",
                            body="Ya puedes ver el plan personalizado de tu mascota.",
                            data={"event": "plan_ready", "plan_id": str(job.plan_id)},
                        ),
                    )

                # Si el plan es PENDING_VET, notificar al vet vinculado
                plan_q = await session.execute(
                    select(NutritionPlanModel.status, NutritionPlanModel.pet_id)
                    .where(NutritionPlanModel.id == job.plan_id)
                )
                plan_row = plan_q.one_or_none()
                if plan_row is not None and plan_row.status == "PENDING_VET":
                    pet_q = await session.execute(
                        select(PetModel.vet_id).where(PetModel.id == plan_row.pet_id)
                    )
                    vet_id = pet_q.scalar_one_or_none()
                    if vet_id is not None:
                        vet_tokens = await token_repo.get_tokens_for_user(vet_id)
                        if vet_tokens:
                            await send_push_to_tokens(
                                tokens=vet_tokens,
                                notification=PushNotification(
                                    title="Nuevo plan para revisar",
                                    body="Un propietario generó un plan con condición médica. Requiere tu aprobación.",
                                    data={"event": "plan_pending_vet", "plan_id": str(job.plan_id)},
                                ),
                            )

            elif job.status == "FAILED":
                owner_tokens = await token_repo.get_tokens_for_user(job.owner_id)
                if owner_tokens:
                    await send_push_to_tokens(
                        tokens=owner_tokens,
                        notification=PushNotification(
                            title="Error al generar tu plan",
                            body="Hubo un problema generando el plan. Por favor intenta de nuevo.",
                            data={"event": "plan_failed", "job_id": str(job_uuid)},
                        ),
                    )
    except Exception:
        logger.exception("Error enviando push notifications post-generación job=%s", job_uuid)


async def generate_plan(ctx: dict, job_id: str, user_tier: str) -> str:
    """
    ARQ task: genera un plan nutricional completo.

    Args:
        ctx: Contexto ARQ (contiene redis pool).
        job_id: UUID del PlanJob en formato string.
        user_tier: Tier del usuario en formato string (free/basico/premium/vet).

    Returns:
        String con resultado ("ok" o "error: ...").
    """
    from backend.infrastructure.db.session import AsyncSessionLocal
    from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
    from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
    from backend.infrastructure.db.plan_job_repository import PostgreSQLPlanJobRepository
    from backend.infrastructure.db.agent_trace_repository import PostgreSQLAgentTraceRepository
    from backend.infrastructure.workers.plan_generation_worker import PlanGenerationWorker

    job_uuid = uuid.UUID(job_id)
    tier = UserTier(user_tier.lower())

    logger.info("arq_generate_plan iniciando job=%s tier=%s", job_id, user_tier)

    async with AsyncSessionLocal() as session:
        try:
            worker = PlanGenerationWorker(
                pet_repo=PostgreSQLPetRepository(session),
                plan_repo=PostgreSQLPlanRepository(session),
                job_repo=PostgreSQLPlanJobRepository(session),
                trace_repo=PostgreSQLAgentTraceRepository(session),
            )
            await worker.execute(job_id=job_uuid, user_tier=tier)
            await session.commit()
            logger.info("arq_generate_plan completado job=%s", job_id)

            # Push notifications post-generación (fire-and-forget)
            await _send_post_generation_notifications(job_uuid)

            return "ok"
        except Exception as exc:
            await session.rollback()
            logger.exception("arq_generate_plan falló job=%s", job_id)

            # Marcar FAILED en sesión limpia
            async with AsyncSessionLocal() as err_session:
                try:
                    err_repo = PostgreSQLPlanJobRepository(err_session)
                    err_job = await err_repo.find_by_id(job_uuid)
                    if err_job is not None and err_job.status.value not in ("READY", "FAILED"):
                        err_job.mark_failed(error_message=str(exc))
                        await err_repo.update(err_job)
                        await err_session.commit()
                except Exception:
                    logger.exception("No se pudo marcar FAILED job=%s en fallback", job_id)

            # Notificar al owner del fallo
            await _send_post_generation_notifications(job_uuid)

            return f"error: {exc}"


async def startup(ctx: dict) -> None:
    """Inicialización del worker — configurar logging."""
    from backend.infrastructure.logging_config import configure_logging
    configure_logging()
    logger.info("ARQ worker iniciado — listo para procesar jobs")


async def shutdown(ctx: dict) -> None:
    """Limpieza del worker al apagarse."""
    logger.info("ARQ worker apagándose — limpieza completada")


class WorkerSettings:
    """
    Configuración del ARQ worker.

    max_jobs=5: límite de jobs concurrentes por worker.
    Incrementar si el VPS tiene más CPU, o agregar réplicas del contenedor worker.
    """
    redis_settings = _parse_redis_settings()
    functions = [generate_plan]
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 5
    job_timeout = 300  # 5 min max por plan — previene jobs colgados
    health_check_interval = 60  # segundos


if __name__ == "__main__":
    run_worker(WorkerSettings)  # type: ignore[arg-type]
