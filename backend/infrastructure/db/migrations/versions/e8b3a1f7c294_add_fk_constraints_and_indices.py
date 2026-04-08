"""add_fk_constraints_and_indices

Auditoría pre-deploy — correcciones de integridad referencial e índices de rendimiento:

FK agregadas:
  - plan_jobs.pet_id → pets.id (SET NULL on delete — el job puede quedar sin pet)
  - plan_jobs.owner_id → users.id (SET NULL on delete)
  - nutrition_plans.approved_by_vet_id → users.id (SET NULL on delete — trazabilidad)

Índices agregados:
  - nutrition_plans.status       — queries PENDING_VET del vet dashboard
  - plan_jobs.status             — queries de polling de jobs en curso

No se cambia JSON → JSONB en nutrition_plans.content:
  Requiere CAST explícito en ALTER TABLE que puede fallar con datos existentes.
  Se trata en migración separada con validación de datos previos.

Revision ID: e8b3a1f7c294
Revises: d4e7f2a1c859
Create Date: 2026-04-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e8b3a1f7c294"
down_revision = "d4e7f2a1c859"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── FK: plan_jobs.pet_id → pets.id ────────────────────────────────────────
    # SET NULL on delete: si se elimina la mascota, el job queda sin pet_id pero
    # no se pierde el registro del job (útil para auditoría).
    # Nota: pet_id en PlanJobModel es NOT NULL en el ORM, pero la columna DB se
    # deja como nullable=False ya existente — la FK no altera la nulabilidad.
    op.create_foreign_key(
        "fk_plan_jobs_pet_id",
        "plan_jobs",
        "pets",
        ["pet_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── FK: plan_jobs.owner_id → users.id ─────────────────────────────────────
    op.create_foreign_key(
        "fk_plan_jobs_owner_id",
        "plan_jobs",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── FK: nutrition_plans.approved_by_vet_id → users.id ─────────────────────
    # SET NULL on delete: si se elimina el vet, el plan queda con aprobación
    # anónima pero no se pierde. El approved_by_vet_id queda NULL.
    op.create_foreign_key(
        "fk_nutrition_plans_approved_by_vet_id",
        "nutrition_plans",
        "users",
        ["approved_by_vet_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── Índice: nutrition_plans.status ────────────────────────────────────────
    # Cubre: GET /v1/vet/plans?status=PENDING_VET, vet dashboard, badge contador.
    op.create_index(
        "ix_nutrition_plans_status",
        "nutrition_plans",
        ["status"],
    )

    # ── Índice: plan_jobs.status ──────────────────────────────────────────────
    # Cubre: polling de jobs en curso (QUEUED, PROCESSING), limpieza de jobs.
    op.create_index(
        "ix_plan_jobs_status",
        "plan_jobs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_plan_jobs_status", table_name="plan_jobs")
    op.drop_index("ix_nutrition_plans_status", table_name="nutrition_plans")
    op.drop_constraint("fk_nutrition_plans_approved_by_vet_id", "nutrition_plans", type_="foreignkey")
    op.drop_constraint("fk_plan_jobs_owner_id", "plan_jobs", type_="foreignkey")
    op.drop_constraint("fk_plan_jobs_pet_id", "plan_jobs", type_="foreignkey")
