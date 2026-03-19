"""
Tests de integración — UserRepository + TokenRepository con DB real.
Sin mocks. Requiere PostgreSQL de test corriendo.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
from backend.infrastructure.db.base import Base
from backend.infrastructure.db.models import RefreshTokenModel, UserModel  # noqa: F401
from backend.infrastructure.db.token_repository import PostgreSQLTokenRepository
from backend.infrastructure.db.user_repository import PostgreSQLUserRepository

_TEST_DB_URL = (
    "postgresql+asyncpg://nutrivet:nutrivet_dev_pass@localhost:5432/nutrivet_dev"
)

# ---------------------------------------------------------------------------
# Fixtures de sesión aislada por test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session():  # type: ignore[return]
    """Sesión async con rollback automático al finalizar el test."""
    engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)

    # Asegurar que las tablas existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()

    await engine.dispose()


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------


class TestUserRepository:
    """Tests de integración del repositorio de usuarios."""

    @pytest.mark.asyncio
    async def test_save_y_find_by_email(self, db_session: AsyncSession) -> None:
        """Guardar un usuario y recuperarlo por email."""
        repo = PostgreSQLUserRepository(db_session)
        user = UserAccount.create(
            email=f"test-{uuid.uuid4()}@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
        )

        await repo.save(user)
        await db_session.flush()

        found = await repo.find_by_email(user.email)
        assert found is not None
        assert found.email == user.email
        assert found.role == UserRole.OWNER
        assert found.tier == UserTier.FREE

    @pytest.mark.asyncio
    async def test_find_by_email_no_existe_retorna_none(
        self, db_session: AsyncSession
    ) -> None:
        """Buscar email inexistente retorna None."""
        repo = PostgreSQLUserRepository(db_session)
        result = await repo.find_by_email("noexiste@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_y_find_by_id(self, db_session: AsyncSession) -> None:
        """Guardar un usuario y recuperarlo por ID."""
        repo = PostgreSQLUserRepository(db_session)
        user = UserAccount.create(
            email=f"vet-{uuid.uuid4()}@clinic.com",
            password_hash="hashed",
            role=UserRole.VET,
        )

        await repo.save(user)
        await db_session.flush()

        found = await repo.find_by_id(user.id)
        assert found is not None
        assert found.id == user.id
        assert found.tier == UserTier.VET

    @pytest.mark.asyncio
    async def test_find_by_id_no_existe_retorna_none(
        self, db_session: AsyncSession
    ) -> None:
        """Buscar ID inexistente retorna None."""
        repo = PostgreSQLUserRepository(db_session)
        result = await repo.find_by_id(uuid.uuid4())
        assert result is None


# ---------------------------------------------------------------------------
# TokenRepository
# ---------------------------------------------------------------------------


class TestTokenRepository:
    """Tests de integración del repositorio de refresh tokens."""

    @pytest_asyncio.fixture
    async def user_id(self, db_session: AsyncSession) -> uuid.UUID:
        """Crea un usuario en DB y retorna su ID para tests de tokens."""
        repo = PostgreSQLUserRepository(db_session)
        user = UserAccount.create(
            email=f"tkn-{uuid.uuid4()}@example.com",
            password_hash="hashed",
            role=UserRole.OWNER,
        )
        await repo.save(user)
        await db_session.flush()
        return user.id

    @pytest.mark.asyncio
    async def test_save_y_find_valid_token(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Guardar un refresh token y encontrarlo como válido."""
        repo = PostgreSQLTokenRepository(db_session)
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        await repo.save_refresh_token(user_id=user_id, token=token, expires_at=expires_at)
        await db_session.flush()

        result = await repo.find_valid_token(token)
        assert result is not None
        assert result["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_token_inexistente_retorna_none(
        self, db_session: AsyncSession
    ) -> None:
        """Buscar token inexistente retorna None."""
        repo = PostgreSQLTokenRepository(db_session)
        result = await repo.find_valid_token("token-no-existe")
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_token_invalida_busqueda(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Revocar un token lo hace inválido para búsquedas futuras."""
        repo = PostgreSQLTokenRepository(db_session)
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        await repo.save_refresh_token(user_id=user_id, token=token, expires_at=expires_at)
        await db_session.flush()

        # Verificar que existe
        result = await repo.find_valid_token(token)
        assert result is not None

        # Revocar
        await repo.revoke_token(token)
        await db_session.flush()

        # Ya no debe encontrarse
        result = await repo.find_valid_token(token)
        assert result is None

    @pytest.mark.asyncio
    async def test_token_expirado_no_se_encuentra(
        self, db_session: AsyncSession, user_id: uuid.UUID
    ) -> None:
        """Token con fecha de expiración pasada no se retorna como válido."""
        repo = PostgreSQLTokenRepository(db_session)
        token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)  # ya expirado

        await repo.save_refresh_token(user_id=user_id, token=token, expires_at=expires_at)
        await db_session.flush()

        result = await repo.find_valid_token(token)
        assert result is None
