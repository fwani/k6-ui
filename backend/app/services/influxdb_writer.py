"""InfluxDB 1.x에 메트릭 전송. 브라우저 Run Web Vitals 등."""

import logging
import httpx

logger = logging.getLogger(__name__)


def _escape_tag(v: str) -> str:
    """Line protocol: tag 값에 쉼표/공백/등호 있으면 이스케이프."""
    s = str(v).replace("\\", "\\\\").replace(",", "\\,").replace(" ", "\\ ").replace("=", "\\=")
    return s


def write_browser_vitals(
    influx_url: str,
    run_id: str,
    test_id: str,
    summary: dict,
    timestamp_ns: int,
    db: str = "k6",
) -> bool:
    """브라우저 Run Web Vitals를 InfluxDB 1.x에 line protocol로 기록. 성공 시 True."""
    base = (influx_url or "").strip().rstrip("/")
    if not base:
        return False
    run_tag = _escape_tag(run_id)
    test_tag = _escape_tag(test_id)
    parts = [f"browser_vitals,run_id={run_tag},test_id={test_tag}"]
    fields = []
    if summary.get("lcp_ms") is not None:
        fields.append(f"lcp_ms={float(summary['lcp_ms'])}")
    if summary.get("fcp_ms") is not None:
        fields.append(f"fcp_ms={float(summary['fcp_ms'])}")
    if summary.get("ttfb_ms") is not None:
        fields.append(f"ttfb_ms={float(summary['ttfb_ms'])}")
    if summary.get("cls") is not None:
        fields.append(f"cls={float(summary['cls'])}")
    if not fields:
        return False
    # Line protocol: 필드 구분은 쉼표, tag set과 field set 구분은 공백
    parts.append(",".join(fields))
    parts.append(str(timestamp_ns))
    line = " ".join(parts)
    url = f"{base}/write?db={db}&precision=ns"
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.post(url, content=line.encode("utf-8"), headers=headers)
            if r.status_code in (200, 204):
                logger.info("influxdb write browser_vitals ok run_id=%s", run_id)
                return True
            logger.warning(
                "influxdb write browser_vitals status=%s body=%s",
                r.status_code,
                (r.text or "")[:200],
            )
    except Exception as e:
        logger.exception("influxdb write browser_vitals failed: %s", e)
    return False


def write_browser_vitals_batch(
    influx_url: str,
    run_id: str,
    test_id: str,
    points: list[tuple[dict, int]],
    db: str = "k6",
) -> bool:
    """여러 시점의 browser_vitals를 한 번에 전송. points = [(summary, timestamp_ns), ...]. 성공 시 True."""
    base = (influx_url or "").strip().rstrip("/")
    if not base or not points:
        return False
    run_tag = _escape_tag(run_id)
    test_tag = _escape_tag(test_id)
    lines = []
    for summary, timestamp_ns in points:
        fields = []
        if summary.get("lcp_ms") is not None:
            fields.append(f"lcp_ms={float(summary['lcp_ms'])}")
        if summary.get("fcp_ms") is not None:
            fields.append(f"fcp_ms={float(summary['fcp_ms'])}")
        if summary.get("ttfb_ms") is not None:
            fields.append(f"ttfb_ms={float(summary['ttfb_ms'])}")
        if summary.get("cls") is not None:
            fields.append(f"cls={float(summary['cls'])}")
        if not fields:
            continue
        line = f"browser_vitals,run_id={run_tag},test_id={test_tag} " + ",".join(fields) + " " + str(timestamp_ns)
        lines.append(line)
    if not lines:
        return False
    body = "\n".join(lines).encode("utf-8")
    url = f"{base}/write?db={db}&precision=ns"
    headers = {"Content-Type": "text/plain; charset=utf-8"}
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.post(url, content=body, headers=headers)
            if r.status_code in (200, 204):
                logger.info("influxdb write browser_vitals_batch ok run_id=%s points=%s", run_id, len(lines))
                return True
            logger.warning(
                "influxdb write browser_vitals_batch status=%s body=%s",
                r.status_code,
                (r.text or "")[:200],
            )
    except Exception as e:
        logger.exception("influxdb write browser_vitals_batch failed: %s", e)
    return False
