"""
Repositorio de device tokens FCM — registro y consulta de tokens por usuario.
"""
from __future__ import annotations

import uuid
import logging

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.db.models import DeviceTokenModel

logger = logging.getLogger(__name__)

_MAX_TOKENS_PER_USER = 5  # máximo de dispositivos simultáneos por usuario


class PostgreSQLDeviceTokenRepository:
    """Repositorio SQLAlchemy para device tokens FCM."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        user_id: uuid.UUID,
        token: str,
        platform: str,
    ) -> None:
        """
        Registra o actualiza un device token para el usuario.

        Si el token ya existe (de cualquier usuario), lo reasigna al usuario
        actual (un dispositivo puede cambiar de usuario al hacer login).
        Limita a _MAX_TOKENS_PER_USER tokens por usuario eliminando los más viejos.

        Args:
            user_id: ID del usuario.
            token: FCM device token.
            platform: "android" | "ios".
        """
        # Upsert: si el token existe lo actualiza, si no lo crea
        stmt = (
            pg_insert(DeviceTokenModel)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                token=token,
                platform=platform,
            )
            .on_conflict_do_update(
                index_elements=["token"],
                set_={"user_id": user_id, "platform": platform},
            )
        )
        await self._session.execute(stmt)

        # Limpiar tokens viejos si supera el límite
        tokens_q = await self._session.execute(
            select(DeviceTokenModel.id)
            .where(DeviceTokenModel.user_id == user_id)
            .order_by(DeviceTokenModel.updated_at.desc())
        )
        token_ids = [row[0] for row in tokens_q.all()]
        if len(token_ids) > _MAX_TOKENS_PER_USER:
            ids_a_eliminar = token_ids[_MAX_TOKENS_PER_USER:]
            await self._session.execute(
                delete(DeviceTokenModel).where(
                    DeviceTokenModel.id.in_(ids_a_eliminar)
                )
            )

        await self._session.commit()

    async def delete_token(self, token: str) -> None:
        """
        Elimina un device token (logout o app desinstalada).

        Args:
            token: FCM device token a eliminar.
        """
        await self._session.execute(
            delete(DeviceTokenModel).where(DeviceTokenModel.token == token)
        )
        await self._session.commit()

    async def get_tokens_for_user(self, user_id: uuid.UUID) -> list[str]:
        """
        Retorna todos los device tokens activos de un usuario.

        Args:
            user_id: ID del usuario.

        Returns:
            Lista de FCM tokens del usuario.
        """
        result = await self._session.execute(
            select(DeviceTokenModel.token)
            .where(DeviceTokenModel.user_id == user_id)
            .order_by(DeviceTokenModel.updated_at.desc())
        )
        return [row[0] for row in result.all()]
