"""Move request_args from test_result to run_request_response.

Revision ID: 003_request_args
Revises: 002_vu_url_suffix
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_request_args"
down_revision: Union[str, None] = "002_vu_url_suffix"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "run_request_response",
        sa.Column("request_args", sa.Text(), nullable=True),
    )
    op.drop_column("test_result", "request_args")


def downgrade() -> None:
    op.add_column(
        "test_result",
        sa.Column("request_args", sa.Text(), nullable=True),
    )
    op.drop_column("run_request_response", "request_args")
