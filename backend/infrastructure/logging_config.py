"""
logging_config — Configuración de structured logging para NutriVet.IA.

Usa structlog con JSON output en producción y consola colorizada en desarrollo.
Inyecta correlation_id por request via contextvars (asyncio-safe).

Constitution REGLA 6: NUNCA incluir PII en logs.
  Campos prohibidos en logs: nombres de mascotas, nombres de owners,
  condiciones médicas en texto plano, especies, pesos. Solo UUIDs anónimos.

Uso:
    from backend.infrastructure.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("plan_generated", pet_id=str(pet_id), model=model, latency_ms=120)

Correlation ID:
    El middleware HTTP inyecta un trace_id único por request.
    Todos los logs del mismo request comparten ese trace_id.
"""
from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar

import structlog

# ─── ContextVar para correlation_id por request ───────────────────────────────
# Thread-safe y asyncio-safe: cada request tiene su propio contexto.
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="-")


def set_correlation_id(value: str) -> None:
    """Establece el correlation_id para el request actual (llamado desde middleware)."""
    _correlation_id.set(value)


def get_correlation_id() -> str:
    """Retorna el correlation_id del request actual."""
    return _correlation_id.get()


# ─── Processor que inyecta correlation_id en cada evento ─────────────────────

def _inject_correlation_id(logger, method_name, event_dict):  # noqa: ARG001
    """Inyecta el correlation_id del request actual en cada log event."""
    event_dict["trace_id"] = _correlation_id.get()
    return event_dict


# ─── Setup principal ──────────────────────────────────────────────────────────

def configure_logging() -> None:
    """
    Configura structlog para toda la aplicación.

    En producción (LOG_FORMAT=json o NODE_ENV=production): JSON output.
    En desarrollo: consola colorizada con formato legible.

    Llamar UNA sola vez al inicio de la aplicación (en main.py).
    """
    is_production = os.environ.get("LOG_FORMAT", "").lower() == "json" or \
                    os.environ.get("NODE_ENV", "").lower() == "production"

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        _inject_correlation_id,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_production:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
        renderer = structlog.processors.JSONRenderer()
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Silenciar loggers ruidosos de librerías externas
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Retorna un logger structlog configurado para el módulo dado.

    Uso:
        logger = get_logger(__name__)
        logger.info("evento", campo="valor")

    Constitution REGLA 6: no incluir PII — usar solo UUIDs anónimos.
    """
    return structlog.get_logger(name)
