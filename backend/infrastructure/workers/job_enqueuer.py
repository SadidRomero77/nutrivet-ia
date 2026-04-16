"""
JobEnqueuer — Encola jobs en ARQ (Redis) con fallback a BackgroundTasks.

En producción (REDIS_URL configurada): encola en ARQ → procesado por worker dedicado.
En desarrollo (sin Redis): ejecuta inline via BackgroundTasks de FastAPI.

Este módulo abstrae la decisión para que plan_router.py no necesite saber
qué backend de jobs está activo.
"""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_redis_url = os.environ.get("REDIS_URL", "")
_arq_pool: Any = None


async def _get_arq_pool() -> Any:
    """Obtiene o crea el pool de conexiones ARQ (lazy singleton)."""
    global _arq_pool
    if _arq_pool is not None:
        return _arq_pool

    if not _redis_url:
        return None

    try:
        from arq import create_pool
        from backend.infrastructure.workers.arq_app import _parse_redis_settings
        _arq_pool = await create_pool(_parse_redis_settings())
        logger.info("ARQ pool inicializado — jobs se encolarán en Redis")
        return _arq_pool
    except Exception as exc:
        logger.warning(
            "No se pudo conectar a Redis para ARQ: %s — usando BackgroundTasks",
            type(exc).__name__,
        )
        return None


async def enqueue_plan_generation(
    job_id: uuid.UUID,
    user_tier: str,
) -> bool:
    """
    Intenta encolar el job en ARQ (Redis).

    Returns:
        True si se encoló exitosamente en ARQ.
        False si debe usarse BackgroundTasks como fallback.
    """
    pool = await _get_arq_pool()
    if pool is None:
        return False

    try:
        await pool.enqueue_job(
            "generate_plan",
            str(job_id),
            user_tier,
        )
        logger.info("Job %s encolado en ARQ", job_id)
        return True
    except Exception as exc:
        logger.warning(
            "Error encolando en ARQ job=%s: %s — fallback a BackgroundTasks",
            job_id, type(exc).__name__,
        )
        return False
