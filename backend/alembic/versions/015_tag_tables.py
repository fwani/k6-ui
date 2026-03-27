"""Normalize tags: tag + performance_test_tag tables; migrate from performance_test.tags JSON."""

from __future__ import annotations

import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "015_tag_tables"
down_revision: Union[str, None] = "014_performance_test_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _normalize_one(s: object) -> str | None:
    t = str(s or "").strip()[:32]
    return t if t else None


def upgrade() -> None:
    bind = op.get_bind()
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "performance_test_tag",
        sa.Column("test_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_id"], ["performance_test.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("test_id", "tag_id"),
    )

    def get_or_create_tag_id(name: str) -> int:
        row = bind.execute(text("SELECT id FROM tag WHERE name = :n"), {"n": name}).fetchone()
        if row:
            return int(row[0])
        bind.execute(text("INSERT INTO tag (name) VALUES (:n)"), {"n": name})
        row2 = bind.execute(text("SELECT id FROM tag WHERE name = :n"), {"n": name}).fetchone()
        assert row2 is not None
        return int(row2[0])

    rows = bind.execute(text("SELECT id, tags FROM performance_test")).fetchall()
    for test_id, tags_str in rows:
        if not tags_str or not str(tags_str).strip():
            continue
        try:
            arr = json.loads(tags_str)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(arr, list):
            continue
        seen: set[str] = set()
        for item in arr:
            nm = _normalize_one(item)
            if not nm or nm in seen:
                continue
            seen.add(nm)
            tid = get_or_create_tag_id(nm)
            bind.execute(
                text(
                    "INSERT OR IGNORE INTO performance_test_tag (test_id, tag_id) "
                    "VALUES (:tid, :gid)"
                ),
                {"tid": test_id, "gid": tid},
            )

    op.drop_column("performance_test", "tags")


def downgrade() -> None:
    op.add_column(
        "performance_test",
        sa.Column("tags", sa.Text(), nullable=True),
    )
    bind = op.get_bind()
    rows = bind.execute(
        text(
            "SELECT pt.id, GROUP_CONCAT(t.name) AS names "
            "FROM performance_test pt "
            "LEFT JOIN performance_test_tag ptt ON ptt.test_id = pt.id "
            "LEFT JOIN tag t ON t.id = ptt.tag_id "
            "GROUP BY pt.id"
        )
    ).fetchall()
    for test_id, names in rows:
        if not names:
            continue
        tag_list = [x.strip() for x in str(names).split(",") if x.strip()]
        bind.execute(
            text("UPDATE performance_test SET tags = :j WHERE id = :id"),
            {"j": json.dumps(tag_list), "id": test_id},
        )
    op.drop_table("performance_test_tag")
    op.drop_table("tag")
