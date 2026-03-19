"""
AuthUseCase — Casos de uso de autenticación.
Orquesta: registro, login, refresh de token, logout.
Depende solo de interfaces (puertos), no de infraestructura concreta.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.application.interfaces.token_repository import ITokenRepository
from backend.application.interfaces.user_repository import IUserRepository
from backend.domain.aggregates.user_account import UserAccount, UserRole
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import JWTService
from backend.infrastructure.auth.password_service import PasswordService

_REFRESH_TOKEN_DAYS = 30


@dataclass
class TokenResponse:
    """DTO de respuesta con tokens de autenticación."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthUseCase:
    """
    Casos de uso de autenticación y autorización.

    Implementa:
    - register: Registro de nuevo usuario (owner o vet).
    - login: Autenticación con email + contraseña.
    - refresh: Rotación de refresh token → nuevo access token.
    - logout: Revocación de refresh token.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: ITokenRepository,
        jwt_service: JWTService,
        password_service: PasswordService,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._jwt_service = jwt_service
        self._password_service = password_service

    async def register(
        self,
        email: str,
        password: str,
        role: UserRole,
    ) -> TokenResponse:
        """
        Registra un nuevo usuario y retorna tokens de acceso.

        Args:
            email: Dirección de correo electrónico única.
            password: Contraseña en texto plano (se hashea antes de persistir).
            role: Rol del usuario (owner / vet).

        Returns:
            TokenResponse con access_token y refresh_token.

        Raises:
            DomainError: Si el email ya está registrado o la contraseña es inválida.
        """
        # Validar contraseña antes de cualquier operación
        UserAccount.validate_raw_password(password)

        # Verificar unicidad del email
        existing = await self._user_repo.find_by_email(email)
        if existing is not None:
            raise DomainError(
                f"El email '{email}' ya está registrado en el sistema."
            )

        # Crear usuario
        password_hash = self._password_service.hash_password(password)
        user = UserAccount.create(email=email, password_hash=password_hash, role=role)
        await self._user_repo.save(user)

        # Emitir tokens
        return await self._emit_tokens(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Autentica un usuario con email y contraseña.

        Args:
            email: Correo electrónico del usuario.
            password: Contraseña en texto plano.

        Returns:
            TokenResponse con access_token y refresh_token.

        Raises:
            DomainError: Si las credenciales son incorrectas (mensaje genérico
                         para evitar enumeración de usuarios).
        """
        _CREDENCIALES_INVALIDAS = DomainError(
            "Credenciales incorrectas. Verifica tu email y contraseña."
        )

        user = await self._user_repo.find_by_email(email)
        if user is None:
            raise _CREDENCIALES_INVALIDAS

        if not self._password_service.verify_password(password, user.password_hash):
            raise _CREDENCIALES_INVALIDAS

        return await self._emit_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Rota un refresh token y emite nuevos tokens.

        Args:
            refresh_token: Refresh token UUID presentado por el cliente.

        Returns:
            TokenResponse con nuevos tokens.

        Raises:
            DomainError: Si el refresh token no existe, está revocado o expiró.
        """
        token_data = await self._token_repo.find_valid_token(refresh_token)
        if token_data is None:
            raise DomainError(
                "El refresh token es inválido, ha sido revocado o ha expirado."
            )

        user = await self._user_repo.find_by_id(token_data["user_id"])
        if user is None:
            raise DomainError("Usuario no encontrado para el refresh token presentado.")

        # Revocar token anterior (rotación)
        await self._token_repo.revoke_token(refresh_token)

        return await self._emit_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        """
        Cierra sesión revocando el refresh token en DB.

        Args:
            refresh_token: Refresh token a invalidar.
        """
        await self._token_repo.revoke_token(refresh_token)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _emit_tokens(self, user: UserAccount) -> TokenResponse:
        """Genera access token + refresh token y persiste el refresh en DB."""
        access_token = self._jwt_service.create_access_token(
            user_id=user.id,
            role=user.role,
            tier=user.tier,
        )
        refresh_token = self._jwt_service.create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=_REFRESH_TOKEN_DAYS)

        await self._token_repo.save_refresh_token(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
