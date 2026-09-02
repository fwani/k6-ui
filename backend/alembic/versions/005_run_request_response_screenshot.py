"""Add run_request_response.screenshot (PNG BLOB).

Revision ID: 005_screenshot
Revises: 004_engine_browser
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_screenshot"
down_revision: Union[str, None] = "004_engine_browser"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "run_request_response",
        sa.Column("screenshot", sa.LargeBinary(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("run_request_response", "screenshot")
