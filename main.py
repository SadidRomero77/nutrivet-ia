"""
NutriVet.IA — FastAPI application entrypoint.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Carga vars de entorno:
# - Producción/staging: vars vienen del contenedor (Docker/Coolify) — load_dotenv() es no-op.
# - Dev local: carga .env si existe, luego .env.dev como fallback.
# override=False: las vars del entorno del sistema tienen prioridad sobre el archivo.
load_dotenv(override=False) or load_dotenv(".env.dev", override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.infrastructure.logging_config import configure_logging

configure_logging()

from backend.presentation.middleware.correlation_middleware import CorrelationMiddleware
from backend.presentation.routers.auth_router import router as auth_router
from backend.presentation.routers.pet_router import router as pet_router
from backend.presentation.routers.plan_router import router as plan_router
from backend.presentation.routers.plan_router import vet_router
from backend.presentation.routers.agent_router import router as agent_router
from backend.presentation.routers.export_router import router as export_router
from backend.presentation.routers.device_router import router as device_router
from backend.presentation.routers.subscription_router import router as subscription_router
from backend.presentation.routers.admin_router import router as admin_router

# ── CORS ──────────────────────────────────────────────────────────────────────
# CORS_ORIGINS debe ser una lista separada por comas en producción.
# Ejemplo: "https://app.nutrivet.ia,https://vet.nutrivet.ia"
# Constitution REGLA 6: NUNCA wildcard en producción.
_cors_origins_raw = os.environ.get("CORS_ORIGINS", "")
if _cors_origins_raw.strip() == "*":
    raise RuntimeError(
        "CORS_ORIGINS='*' no está permitido. "
        "Define los orígenes explícitos separados por coma. "
        "En desarrollo usa CORS_ORIGINS='http://localhost:3000,http://localhost:8080'"
    )
_allowed_origins: list[str] = (
    [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]
    if _cors_origins_raw.strip()
    else ["http://localhost:3000", "http://localhost:8080", "http://localhost:8081"]
)

# ── Rate Limiter ───────────────────────────────────────────────────────────────
# Instancia compartida — importada desde módulo central para evitar duplicados.
# Para multi-réplica: cambiar a Redis con storage_uri="redis://..."
from backend.presentation.rate_limiter import limiter

app = FastAPI(
    title="NutriVet.IA API",
    version="1.0.0",
    description="Planes nutricionales personalizados para perros y gatos.",
)


@app.on_event("shutdown")
async def _shutdown_event() -> None:
    """
    Graceful shutdown: cierra pools de conexiones al recibir SIGTERM.

    Coolify/Docker envían SIGTERM al contenedor. Uvicorn lo captura y dispara
    este evento antes de terminar el proceso. Sin esto, las conexiones a
    PostgreSQL y OpenRouter quedan huérfanas.
    """
    import logging as _logging
    _sd_logger = _logging.getLogger("nutrivet.shutdown")
    _sd_logger.info("Iniciando graceful shutdown...")

    # Cerrar pool de DB
    try:
        from backend.infrastructure.db.session import engine
        await engine.dispose()
        _sd_logger.info("Pool de DB cerrado.")
    except Exception as exc:
        _sd_logger.warning("Error cerrando pool DB: %s", exc)

    _sd_logger.info("Shutdown completado.")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID", "X-Trace-ID"],
)
# CorrelationMiddleware se agrega después de CORS para ejecutarse PRIMERO (orden inverso en Starlette).
# Asegura que trace_id esté disponible para todos los logs del request.
app.add_middleware(CorrelationMiddleware)


# ── Security Headers ─────────────────────────────────────────────────────────
# OWASP recomendaciones: previene clickjacking, sniffing de MIME type, y XSS.
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Agrega headers de seguridad a todas las respuestas."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth_router)
app.include_router(pet_router)
app.include_router(plan_router)
app.include_router(vet_router)
app.include_router(agent_router)
app.include_router(export_router)
app.include_router(device_router)
app.include_router(subscription_router)
app.include_router(admin_router)


@app.get("/health")
async def health() -> dict:
    """
    Health check con verificación de conectividad a PostgreSQL y Redis.
    Coolify y los load balancers usan este endpoint para routing.
    Retorna 503 si la DB no está disponible (crítico).
    Redis y OpenRouter degradados no bloquean el routing.
    """
    from fastapi import status
    from fastapi.responses import JSONResponse
    from backend.infrastructure.db.session import engine

    import logging as _logging
    _hc_logger = _logging.getLogger("nutrivet.health")

    # Check PostgreSQL (crítico — sin DB no hay app)
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        _hc_logger.error("DB health check failed: %s", type(exc).__name__)

    # Check Redis (degradado sin él — BackgroundTasks fallback funciona)
    redis_ok = False
    try:
        redis_url = os.environ.get("REDIS_URL", "")
        if redis_url:
            import httpx as _httpx
            # Verificación simple: intentar conectar al puerto
            _parts = redis_url.replace("redis://", "").split(":")
            _host = _parts[0] if _parts else "localhost"
            import socket
            s = socket.create_connection((_host.split("@")[-1], 6379), timeout=2)
            s.close()
            redis_ok = True
    except Exception:
        pass  # Redis degradado — no crítico

    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "nutrivet-ia",
        "db": "connected" if db_ok else "unavailable",
        "redis": "connected" if redis_ok else "unavailable",
    }
    http_status = 200 if db_ok else 503
    return JSONResponse(content=payload, status_code=http_status)
