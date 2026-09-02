"""Initial schema: performance_test, test_run, test_result, run_request_response.

Revision ID: 001_initial
Revises:
Create Date: 2026-03-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "performance_test",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("query_params", sa.Text(), nullable=True),
        sa.Column("http_method", sa.String(16), nullable=False),
        sa.Column("request_body", sa.Text(), nullable=True),
        sa.Column("headers", sa.Text(), nullable=True),
        sa.Column("vus", sa.Integer(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("request_delay", sa.Float(), nullable=True),
        sa.Column("ramp_up", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("iterations", sa.Integer(), nullable=True),
        sa.Column("body_preview_size", sa.Integer(), nullable=False, server_default=sa.text("500")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "test_run",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("test_id", sa.String(36), sa.ForeignKey("performance_test.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="Ready"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "test_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("test_run.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("avg_response_time", sa.Float(), nullable=False),
        sa.Column("max_response_time", sa.Float(), nullable=False),
        sa.Column("failure_rate", sa.Float(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("tps_or_rps", sa.Float(), nullable=False),
        sa.Column("execution_time", sa.Float(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("request_args", sa.Text(), nullable=True),
    )
    op.create_table(
        "run_request_response",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("test_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("run_request_response")
    op.drop_table("test_result")
    op.drop_table("test_run")
    op.drop_table("performance_test")
