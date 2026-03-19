"""Add performance_test.error_page_match_mode (contains | not_contains).

Revision ID: 007_match_mode
Revises: 006_error_failed
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_match_mode"
down_revision: Union[str, None] = "006_error_failed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("error_page_match_mode", sa.String(32), nullable=False, server_default="contains"),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "error_page_match_mode")
