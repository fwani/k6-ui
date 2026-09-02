"""Add performance_test.tags (JSON array of tag strings)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014_performance_test_tags"
down_revision: Union[str, None] = "013_browser_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("tags", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("performance_test", "tags")
