"""Add performance_test.engine (http | browser).

Revision ID: 008_test_engine
Revises: 007_match_mode
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008_test_engine"
down_revision: Union[str, None] = "007_match_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("engine", sa.String(32), nullable=False, server_default="http"),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "engine")
