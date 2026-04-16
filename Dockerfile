# ─── Stage 1: Build ──────────────────────────────────────────────────────────
# Instala dependencias en una capa cacheable separada del código.
FROM python:3.12-slim AS builder

WORKDIR /app

# Dependencias de sistema para compilar paquetes nativos (psycopg2, weasyprint, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo archivos de dependencias primero (cache layer)
COPY pyproject.toml uv.lock ./

# Instalar uv y dependencias de producción (sin dev)
RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev --no-editable

# ─── Stage 2: Runtime ──────────��─────────────────────────────────────────────
# Imagen mínima sin herramientas de build.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Dependencias de sistema SOLO runtime (sin build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash nutrivet

# Copiar virtualenv desde builder
COPY --from=builder /app/.venv /app/.venv

# Copiar código fuente
COPY main.py pyproject.toml alembic.ini ./
COPY backend/ backend/
COPY domain/ domain/
COPY scripts/ scripts/

# Asegurar que el virtualenv está en el PATH
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Cambiar a usuario no-root (seguridad — OWASP)
USER nutrivet

# Health check — Coolify y Docker Compose lo usan para routing
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Uvicorn con 2 workers — ajustar según CPU del VPS (CPX31 = 4 vCPU)
# --proxy-headers: confía en X-Forwarded-For de Coolify/Caddy
# --forwarded-allow-ips='*': permite proxy headers de cualquier IP interna
CMD ["uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "2", \
    "--proxy-headers", \
    "--forwarded-allow-ips", "*", \
    "--log-level", "info"]
