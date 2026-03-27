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

# k6 multipart용 업로드 파일 저장 디렉터리(API·k6 동일 호스트에서 읽을 수 있어야 함). Docker: /app/data/k6_fixtures 권장.
_default_fixture = _env_dir / "data" / "k6_fixtures"
K6_FIXTURE_DIR: Path = Path(
    _str_or_default("GRAPHIO_K6_FIXTURE_DIR", str(_default_fixture))
).expanduser().resolve()


def _env_truthy(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None or not str(raw).strip():
        return default
    v = str(raw).strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    return default


# 브라우저(Playwright) 기본: 헤드리스. GRAPHIO_BROWSER_HEADLESS=0 이면 창 표시(로컬·DISPLAY 필요).
BROWSER_HEADLESS: bool = _env_truthy("GRAPHIO_BROWSER_HEADLESS", True)
