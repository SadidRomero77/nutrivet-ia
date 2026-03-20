"""
Gestión de sesiones SQLAlchemy async — NutriVet.IA.
Provee engine async y factory de sesiones para inyección de dependencias.
"""
from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_DATABASE_URL = os.environ.get(
    "DATABASE_URL_ASYNC",
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://nutrivet:nutrivet_dev_pass@localhost:5432/nutrivet_dev",
    ),
)

engine = create_async_engine(_DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncSession:  # type: ignore[return]
    """
    Dependencia FastAPI que provee una sesión async por request.
    Hace commit automático al finalizar, rollback en caso de error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
