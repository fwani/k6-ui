"""환경 설정. .env 로드 후 DATABASE_URL, GRAFANA_DASHBOARD_URL, INFLUXDB_URL 사용."""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ 또는 프로젝트 루트의 .env 로드 (config.py 기준 backend/app/.env, backend/.env)
_env_dir = Path(__file__).resolve().parent.parent
load_dotenv(_env_dir / ".env")
load_dotenv(_env_dir.parent / ".env")


def _str_or_default(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


DATABASE_URL: str = _str_or_default(
    "DATABASE_URL",
    "sqlite:///./app.db",
)
GRAFANA_DASHBOARD_URL: str = _str_or_default("GRAFANA_DASHBOARD_URL", "")
INFLUXDB_URL: str = _str_or_default("INFLUXDB_URL", "http://influxdb:8086")
