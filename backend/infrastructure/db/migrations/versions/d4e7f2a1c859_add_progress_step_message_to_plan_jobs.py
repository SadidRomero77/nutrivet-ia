"""add_progress_step_message_to_plan_jobs

Agrega dos columnas a plan_jobs para exponer el progreso granular
del worker durante el polling (C1 — feedback progresivo):
  - progress_step: paso actual (0-10, 0=no iniciado)
  - progress_message: mensaje legible del paso actual

Revision ID: d4e7f2a1c859
Revises: b9c2e4f1a837
Create Date: 2026-04-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "d4e7f2a1c859"
down_revision = "b9c2e4f1a837"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plan_jobs",
        sa.Column("progress_step", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "plan_jobs",
        sa.Column("progress_message", sa.String(200), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("plan_jobs", "progress_message")
    op.drop_column("plan_jobs", "progress_step")
