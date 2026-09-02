# Stage 1: build a custom k6 binary with the xk6-sql extension (+ PostgreSQL driver)
# so the API can run DB query load tests (engine="db") in addition to HTTP/browser.
FROM golang:1.25-bookworm AS k6build
RUN go install go.k6.io/xk6/cmd/xk6@latest
RUN xk6 build \
    --with github.com/grafana/xk6-sql@latest \
    --with github.com/grafana/xk6-sql-driver-postgres@latest \
    --output /k6

# Backend: Python 3.14 + uv, FastAPI/uvicorn, k6
FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Custom k6 binary with xk6-sql (HTTP load test + DB query test from API)
COPY --from=k6build /k6 /usr/local/bin/k6

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
