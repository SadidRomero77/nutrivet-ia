"""add_user_profile_and_pet_vet_id

Revision ID: 343bd5b48f0c
Revises: 867f279f3329
Create Date: 2026-03-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '343bd5b48f0c'
down_revision: Union[str, Sequence[str], None] = '867f279f3329'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agrega full_name y phone a users, y vet_id a pets."""
    # Columnas de perfil de usuario
    op.add_column('users', sa.Column('full_name', sa.String(length=150), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(length=30), nullable=True))

    # FK de veterinario en mascotas clínicas
    op.add_column('pets', sa.Column('vet_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_pets_vet_id_users',
        'pets',
        'users',
        ['vet_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(op.f('ix_pets_vet_id'), 'pets', ['vet_id'], unique=False)


def downgrade() -> None:
    """Revierte los cambios de esta migración."""
    op.drop_index(op.f('ix_pets_vet_id'), table_name='pets')
    op.drop_constraint('fk_pets_vet_id_users', 'pets', type_='foreignkey')
    op.drop_column('pets', 'vet_id')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'full_name')
