"""
PostgreSQLUserRepository — Implementación de IUserRepository con SQLAlchemy async.
Mapea entre UserModel (ORM) y UserAccount (dominio).
"""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.interfaces.user_repository import IUserRepository
from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier
from backend.infrastructure.db.models import UserModel


class PostgreSQLUserRepository(IUserRepository):
    """
    Repositorio de usuarios backed por PostgreSQL vía SQLAlchemy async.

    Responsabilidades:
    - Persistir y recuperar UserAccount.
    - Mapear entre entidades de dominio y modelos ORM.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: Sesión async de SQLAlchemy inyectada por FastAPI.
        """
        self._session = session

    async def save(self, user: UserAccount) -> None:
        """Persiste un UserAccount (INSERT o UPDATE por upsert)."""
        existing = await self._session.get(UserModel, user.id)
        if existing is None:
            model = UserModel(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role.value,
                tier=user.tier.value,
                subscription_status="active",
                is_active=user.is_active,
                full_name=user.full_name,
                phone=user.phone,
                clinic_name=user.clinic_name,
                specialization=user.specialization,
                license_number=user.license_number,
                vet_status=user.vet_status,
            )
            self._session.add(model)
        else:
            existing.email = user.email
            existing.password_hash = user.password_hash
            existing.role = user.role.value
            existing.tier = user.tier.value
            existing.is_active = user.is_active
            existing.full_name = user.full_name
            existing.phone = user.phone
            existing.clinic_name = user.clinic_name
            existing.specialization = user.specialization
            existing.license_number = user.license_number
            existing.vet_status = user.vet_status

    async def find_by_email(self, email: str) -> Optional[UserAccount]:
        """Busca usuario por email. Retorna None si no existe."""
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def find_by_id(self, user_id: uuid.UUID) -> Optional[UserAccount]:
        """Busca usuario por ID. Retorna None si no existe."""
        model = await self._session.get(UserModel, user_id)
        if model is None:
            return None
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: UserModel) -> UserAccount:
        """Mapea UserModel (ORM) → UserAccount (dominio)."""
        return UserAccount(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            role=UserRole(model.role),
            tier=UserTier(model.tier),
            is_active=model.is_active,
            full_name=model.full_name,
            phone=model.phone,
            clinic_name=getattr(model, 'clinic_name', None),
            specialization=getattr(model, 'specialization', None),
            license_number=getattr(model, 'license_number', None),
            vet_status=getattr(model, 'vet_status', None),
        )
