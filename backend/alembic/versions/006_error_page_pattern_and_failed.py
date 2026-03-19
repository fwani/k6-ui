"""Add performance_test.error_page_pattern, run_request_response.failed.

Revision ID: 006_error_failed
Revises: 005_screenshot
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006_error_failed"
down_revision: Union[str, None] = "005_screenshot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("error_page_pattern", sa.Text(), nullable=True),
    )
    op.add_column(
        "run_request_response",
        sa.Column("failed", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("run_request_response", "failed")
    op.drop_column("performance_test", "error_page_pattern")
