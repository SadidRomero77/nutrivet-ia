"""add_composite_index_pet_status

Índice compuesto (pet_id, status) en nutrition_plans.
Optimiza las queries más frecuentes:
  - GET /v1/plans (filtrar planes del owner por pet + status)
  - Vet dashboard: planes PENDING_VET por mascota
  - count_active_by_owner: cuenta planes ACTIVE por owner

Revision ID: a1b2c3d4e5f6
Revises: e8b3a1f7c294
Create Date: 2026-04-15
"""
from __future__ import annotations

from alembic import op


revision = "a1b2c3d4e5f6"
down_revision = "e8b3a1f7c294"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_nutrition_plans_pet_id_status",
        "nutrition_plans",
        ["pet_id", "status"],
    )
    op.create_index(
        "ix_nutrition_plans_owner_id_status",
        "nutrition_plans",
        ["owner_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_nutrition_plans_owner_id_status", table_name="nutrition_plans")
    op.drop_index("ix_nutrition_plans_pet_id_status", table_name="nutrition_plans")
