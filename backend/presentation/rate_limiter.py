"""
Rate Limiter compartido — instancia única para toda la app.

Todos los routers deben importar `limiter` desde este módulo
en vez de crear su propia instancia.

slowapi requiere que el decorador @limiter.limit() use la MISMA
instancia registrada en app.state.limiter.

Almacenamiento:
  - Producción (REDIS_URL definida): Redis — counters compartidos entre todos
    los workers de Uvicorn. Sin Redis, el rate limiting es por-worker y pierde
    efectividad con múltiples réplicas (ver RUNBOOK.md § Rate Limiting).
  - Desarrollo (sin REDIS_URL): in-memory — suficiente para un solo worker local.

NOTA: la conexión a Redis es lazy — los errores de conectividad se manifiestan
en el primer request rate-limitado, no en el arranque. Monitorear en Sentry.
"""
from __future__ import annotations

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_redis_url = os.environ.get("REDIS_URL", "")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    **({"storage_uri": _redis_url} if _redis_url else {}),
)
