"""
IUserRepository — Puerto (interfaz) del repositorio de usuarios.
La capa de aplicación depende de esta abstracción, no de SQLAlchemy.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from backend.domain.aggregates.user_account import UserAccount


class IUserRepository(ABC):
    """Interfaz del repositorio de cuentas de usuario."""

    @abstractmethod
    async def save(self, user: UserAccount) -> None:
        """Persiste un UserAccount nuevo o actualiza uno existente."""
        ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[UserAccount]:
        """Busca un usuario por email. Retorna None si no existe."""
        ...

    @abstractmethod
    async def find_by_id(self, user_id: uuid.UUID) -> Optional[UserAccount]:
        """Busca un usuario por ID. Retorna None si no existe."""
        ...
