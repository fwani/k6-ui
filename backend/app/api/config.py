"""설정 API: GET /config (Grafana 대시보드 URL 등)."""

from fastapi import APIRouter

from app.config import GRAFANA_BROWSER_VITALS_URL, GRAFANA_DASHBOARD_URL

router = APIRouter(tags=["config"])


@router.get("/config")
def get_config() -> dict:
    """GET /config. UI에 표시할 Grafana 대시보드 URL 등."""
    return {
        "grafanaDashboardUrl": GRAFANA_DASHBOARD_URL,
        "grafanaBrowserVitalsUrl": GRAFANA_BROWSER_VITALS_URL,
    }
