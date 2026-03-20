"""Add performance_test.http_scenario (JSON text, multi-step k6).

Revision ID: 009_http_scenario
Revises: 008_test_engine
Create Date: 2026-03-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009_http_scenario"
down_revision: Union[str, None] = "008_test_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("performance_test", sa.Column("http_scenario", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("performance_test", "http_scenario")
