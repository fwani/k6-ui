"""Add performance_test.browser_actions (JSON text, Playwright post-load steps)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013_browser_actions"
down_revision: Union[str, None] = "012_overall_failure_rate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("browser_actions", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "browser_actions")
