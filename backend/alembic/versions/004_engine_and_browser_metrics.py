"""Add test_run.engine and browser metrics to test_result.

Revision ID: 004_engine_browser
Revises: 003_request_args
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_engine_browser"
down_revision: Union[str, None] = "003_request_args"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_run",
        sa.Column("engine", sa.String(32), nullable=False, server_default="http"),
    )
    op.add_column(
        "test_result",
        sa.Column("lcp_ms", sa.Float(), nullable=True),
    )
    op.add_column(
        "test_result",
        sa.Column("fcp_ms", sa.Float(), nullable=True),
    )
    op.add_column(
        "test_result",
        sa.Column("cls", sa.Float(), nullable=True),
    )
    op.add_column(
        "test_result",
        sa.Column("ttfb_ms", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_result", "ttfb_ms")
    op.drop_column("test_result", "cls")
    op.drop_column("test_result", "fcp_ms")
    op.drop_column("test_result", "lcp_ms")
    op.drop_column("test_run", "engine")
