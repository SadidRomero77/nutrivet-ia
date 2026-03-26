"""
Router de device tokens — registro de tokens FCM para push notifications.

POST /v1/devices/token   — registra o actualiza token FCM del dispositivo
DELETE /v1/devices/token — elimina token FCM (logout)
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.auth.jwt_service import TokenPayload
from backend.infrastructure.db.device_token_repository import PostgreSQLDeviceTokenRepository
from backend.infrastructure.db.session import get_db_session
from backend.presentation.middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["devices"])

_VALID_PLATFORMS = {"android", "ios"}


class RegisterTokenRequest(BaseModel):
    """Request para registrar un device token FCM."""
    token: str = Field(..., min_length=10, description="FCM device token")
    platform: str = Field(..., description="android | ios")


class DeleteTokenRequest(BaseModel):
    """Request para eliminar un device token FCM."""
    token: str = Field(..., min_length=10, description="FCM device token a eliminar")


@router.post("/v1/devices/token", status_code=status.HTTP_204_NO_CONTENT)
async def register_device_token(
    body: RegisterTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> None:
    """
    Registra o actualiza el token FCM del dispositivo del usuario.

    Llamar después de login y cuando Firebase actualiza el token.
    El token queda asociado al usuario autenticado.
    """
    platform = body.platform.lower()
    if platform not in _VALID_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Platform inválida: '{body.platform}'. Válidas: android, ios",
        )

    repo = PostgreSQLDeviceTokenRepository(session)
    await repo.upsert(
        user_id=user.user_id,
        token=body.token,
        platform=platform,
    )
    logger.info(
        "device_token registrado: user=%s platform=%s token=...%s",
        user.user_id, platform, body.token[-8:],
    )


@router.delete("/v1/devices/token", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device_token(
    body: DeleteTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> None:
    """
    Elimina el token FCM del dispositivo.

    Llamar al hacer logout para dejar de recibir notificaciones en este dispositivo.
    """
    repo = PostgreSQLDeviceTokenRepository(session)
    await repo.delete_token(token=body.token)
    logger.info(
        "device_token eliminado: user=%s token=...%s",
        user.user_id, body.token[-8:],
    )
