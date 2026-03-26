"""add_device_tokens_and_payments

Revision ID: c3a8f9e1d042
Revises: f5951fc0f352
Create Date: 2026-03-25 00:00:00.000000

Agrega tablas:
  - device_tokens: tokens FCM para push notifications por usuario/dispositivo.
  - payments: registro de pagos PayU Colombia para suscripciones.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3a8f9e1d042'
down_revision: Union[str, Sequence[str], None] = 'f5951fc0f352'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — agrega device_tokens y payments."""
    # ── device_tokens ──────────────────────────────────────────────────────────
    op.create_table(
        'device_tokens',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('platform', sa.String(length=10), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_device_tokens_user_id', 'device_tokens', ['user_id'])
    op.create_index('ix_device_tokens_token', 'device_tokens', ['token'])

    # ── payments ───────────────────────────────────────────────────────────────
    op.create_table(
        'payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('reference_code', sa.String(length=100), nullable=False),
        sa.Column('tier', sa.String(length=20), nullable=False),
        sa.Column('amount_cop', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=5), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('payu_transaction_id', sa.String(length=100), nullable=True),
        sa.Column('payu_order_id', sa.String(length=100), nullable=True),
        sa.Column('raw_webhook', sa.JSON(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_code'),
    )
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_reference_code', 'payments', ['reference_code'])


def downgrade() -> None:
    """Downgrade schema — elimina device_tokens y payments."""
    op.drop_index('ix_payments_reference_code', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_table('payments')
    op.drop_index('ix_device_tokens_token', table_name='device_tokens')
    op.drop_index('ix_device_tokens_user_id', table_name='device_tokens')
    op.drop_table('device_tokens')
