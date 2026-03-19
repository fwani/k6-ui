# Backend: Python 3.14 + uv, FastAPI/uvicorn, k6
FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# k6 binary (for load test from API)
COPY --from=grafana/k6:latest /usr/bin/k6 /usr/local/bin/k6

# Dependencies from pyproject.toml
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# Playwright Chromium (for browser/rendering runs)
RUN uv run playwright install chromium

# Application + Alembic
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY .python-version ./
COPY scripts/entrypoint.sh ./scripts/entrypoint.sh

ENV PYTHONPATH=/app
EXPOSE 8080
ENTRYPOINT ["/bin/sh", "./scripts/entrypoint.sh"]
