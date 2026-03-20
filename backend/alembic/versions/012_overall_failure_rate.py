"""Add test_result.overall_failure_rate (HTTP 비-2xx 또는 판별 failed 비율)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012_overall_failure_rate"
down_revision: Union[str, None] = "011_vu_start"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_result",
        sa.Column("overall_failure_rate", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("test_result", "overall_failure_rate")
