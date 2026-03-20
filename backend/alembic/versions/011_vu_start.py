"""Add performance_test.vu_start (first number for {{VU}} placeholder)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011_vu_start"
down_revision: Union[str, None] = "010_error_page_rules"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("vu_start", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "vu_start")
