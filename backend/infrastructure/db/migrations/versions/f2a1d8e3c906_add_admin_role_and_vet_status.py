"""add_admin_role_and_vet_status

Revision ID: f2a1d8e3c906
Revises: e1b4c7a9f203
Create Date: 2026-03-26 00:00:00.000000

Cambios:
  - Agrega valor 'admin' al enum user_role_enum de la tabla users.
  - Agrega columna vet_status (pending | approved | rejected) para vets.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2a1d8e3c906'
down_revision: Union[str, Sequence[str], None] = 'e1b4c7a9f203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL requiere ALTER TYPE para agregar valores a un enum existente
    op.execute("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'admin'")
    op.add_column('users', sa.Column('vet_status', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'vet_status')
    # No es posible remover valores de un enum en PostgreSQL sin recrearlo
    # Para downgrade completo, recrear el tipo manualmente
