"""merge_all_heads

Revision ID: 1e222fb7b70d
Revises: 343bd5b48f0c, f2a1d8e3c906
Create Date: 2026-03-26 20:36:03.498342

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e222fb7b70d'
down_revision: Union[str, Sequence[str], None] = ('343bd5b48f0c', 'f2a1d8e3c906')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
