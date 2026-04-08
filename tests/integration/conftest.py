"""
Fixtures de integración — PostgreSQL real vía testcontainers.

Cada test recibe una sesión aislada con rollback automático al terminar:
el esquema se crea una vez por sesión de pytest (scope=session) y cada
test individual recibe su propia transacción que se revierte al finalizar.

Requiere Docker en el entorno de CI/CD.
Para saltar estos tests localmente sin Docker: pytest --ignore=tests/integration
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Clave Fernet de test (no confidencial — solo para entorno de test)
os.environ.setdefault(
    "FERNET_KEY",
    "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
)
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-integration-tests")

# Import diferido: los modelos se importan DESPUÉS de setear FERNET_KEY
from backend.infrastructure.db.base import Base  # noqa: E402
import backend.infrastructure.db.models  # noqa: F401, E402 — registra todos los ORM models en Base.metadata


@pytest.fixture(scope="session")
def pg_container():
    """
    Levanta un contenedor PostgreSQL para toda la sesión de tests.

    El contenedor se destruye automáticamente al finalizar pytest.
    Si Docker no está disponible, el fixture falla con un error claro.
    """
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers no instalado — saltar integration tests")

    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def pg_engine(pg_container):
    """Motor SQLAlchemy async conectado al contenedor PostgreSQL."""
    import asyncio

    url = pg_container.get_connection_url().replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://"
    )

    engine = create_async_engine(url, poolclass=NullPool)

    # Crear esquema una sola vez para toda la sesión
    async def _create_schema():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create_schema())

    yield engine

    loop.run_until_complete(engine.dispose())
    loop.close()


@pytest_asyncio.fixture
async def db_session(pg_engine):
    """
    Sesión DB con transacción aislada por test.

    Cada test recibe una transacción anidada (SAVEPOINT) que se revierte
    al finalizar — los datos no persisten entre tests.
    """
    session_factory = async_sessionmaker(
        bind=pg_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
