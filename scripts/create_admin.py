#!/usr/bin/env python3
"""
Script de bootstrap — crea el primer usuario administrador de NutriVet.IA.

Uso:
    python scripts/create_admin.py --email admin@nutrivet.ia --password MiClave123

El script crea un usuario con rol 'admin' si el email no existe.
Si ya existe, no hace nada (idempotente).

Requisitos:
    - DATABASE_URL configurada en el entorno (o .env)
    - JWT_SECRET_KEY configurada
"""
from __future__ import annotations

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Agrega la raíz del proyecto al PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv(override=False) or load_dotenv(".env.dev", override=False)


async def create_admin(email: str, password: str, full_name: str | None) -> None:
    """Crea el usuario admin si no existe."""
    from backend.infrastructure.db.session import AsyncSessionLocal
    from backend.infrastructure.db.user_repository import PostgreSQLUserRepository
    from backend.infrastructure.auth.password_service import PasswordService
    from backend.domain.aggregates.user_account import UserAccount, UserRole, UserTier

    async with AsyncSessionLocal() as session:
        user_repo = PostgreSQLUserRepository(session)
        existing = await user_repo.find_by_email(email)

        if existing is not None:
            print(f"✓ El usuario '{email}' ya existe (rol: {existing.role.value}). Sin cambios.")
            return

        pw_service = PasswordService()
        admin = UserAccount(
            id=__import__("uuid").uuid4(),
            email=email.lower().strip(),
            password_hash=pw_service.hash(password),
            role=UserRole.ADMIN,
            tier=UserTier.VET,  # Admin tiene acceso completo
            is_active=True,
            full_name=full_name or "Administrador NutriVet.IA",
        )
        await user_repo.save(admin)
        await session.commit()
        print(f"✅ Admin creado: {email}")
        print(f"   ID: {admin.id}")
        print(f"   Rol: {admin.role.value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crear usuario administrador de NutriVet.IA")
    parser.add_argument("--email", required=True, help="Email del admin")
    parser.add_argument("--password", required=True, help="Contraseña (mínimo 8 caracteres)")
    parser.add_argument("--name", default=None, help="Nombre completo (opcional)")
    args = parser.parse_args()

    if len(args.password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    asyncio.run(create_admin(args.email, args.password, args.name))


if __name__ == "__main__":
    main()
