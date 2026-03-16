"""Add performance_test.query_params for request query string.

Revision ID: 004_query_params
Revises: 003_ramp_iterations
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_query_params"
down_revision: Union[str, None] = "003_ramp_iterations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("query_params", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "query_params")
