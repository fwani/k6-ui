"""k6 부하 테스트 실행. 스크립트 동적 생성, subprocess 실행. MVP: 동시 1건."""

import json
import logging
import subprocess
import threading
from urllib.parse import quote

logger = logging.getLogger(__name__)

from app.models.db import PerformanceTest


class K6NotFoundError(Exception):
    """k6가 PATH에 없거나 설치되지 않음."""

_processes: dict[str, subprocess.Popen] = {}
_processes_lock = threading.Lock()


def _parse_headers(headers: str | None) -> dict[str, str]:
    if not headers or not headers.strip():
        return {}
    try:
        d = json.loads(headers)
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _build_url_with_params(base: str, query_params: str | None) -> str:
    """base URL + query_params(JSON array [{"key":"k","value":"v"},...]) → 최종 요청 URL."""
    base = (base or "").strip() or "https://httpbin.org/get"
    if not query_params or not query_params.strip():
        return base
    try:
        arr = json.loads(query_params)
        if not isinstance(arr, list) or not arr:
            return base
        pairs = []
        for item in arr:
            if not isinstance(item, dict):
                continue
            k = item.get("key") if hasattr(item, "get") else (item.get("key") if isinstance(item, dict) else None)
            v = item.get("value") if hasattr(item, "get") else (item.get("value") if isinstance(item, dict) else "")
            if k is None:
                continue
            k = str(k).strip()
            if not k:
                continue
            v = "" if v is None else str(v).strip()
            pairs.append(f"{quote(k, safe='')}={quote(v, safe='')}")
        if not pairs:
            return base
        qs = "&".join(pairs)
        return base + ("&" if "?" in base else "?") + qs
    except (json.JSONDecodeError, TypeError, ValueError):
        return base


def generate_script(test: PerformanceTest) -> str:
    """테스트 파라미터로 k6 JS 스크립트 생성. handleSummary는 stdout으로 JSON 출력."""
    method = (getattr(test, "http_method", None) or "GET").upper()
    base_url = (getattr(test, "target_url", None) or "").strip() or "https://httpbin.org/get"
    query_params = getattr(test, "query_params", None)
    url = _build_url_with_params(base_url, query_params)
    body = getattr(test, "request_body", None) or ""
    if body is not None:
        body = str(body).strip()
    else:
        body = ""
    headers = _parse_headers(getattr(test, "headers", None))
    if "Content-Type" not in headers and method in ("POST", "PUT", "PATCH"):
        headers["Content-Type"] = "application/json"
    vus = max(1, int(getattr(test, "vus", 1) or 1))
    duration_s = max(1, int(getattr(test, "duration", 10) or 10))
    ramp_up = max(0, int(getattr(test, "ramp_up", 0) or 0))
    iterations = getattr(test, "iterations", None)
    if iterations is not None:
        iterations = max(1, int(iterations))
    rd = getattr(test, "request_delay", None)
    sleep_s = float(rd) if rd is not None and float(rd) >= 0 else 1

    headers_js = json.dumps(headers) if headers else "{}"
    body_arg = f", {json.dumps(body)}" if body else ""
    body_headers = f", {{ headers: {headers_js} }}" if headers else ""

    # k6 http module: get(url), post(url, body, opts), etc.
    if method == "GET":
        call = f"http.get({json.dumps(url)}{body_headers})"
    elif method == "POST":
        call = f"http.post({json.dumps(url)}{body_arg}{body_headers})"
    elif method == "PUT":
        call = f"http.put({json.dumps(url)}{body_arg}{body_headers})"
    elif method == "DELETE":
        call = f"http.del({json.dumps(url)}{body_headers})"
    else:
        call = f"http.request({json.dumps(method)}, {json.dumps(url)}{body_arg}{body_headers})"

    # JMeter-style: iterations = total iterations (duration 대신); rampUp = duration 모드에서만 stages 사용
    if iterations is not None:
        options_js = f"  vus: {vus},\n  iterations: {iterations},\n"
    elif ramp_up > 0:
        options_js = f"""  stages: [
    {{ duration: '{ramp_up}s', target: {vus} }},
    {{ duration: '{duration_s}s', target: {vus} }},
  ],
"""
    else:
        options_js = f"  vus: {vus},\n  duration: '{duration_s}s',\n"

    # handleSummary: stdout으로 JSON 출력 → 파일 경로 의존 없이 communicate()에서 파싱
    script = f"""import http from 'k6/http';
import {{ sleep }} from 'k6';

export const options = {{
{options_js}}};

export default function () {{
  {call};
  sleep({sleep_s});
}}

const SUMMARY_MARKER = '__K6_SUMMARY_JSON__';
const SUMMARY_END = '__K6_SUMMARY_END__';
export function handleSummary(data) {{
  return {{ stdout: SUMMARY_MARKER + JSON.stringify(data) + SUMMARY_END }};
}}
"""
    return script


