#!/bin/sh
set -e
cd "$(dirname "$0")/.."
uv run alembic upgrade head
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 "$@" --reload
