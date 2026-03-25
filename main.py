"""
NutriVet.IA — FastAPI application entrypoint.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Carga vars de entorno:
# - Producción/staging: vars vienen del contenedor (Docker/Coolify) — load_dotenv() es no-op.
# - Dev local: carga .env si existe, luego .env.dev como fallback.
# override=False: las vars del entorno del sistema tienen prioridad sobre el archivo.
load_dotenv(override=False) or load_dotenv(".env.dev", override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.presentation.routers.auth_router import router as auth_router
from backend.presentation.routers.pet_router import router as pet_router
from backend.presentation.routers.plan_router import router as plan_router
from backend.presentation.routers.plan_router import vet_router
from backend.presentation.routers.agent_router import router as agent_router
from backend.presentation.routers.export_router import router as export_router

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
# Backend: in-memory por IP (adecuado para piloto mono-servidor).
# Para multi-réplica: cambiar a Redis con storage_uri="redis://..."
# Límites por endpoint se definen en cada router con @limiter.limit("X/minute").
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(
    title="NutriVet.IA API",
    version="1.0.0",
    description="Planes nutricionales personalizados para perros y gatos.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

app.include_router(auth_router)
app.include_router(pet_router)
app.include_router(plan_router)
app.include_router(vet_router)
app.include_router(agent_router)
app.include_router(export_router)


@app.get("/health")
async def health() -> dict:
    """
    Health check con verificación de conectividad a PostgreSQL.
    Coolify y los load balancers usan este endpoint para routing.
    Retorna 503 si la DB no está disponible.
    """
    from fastapi import status
    from fastapi.responses import JSONResponse
    from backend.infrastructure.db.session import engine

    import logging as _logging
    _hc_logger = _logging.getLogger("nutrivet.health")

    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        # Log interno con detalle — nunca exponer al exterior (OWASP A05)
        _hc_logger.error("DB health check failed: %s", type(exc).__name__)

    payload = {
        "status": "ok" if db_ok else "degraded",
        "service": "nutrivet-ia",
        "db": "connected" if db_ok else "unavailable",
    }
    http_status = 200 if db_ok else 503
    return JSONResponse(content=payload, status_code=http_status)
