"""환경 설정. .env 로드 후 DATABASE_URL, GRAFANA_DASHBOARD_URL, INFLUXDB_URL 사용."""

import os
from pathlib import Path
from urllib.parse import urlparse

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
_GRAFANA_BROWSER_VITALS: str = _str_or_default("GRAFANA_BROWSER_VITALS_URL", "")


def _browser_vitals_url() -> str:
    if _GRAFANA_BROWSER_VITALS.strip():
        return _GRAFANA_BROWSER_VITALS.strip()
    base = GRAFANA_DASHBOARD_URL.strip().rstrip("/")
    if not base:
        return ""
    parsed = urlparse(base)
    path = "/d/browser-web-vitals/browser-web-vitals"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


GRAFANA_BROWSER_VITALS_URL: str = _browser_vitals_url()
INFLUXDB_URL: str = _str_or_default("INFLUXDB_URL", "http://influxdb:8086")
