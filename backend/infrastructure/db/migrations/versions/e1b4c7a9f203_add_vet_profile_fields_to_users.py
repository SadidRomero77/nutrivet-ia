"""add_vet_profile_fields_to_users

Revision ID: e1b4c7a9f203
Revises: c3a8f9e1d042
Create Date: 2026-03-25 00:00:00.000000

Agrega campos de perfil profesional a la tabla users:
  - clinic_name: nombre de la clínica veterinaria (solo vets)
  - specialization: especialización clínica (solo vets)
  - license_number: cédula profesional / número de tarjeta profesional (solo vets)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b4c7a9f203'
down_revision: Union[str, Sequence[str], None] = 'c3a8f9e1d042'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('clinic_name', sa.String(200), nullable=True))
    op.add_column('users', sa.Column('specialization', sa.String(150), nullable=True))
    op.add_column('users', sa.Column('license_number', sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'license_number')
    op.drop_column('users', 'specialization')
    op.drop_column('users', 'clinic_name')
