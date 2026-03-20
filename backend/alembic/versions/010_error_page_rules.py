"""Add performance_test.error_page_rules (JSON array of pattern + matchMode)."""

from typing import Sequence, Union

import json

from alembic import op
import sqlalchemy as sa

revision: str = "010_error_page_rules"
down_revision: Union[str, None] = "009_http_scenario"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("performance_test", sa.Column("error_page_rules", sa.Text(), nullable=True))
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, error_page_pattern, error_page_match_mode FROM performance_test")).fetchall()

    for row in rows:
        rid, pat, mode = row[0], row[1], row[2] or "contains"
        if not pat or not str(pat).strip():
            continue
        m = (mode or "contains").strip()
        if m not in ("contains", "not_contains"):
            m = "contains"
        payload = json.dumps([{"pattern": str(pat).strip(), "matchMode": m}], ensure_ascii=False)
        conn.execute(
            sa.text("UPDATE performance_test SET error_page_rules = :p WHERE id = :id"),
            {"p": payload, "id": rid},
        )


def downgrade() -> None:
    op.drop_column("performance_test", "error_page_rules")
