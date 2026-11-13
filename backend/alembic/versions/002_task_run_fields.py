"""Add task, run and run_step fields for the mock agent.

Revision ID: 002
Revises: 001
Create Date: 2026-11-13 00:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # tasks
    op.add_column("tasks", sa.Column("expected_output", sa.Text(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column("difficulty", sa.String(), nullable=False, server_default="medium"),
    )

    # runs
    op.add_column(
        "runs",
        sa.Column(
            "agent_version", sa.String(), nullable=False, server_default="mock-v1"
        ),
    )
    op.add_column(
        "runs",
        sa.Column("total_cost", sa.Float(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "runs",
        sa.Column(
            "total_latency_ms", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )

    # run_steps
    op.add_column(
        "run_steps",
        sa.Column("step_type", sa.String(), nullable=False, server_default="thought"),
    )
    op.add_column("run_steps", sa.Column("content", sa.Text(), nullable=True))
    op.add_column(
        "run_steps",
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "run_steps",
        sa.Column("tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("run_steps", "tokens")
    op.drop_column("run_steps", "latency_ms")
    op.drop_column("run_steps", "content")
    op.drop_column("run_steps", "step_type")
    op.drop_column("runs", "total_latency_ms")
    op.drop_column("runs", "total_cost")
    op.drop_column("runs", "agent_version")
    op.drop_column("tasks", "difficulty")
    op.drop_column("tasks", "expected_output")