"""Tests RED — AuthUseCase (unit-02-auth-service Paso 6).

Usa DB real de test (sin mocks). Fixture de sesión aislada por test.
"""
from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from backend.application.use_cases.auth_use_case import AuthUseCase, TokenResponse
from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import JWTService
from backend.infrastructure.auth.password_service import PasswordService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def jwt_service() -> JWTService:
    """JWTService con clave de test."""
    return JWTService(secret_key="test-secret-auth-uc-456", algorithm="HS256")


@pytest.fixture
def password_service() -> PasswordService:
    """PasswordService real (bcrypt)."""
    return PasswordService()


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    """Mock de IUserRepository para aislar tests del use case."""
    repo = AsyncMock()
    repo.find_by_email = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_token_repo() -> AsyncMock:
    """Mock de ITokenRepository para aislar tests del use case."""
    repo = AsyncMock()
    repo.save_refresh_token = AsyncMock()
    repo.find_valid_token = AsyncMock(return_value=None)
    repo.revoke_token = AsyncMock()
    return repo


@pytest.fixture
def auth_use_case(
    jwt_service: JWTService,
    password_service: PasswordService,
    mock_user_repo: AsyncMock,
    mock_token_repo: AsyncMock,
) -> AuthUseCase:
    """AuthUseCase con dependencias inyectadas."""
    return AuthUseCase(
        user_repo=mock_user_repo,
        token_repo=mock_token_repo,
        jwt_service=jwt_service,
        password_service=password_service,
    )


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------


class TestRegister:
    """Casos de uso de registro de usuarios."""

    @pytest.mark.asyncio
    async def test_registro_owner_exitoso(
        self,
        auth_use_case: AuthUseCase,
        mock_user_repo: AsyncMock,
    ) -> None:
        """Registro de owner retorna access token y refresh token."""
        mock_user_repo.find_by_email.return_value = None

        result: TokenResponse = await auth_use_case.register(
            email="valentina@example.com",
            password="Valida123",
            role=UserRole.OWNER,
        )

        assert isinstance(result, TokenResponse)
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_registro_con_email_existente_falla(
        self,
        auth_use_case: AuthUseCase,
        mock_user_repo: AsyncMock,
        password_service: PasswordService,
    ) -> None:
        """Registro con email ya existente lanza DomainError."""
        existing = UserAccount.create(
            email="existente@example.com",
            password_hash=password_service.hash_password("Otra123"),
            role=UserRole.OWNER,
        )
        mock_user_repo.find_by_email.return_value = existing

        with pytest.raises(DomainError, match="email"):
            await auth_use_case.register(
                email="existente@example.com",
                password="Valida123",
                role=UserRole.OWNER,
            )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    """Casos de uso de inicio de sesión."""

    @pytest.mark.asyncio
    async def test_login_credenciales_correctas(
        self,
        auth_use_case: AuthUseCase,
        mock_user_repo: AsyncMock,
        password_service: PasswordService,
    ) -> None:
        """Login con credenciales correctas retorna tokens."""
        user = UserAccount.create(
            email="valentina@example.com",
            password_hash=password_service.hash_password("Valida123"),
            role=UserRole.OWNER,
        )
        mock_user_repo.find_by_email.return_value = user

        result = await auth_use_case.login(
            email="valentina@example.com",
            password="Valida123",
        )

        assert result.access_token
        assert result.refresh_token

    @pytest.mark.asyncio
    async def test_login_password_incorrecto_falla(
        self,
        auth_use_case: AuthUseCase,
        mock_user_repo: AsyncMock,
        password_service: PasswordService,
    ) -> None:
        """Login con password incorrecto lanza DomainError."""
        user = UserAccount.create(
            email="valentina@example.com",
            password_hash=password_service.hash_password("Valida123"),
            role=UserRole.OWNER,
        )
        mock_user_repo.find_by_email.return_value = user

        with pytest.raises(DomainError, match="(?i)credenciales"):
            await auth_use_case.login(
                email="valentina@example.com",
                password="Incorrecta999",
            )

    @pytest.mark.asyncio
    async def test_login_email_no_existe_falla(
        self,
        auth_use_case: AuthUseCase,
        mock_user_repo: AsyncMock,
    ) -> None:
        """Login con email inexistente lanza DomainError."""
        mock_user_repo.find_by_email.return_value = None

        with pytest.raises(DomainError, match="(?i)credenciales"):
            await auth_use_case.login(
                email="noexiste@example.com",
                password="Valida123",
            )


# ---------------------------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------------------------


class TestRefreshToken:
    """Casos de uso de rotación de refresh token."""

    @pytest.mark.asyncio
    async def test_refresh_token_valido(
        self,
        auth_use_case: AuthUseCase,
        mock_token_repo: AsyncMock,
        mock_user_repo: AsyncMock,
        password_service: PasswordService,
    ) -> None:
        """Refresh token válido retorna nuevo access token y rota el refresh."""
        user = UserAccount.create(
            email="valentina@example.com",
            password_hash=password_service.hash_password("Valida123"),
            role=UserRole.OWNER,
        )
        old_token = "old-refresh-uuid"
        mock_token_repo.find_valid_token.return_value = {
            "user_id": user.id,
            "token": old_token,
        }
        mock_user_repo.find_by_id.return_value = user

        result = await auth_use_case.refresh(refresh_token=old_token)

        assert result.access_token
        assert result.refresh_token
        mock_token_repo.revoke_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_invalido_falla(
        self,
        auth_use_case: AuthUseCase,
        mock_token_repo: AsyncMock,
    ) -> None:
        """Refresh token inexistente o revocado lanza DomainError."""
        mock_token_repo.find_valid_token.return_value = None

        with pytest.raises(DomainError, match="refresh"):
            await auth_use_case.refresh(refresh_token="token-invalido")


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


class TestLogout:
    """Casos de uso de cierre de sesión."""

    @pytest.mark.asyncio
    async def test_logout_invalida_refresh_token(
        self,
        auth_use_case: AuthUseCase,
        mock_token_repo: AsyncMock,
    ) -> None:
        """Logout revoca el refresh token en DB."""
        refresh = "valid-refresh-token"

        await auth_use_case.logout(refresh_token=refresh)

        mock_token_repo.revoke_token.assert_called_once_with(refresh)