def _metric_val(m: dict, key: str, default: float = 0) -> float:
    """metrics 항목에서 값 추출. m.KEY 또는 m.values.KEY 지원 (k6 버전 차이)."""
    if not m:
        return default
    v = m.get(key)
    if v is not None:
        return float(v)
    vals = m.get("values") or m.get("value")
    if isinstance(vals, dict) and key in vals:
        return float(vals[key])
    return default


def _parse_k6_summary(data: dict) -> dict | None:
    """k6 handleSummary JSON에서 Result 필드 추출. 실패 시 None."""
    try:
        metrics = data.get("metrics") or {}
        hr_duration = metrics.get("http_req_duration") or {}
        hr_failed = metrics.get("http_req_failed") or {}
        hr_reqs = metrics.get("http_reqs") or {}
        avg_ms = _metric_val(hr_duration, "avg")
        max_ms = _metric_val(hr_duration, "max")
        rate = _metric_val(hr_failed, "rate")
        count = int(_metric_val(hr_reqs, "count"))
        req_rate = _metric_val(hr_reqs, "rate")
        exec_s = count / req_rate if req_rate > 0 else 0.0
        return {
            "avg_response_time": avg_ms,
            "max_response_time": max_ms,
            "failure_rate": rate,
            "request_count": count,
            "tps_or_rps": req_rate,
            "execution_time": exec_s,
        }
    except (TypeError, ValueError, KeyError):
        return None


_SUMMARY_MARKER = b"__K6_SUMMARY_JSON__"
_SUMMARY_END = b"__K6_SUMMARY_END__"


def start(
    run_id: str,
    test: PerformanceTest,
    on_complete: Callable[[str, int, dict | None, str | None], None] | None = None,
) -> None:
    """백그라운드에서 k6 실행. 스크립트는 stdin으로 전달(k6 run -). 요약은 stdout에서 파싱."""
    script = generate_script(test)

    with _processes_lock:
        if run_id in _processes:
            return
        try:
            proc = subprocess.Popen(
                ["k6", "run", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            raise K6NotFoundError(
                "k6가 설치되어 있지 않거나 PATH에 없습니다. "
                "로컬에서는 k6를 설치하거나 Docker로 API를 실행하세요."
            )
        _processes[run_id] = proc

    # 테스트 duration + 여유(정리·요약) 초, 최대 2시간
    run_timeout = min(
        max(int(test.duration or 60) + 60, 120),
        7200,
    )

    def wait_and_cleanup():
        script_bytes = script.encode("utf-8")
        exit_code = -1
        summary = None
        error_output = None
        try:
            stdout_bytes, stderr_bytes = proc.communicate(input=script_bytes, timeout=run_timeout)
            exit_code = proc.returncode if proc.returncode is not None else -1
            if stderr_bytes:
                try:
                    error_output = stderr_bytes.decode("utf-8", errors="replace").strip() or None
                except (OSError, UnicodeDecodeError):
                    pass
            if stdout_bytes and _SUMMARY_MARKER in stdout_bytes and _SUMMARY_END in stdout_bytes:
                try:
                    start_i = stdout_bytes.index(_SUMMARY_MARKER) + len(_SUMMARY_MARKER)
                    end_i = stdout_bytes.index(_SUMMARY_END)
                    json_str = stdout_bytes[start_i:end_i].decode("utf-8", errors="replace")
                    summary = _parse_k6_summary(json.loads(json_str))
                except (ValueError, json.JSONDecodeError, TypeError, KeyError):
                    pass
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                _, stderr_bytes = proc.communicate()
                stderr_bytes = (stderr_bytes or b"") + "\n(프로세스 타임아웃으로 종료)".encode("utf-8")
                error_output = stderr_bytes.decode("utf-8", errors="replace").strip()
            except Exception:
                error_output = "프로세스 타임아웃으로 종료"
            exit_code = -9
        except (OSError, BrokenPipeError):
            exit_code = -1
            error_output = "스크립트 전달 실패"
        finally:
            with _processes_lock:
                _processes.pop(run_id, None)
            if on_complete:
                try:
                    on_complete(run_id, exit_code, summary, error_output)
                except Exception as e:
                    logger.exception("on_run_complete callback failed: %s", e)

    t = threading.Thread(target=wait_and_cleanup, daemon=True)
    t.start()


def stop(run_id: str) -> bool:
    """실행 중인 k6 프로세스 중지. 있으면 True."""
    with _processes_lock:
        proc = _processes.get(run_id)
        if not proc or proc.poll() is not None:
            return False
        proc.terminate()
        _processes.pop(run_id, None)
    return True


def is_running(run_id: str) -> bool:
    with _processes_lock:
        proc = _processes.get(run_id)
        return proc is not None and proc.poll() is None
