"""
Router de autenticación — FastAPI.
Endpoints: /v1/auth/register, /v1/auth/login, /v1/auth/refresh, /v1/auth/logout, /v1/auth/me.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.use_cases.auth_use_case import (
    AuthUseCase,
    TokenResponse as UseCaseTokenResponse,
)
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import JWTService, TokenPayload
from backend.infrastructure.auth.password_service import PasswordService
from backend.infrastructure.db.session import get_db_session
from backend.infrastructure.db.token_repository import PostgreSQLTokenRepository
from backend.infrastructure.db.user_repository import PostgreSQLUserRepository
from backend.presentation.middleware.auth_middleware import get_current_user, get_jwt_service
from backend.presentation.schemas.auth_schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _build_use_case(
    session: AsyncSession,
    jwt_service: JWTService,
) -> AuthUseCase:
    """Construye el AuthUseCase con sus dependencias de infraestructura."""
    return AuthUseCase(
        user_repo=PostgreSQLUserRepository(session),
        token_repo=PostgreSQLTokenRepository(session),
        jwt_service=jwt_service,
        password_service=PasswordService(),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """
    Registra un nuevo usuario (owner o vet) y retorna tokens JWT.

    - **email**: Correo electrónico único.
    - **password**: Mínimo 8 caracteres, una mayúscula y un número.
    - **role**: `owner` (propietario de mascota) o `vet` (veterinario).
    """
    try:
        uc = _build_use_case(session, jwt_service)
        result: UseCaseTokenResponse = await uc.register(
            email=str(body.email),
            password=body.password,
            role=body.role,
            full_name=body.full_name,
            phone=body.phone,
        )
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """
    Autentica un usuario y retorna tokens JWT.

    Mensaje de error genérico para evitar enumeración de usuarios.
    """
    try:
        uc = _build_use_case(session, jwt_service)
        result = await uc.login(email=str(body.email), password=body.password)
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotar refresh token",
)
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """
    Rota el refresh token y emite un nuevo par de tokens.

    El refresh token anterior queda invalidado inmediatamente.
    """
    try:
        uc = _build_use_case(session, jwt_service)
        result = await uc.refresh(refresh_token=body.refresh_token)
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
async def logout(
    body: LogoutRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> None:
    """
    Cierra sesión invalidando el refresh token en DB.

    Retorna 204 No Content en todos los casos (no revela si el token era válido).
    """
    uc = _build_use_case(session, jwt_service)
    await uc.logout(refresh_token=body.refresh_token)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Perfil del usuario autenticado",
)
async def get_me(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> UserProfileResponse:
    """Obtiene el perfil del usuario autenticado."""
    user_repo = PostgreSQLUserRepository(session)
    user_obj = await user_repo.find_by_id(user.user_id)
    if user_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return UserProfileResponse(
        user_id=user_obj.id,
        email=user_obj.email,
        role=user_obj.role.value,
        tier=user_obj.tier.value,
        full_name=user_obj.full_name,
        phone=user_obj.phone,
    )


@router.get(
    "/vet/{vet_id}/profile",
    response_model=UserProfileResponse,
    summary="Perfil público de un veterinario",
)
async def get_vet_profile(
    vet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> UserProfileResponse:
    """Obtiene el perfil público de un veterinario (nombre y contacto)."""
    user_repo = PostgreSQLUserRepository(session)
    vet = await user_repo.find_by_id(vet_id)
    if vet is None or vet.role.value != 'vet':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinario no encontrado.")
    return UserProfileResponse(
        user_id=vet.id,
        email=vet.email,
        role=vet.role.value,
        tier=vet.tier.value,
        full_name=vet.full_name,
        phone=vet.phone,
    )
