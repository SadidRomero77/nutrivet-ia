"""agent_traces_immutability_trigger

Constitution REGLA 6: agent_traces son inmutables post-generación.
Agrega un trigger BEFORE UPDATE en la tabla agent_traces que lanza
una excepción si alguien intenta modificar una traza existente.

Esto complementa la restricción a nivel de aplicación (no hay método
update() en IAgentTraceRepository) con un guardarraíl a nivel de base
de datos que no puede ser bypaseado por acceso SQL directo.

Revision ID: b9c2e4f1a837
Revises: 1e222fb7b70d
Create Date: 2026-04-02

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'b9c2e4f1a837'
down_revision: Union[str, Sequence[str], None] = '1e222fb7b70d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crea función y trigger que bloquean cualquier UPDATE en agent_traces.

    La función lanza una excepción con mensaje claro para facilitar el diagnóstico.
    """
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_agent_trace_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'agent_traces son inmutables (Constitution REGLA 6). '
                'Para corregir una traza, insertar una nueva con referencia '
                'a la original en output_summary. trace_id=%', OLD.id;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_agent_traces_immutable
        BEFORE UPDATE ON agent_traces
        FOR EACH ROW
        EXECUTE FUNCTION prevent_agent_trace_update();
    """)


def downgrade() -> None:
    """Elimina trigger y función."""
    op.execute("DROP TRIGGER IF EXISTS trg_agent_traces_immutable ON agent_traces;")
    op.execute("DROP FUNCTION IF EXISTS prevent_agent_trace_update();")
