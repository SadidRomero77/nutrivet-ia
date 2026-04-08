"""
CorrelationMiddleware — Inyecta un trace_id único por request HTTP.

Extrae el header X-Trace-ID si lo envía el cliente (útil para rastrear
requests desde mobile). Si no existe, genera un UUID v4 nuevo.

El trace_id queda disponible para todos los logs del request via
set_correlation_id() del módulo logging_config.

Responde con el header X-Trace-ID para que el cliente pueda reportar
el ID al support cuando hay errores.
"""
from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.infrastructure.logging_config import set_correlation_id

_TRACE_HEADER = "X-Trace-ID"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware que asigna un trace_id único a cada request y lo propaga
    a los logs via contextvars.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(_TRACE_HEADER) or str(uuid.uuid4())
        set_correlation_id(trace_id)

        response = await call_next(request)
        response.headers[_TRACE_HEADER] = trace_id
        return response
