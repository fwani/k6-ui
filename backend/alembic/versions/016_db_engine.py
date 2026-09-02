"""Add performance_test.db_driver, db_query for the DB query engine (k6 + xk6-sql).

DSN(연결 문자열)은 기존 target_url 컬럼을 재사용한다.

Revision ID: 016_db_engine
Revises: 015_tag_tables
Create Date: 2026-06-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016_db_engine"
down_revision: Union[str, None] = "015_tag_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("performance_test", sa.Column("db_driver", sa.String(length=32), nullable=True))
    op.add_column("performance_test", sa.Column("db_query", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("performance_test", "db_query")
    op.drop_column("performance_test", "db_driver")
