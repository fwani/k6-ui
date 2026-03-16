"""Add performance_test.ramp_up, iterations (JMeter-style).

Revision ID: 003_ramp_iterations
Revises: 002_error_message
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_ramp_iterations"
down_revision: Union[str, None] = "002_error_message"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("ramp_up", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "performance_test",
        sa.Column("iterations", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "iterations")
    op.drop_column("performance_test", "ramp_up")
