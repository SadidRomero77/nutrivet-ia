"""
Tests de endpoints de autenticación — FastAPI con DB real.
Cubre: register, login, refresh, logout.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.infrastructure.auth.jwt_service import JWTService
from backend.infrastructure.db.base import Base
from backend.infrastructure.db.models import RefreshTokenModel, UserModel  # noqa: F401
from backend.infrastructure.db.session import get_db_session
from backend.presentation.middleware.auth_middleware import get_jwt_service
from backend.presentation.routers.auth_router import router

import os
_TEST_DB_URL = os.environ.get(
    "DATABASE_URL_ASYNC",
    "postgresql+asyncpg://nutrivet:nutrivet_dev_pass@localhost:5432/nutrivet_dev",
)
_TEST_SECRET = "test-router-secret-abc"
_test_jwt = JWTService(secret_key=_TEST_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# App de test con overrides de dependencias
# ---------------------------------------------------------------------------


def build_test_app(session_factory: async_sessionmaker) -> FastAPI:
    """Construye app FastAPI de test con sesión aislada y JWT de test."""
    app = FastAPI()
    app.include_router(router)

    async def _override_session():  # type: ignore[return]
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_jwt_service] = lambda: _test_jwt

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def async_client():  # type: ignore[return]
    """Cliente HTTP async con app de test y DB real."""
    engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    app = build_test_app(session_factory)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    await engine.dispose()


@pytest.fixture
def unique_email() -> str:
    """Email único por test para evitar conflictos en DB."""
    return f"user-{uuid.uuid4()}@test.com"


# ---------------------------------------------------------------------------
# Tests de registro
# ---------------------------------------------------------------------------


class TestRegisterEndpoint:
    """Tests del endpoint POST /v1/auth/register."""

    @pytest.mark.asyncio
    async def test_registro_owner_exitoso(
        self, async_client: AsyncClient, unique_email: str
    ) -> None:
        """Registro exitoso retorna 201 con tokens."""
        resp = await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "Valida123", "role": "owner"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_registro_vet_exitoso(
        self, async_client: AsyncClient, unique_email: str
    ) -> None:
        """Registro de vet retorna 201."""
        resp = await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "Segura456", "role": "vet"},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_registro_email_duplicado_409(
        self, async_client: AsyncClient, unique_email: str
    ) -> None:
        """Email duplicado retorna 409 Conflict."""
        payload = {"email": unique_email, "password": "Valida123", "role": "owner"}
        await async_client.post("/v1/auth/register", json=payload)

        resp = await async_client.post("/v1/auth/register", json=payload)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_registro_password_debil_422(
        self, async_client: AsyncClient, unique_email: str
    ) -> None:
        """Contraseña de menos de 8 caracteres retorna 422."""
        resp = await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "abc", "role": "owner"},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Tests de login
# ---------------------------------------------------------------------------


class TestLoginEndpoint:
    """Tests del endpoint POST /v1/auth/login."""

    @pytest_asyncio.fixture
    async def registered_user(
        self, async_client: AsyncClient, unique_email: str
    ) -> dict:
        """Registra un usuario y retorna sus credenciales."""
        await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "Valida123", "role": "owner"},
        )
        return {"email": unique_email, "password": "Valida123"}

    @pytest.mark.asyncio
    async def test_login_credenciales_correctas(
        self, async_client: AsyncClient, registered_user: dict
    ) -> None:
        """Login con credenciales correctas retorna 200 con tokens."""
        resp = await async_client.post("/v1/auth/login", json=registered_user)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_password_incorrecto_401(
        self, async_client: AsyncClient, registered_user: dict
    ) -> None:
        """Password incorrecto retorna 401."""
        resp = await async_client.post(
            "/v1/auth/login",
            json={"email": registered_user["email"], "password": "Incorrecta999"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_email_no_existe_401(
        self, async_client: AsyncClient
    ) -> None:
        """Email inexistente retorna 401."""
        resp = await async_client.post(
            "/v1/auth/login",
            json={"email": "noexiste@example.com", "password": "Valida123"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests de refresh
# ---------------------------------------------------------------------------


class TestRefreshEndpoint:
    """Tests del endpoint POST /v1/auth/refresh."""

    @pytest_asyncio.fixture
    async def tokens(self, async_client: AsyncClient, unique_email: str) -> dict:
        """Registra usuario y retorna sus tokens iniciales."""
        resp = await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "Valida123", "role": "owner"},
        )
        return resp.json()

    @pytest.mark.asyncio
    async def test_refresh_token_valido(
        self, async_client: AsyncClient, tokens: dict
    ) -> None:
        """Refresh token válido retorna 200 con nuevos tokens."""
        resp = await async_client.post(
            "/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        # El nuevo refresh token es diferente (rotación)
        assert data["refresh_token"] != tokens["refresh_token"]

    @pytest.mark.asyncio
    async def test_refresh_token_invalido_401(
        self, async_client: AsyncClient
    ) -> None:
        """Refresh token inválido retorna 401."""
        resp = await async_client.post(
            "/v1/auth/refresh",
            json={"refresh_token": "token-que-no-existe"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests de logout
# ---------------------------------------------------------------------------


class TestLogoutEndpoint:
    """Tests del endpoint POST /v1/auth/logout."""

    @pytest.mark.asyncio
    async def test_logout_retorna_204(
        self, async_client: AsyncClient, unique_email: str
    ) -> None:
        """Logout siempre retorna 204 No Content."""
        reg_resp = await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "Valida123", "role": "owner"},
        )
        refresh_token = reg_resp.json()["refresh_token"]

        resp = await async_client.post(
            "/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_logout_invalida_refresh_token(
        self, async_client: AsyncClient, unique_email: str
    ) -> None:
        """Después de logout, el refresh token ya no puede usarse."""
        reg_resp = await async_client.post(
            "/v1/auth/register",
            json={"email": unique_email, "password": "Valida123", "role": "owner"},
        )
        refresh_token = reg_resp.json()["refresh_token"]

        # Logout
        await async_client.post(
            "/v1/auth/logout",
            json={"refresh_token": refresh_token},
        )

        # Intentar refresh con token revocado
        resp = await async_client.post(
            "/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401
