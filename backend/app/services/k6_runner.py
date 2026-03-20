"""k6 부하 테스트 실행. 스크립트 동적 생성, subprocess 실행. MVP: 동시 1건."""

import json
import logging
import re
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urlparse, urlunparse

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_JINJA_ENV = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=False)
_K6_SCRIPT_TEMPLATE = _JINJA_ENV.get_template("k6_script.tpl")
_K6_SCENARIO_TEMPLATE = _JINJA_ENV.get_template("k6_scenario_script.tpl")

VU_PLACEHOLDER = "{{VU}}"

from app.config import INFLUXDB_URL
from app.models.db import PerformanceTest
from app.services.error_page_rules import parse_error_rules_from_test


class K6NotFoundError(Exception):
    """k6가 PATH에 없거나 설치되지 않음."""

_processes: dict[str, subprocess.Popen] = {}
_processes_lock = threading.Lock()

_log_buffers: dict[str, list[str]] = {}
_log_lock = threading.Lock()
_MAX_LOG_LINES = 5000


def _parse_headers(headers: str | None) -> dict[str, str]:
    if not headers or not headers.strip():
        return {}
    try:
        d = json.loads(headers)
        return {str(k): str(v) for k, v in d.items()} if isinstance(d, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _normalize_run_header_overrides(overrides: dict[str, str] | None) -> dict[str, str]:
    if not overrides:
        return {}
    out: dict[str, str] = {}
    for k, v in overrides.items():
        key = str(k).strip()
        if not key:
            continue
        out[key] = "" if v is None else str(v)
    return out


def _merge_http_headers(base: dict[str, str], overrides: dict[str, str]) -> dict[str, str]:
    """테스트 정의 헤더 + 실행 시 헤더. 동일 키는 overrides 우선."""
    if not overrides:
        return dict(base)
    merged = dict(base)
    merged.update(overrides)
    return merged


def _contains_vu_placeholder(s: str) -> bool:
    """문자열에 {{VU}} 플레이스홀더가 포함되어 있는지."""
    return s is not None and VU_PLACEHOLDER in str(s)


def _url_with_vu_suffix(base: str) -> str:
    """base URL의 path 끝에 {{VU}}를 붙인 URL 반환. 쿼리/프래그먼트는 유지."""
    base = (base or "").strip()
    if not base:
        return base
    parsed = urlparse(base)
    path = parsed.path + VU_PLACEHOLDER
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))


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


def _vu_start_from_test(test: PerformanceTest) -> int:
    """{{VU}}에 쓰는 첫 VU 값 (__VU==1일 때)."""
    try:
        n = int(getattr(test, "vu_start", 1) or 1)
    except (TypeError, ValueError):
        return 1
    return max(1, n)


def _replace_vu_placeholder(s: str, vu: str = "1") -> str:
    """문자열 내 {{VU}}를 주어진 값으로 치환. per-VU 결과 저장 시 대표값용."""
    if s is None:
        return ""
    return str(s).replace(VU_PLACEHOLDER, vu)


def _load_scenario_steps(test: PerformanceTest) -> list | None:
    """http_scenario JSON 배열 파싱. 비어 있거나 없으면 None."""
    raw = getattr(test, "http_scenario", None)
    if not raw or not str(raw).strip():
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, list) or len(data) == 0:
            return None
        return data
    except (json.JSONDecodeError, TypeError):
        return None


def _parse_step_query_params(raw_qp: object) -> list:
    if raw_qp is None:
        return []
    if isinstance(raw_qp, list):
        return raw_qp
    if isinstance(raw_qp, str) and raw_qp.strip():
        try:
            arr = json.loads(raw_qp)
            return arr if isinstance(arr, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def _steps_payload_need_per_vu(steps_payload: list[dict]) -> bool:
    for s in steps_payload:
        if _contains_vu_placeholder(s.get("urlTemplate")):
            return True
        if _contains_vu_placeholder(s.get("bodyTemplate")):
            return True
        for v in (s.get("headers") or {}).values():
            if _contains_vu_placeholder(str(v)):
                return True
        for item in s.get("queryParams") or []:
            if isinstance(item, dict) and _contains_vu_placeholder(str(item.get("value", ""))):
                return True
    return False


def _build_k6_scenario_step_payloads(test: PerformanceTest) -> tuple[list[dict], bool] | None:
    """시나리오가 있으면 k6 STEPS 배열과 per-VU 필요 여부. 없으면 None."""
    raw_list = _load_scenario_steps(test)
    if not raw_list:
        return None
    vu_suf = bool(getattr(test, "vu_url_suffix", False))
    out: list[dict] = []
    for i, raw in enumerate(raw_list):
        if not isinstance(raw, dict):
            continue
        url = (raw.get("url") or "").strip()
        if not url:
            continue
        if vu_suf and VU_PLACEHOLDER not in url:
            url = _url_with_vu_suffix(url)
        method = (raw.get("method") or "GET").upper()
        qp = _parse_step_query_params(raw.get("queryParams"))
        if not qp:
            qp = _parse_step_query_params(raw.get("query_params"))
        headers = raw.get("headers")
        if not isinstance(headers, dict):
            headers = {}
        headers = {str(k): "" if v is None else str(v) for k, v in headers.items()}
        body = raw.get("body")
        body = "" if body is None else str(body)
        name = raw.get("name")
        name = f"step_{i + 1}" if not (name and str(name).strip()) else str(name).strip()
        cap_raw = raw.get("capture")
        capture = None
        if isinstance(cap_raw, dict) and cap_raw.get("var"):
            v_cap = str(cap_raw["var"]).strip()
            if v_cap:
                src = (cap_raw.get("from") or "json").strip().lower()
                if src == "header":
                    hn = cap_raw.get("header")
                    if hn and str(hn).strip():
                        capture = {
                            "from": "header",
                            "header": str(hn).strip(),
                            "var": v_cap,
                        }
                        cn = cap_raw.get("cookieName") or cap_raw.get("cookie_name")
                        if cn and str(cn).strip():
                            capture["cookieName"] = str(cn).strip()
                elif cap_raw.get("path") and str(cap_raw.get("path")).strip():
                    capture = {
                        "from": "json",
                        "path": str(cap_raw["path"]).strip(),
                        "var": v_cap,
                    }
        entry: dict = {
            "name": name,
            "method": method,
            "urlTemplate": url,
            "queryParams": qp,
            "headers": headers,
            "bodyTemplate": body,
            "capture": capture,
        }
        sas = raw.get("sleepAfterSeconds")
        if sas is None:
            sas = raw.get("sleep_after_seconds")
        if sas is not None:
            try:
                sf = float(sas)
                if 0 < sf <= 600:
                    entry["sleepAfterSeconds"] = sf
            except (TypeError, ValueError):
                pass
        out.append(entry)
    if not out:
        return None
    per_vu = _steps_payload_need_per_vu(out)
    return out, per_vu


def _build_options_js(test: PerformanceTest) -> str:
    vus = max(1, int(getattr(test, "vus", 1) or 1))
    duration_s = max(1, int(getattr(test, "duration", 10) or 10))
    ramp_up = max(0, int(getattr(test, "ramp_up", 0) or 0))
    iterations = getattr(test, "iterations", None)
    if iterations is not None:
        iterations = max(1, int(iterations))
        total_iterations = iterations * vus
        return f"  vus: {vus},\n  iterations: {total_iterations},\n"
    if ramp_up > 0:
        return f"""  stages: [
    {{ duration: '{ramp_up}s', target: {vus} }},
    {{ duration: '{duration_s}s', target: {vus} }},
  ],
"""
    return f"  vus: {vus},\n  duration: '{duration_s}s',\n"


def _render_scenario_script(
    test: PerformanceTest,
    steps_payload: list[dict],
    *,
    options_js: str,
    sleep_s: float,
    error_rules_js: str | None,
) -> str:
    steps_json = json.dumps(steps_payload, ensure_ascii=False)
    vu_offset = _vu_start_from_test(test) - 1
    ctx = {
        "steps_json": steps_json,
        "options_js": options_js,
        "placeholder_js": json.dumps(VU_PLACEHOLDER),
        "sleep_s": sleep_s,
        "error_rules_js": error_rules_js,
        "vu_offset": vu_offset,
    }
    return _K6_SCENARIO_TEMPLATE.render(**ctx)


def get_request_args_json(test: PerformanceTest) -> str | None:
    """테스트에서 요청 인자(url, method, headers, body)를 JSON 문자열로 반환. 결과 저장용. per-VU일 때는 {{VU}}→vu_start 대표값."""
    try:
        vu_rep = str(_vu_start_from_test(test))
        built = _build_k6_scenario_step_payloads(test)
        if built:
            steps, per_vu = built
            s0 = steps[0]
            method = s0["method"]
            qp_json = json.dumps(s0.get("queryParams") or []) if s0.get("queryParams") else None
            url = _build_url_with_params(s0["urlTemplate"], qp_json)
            if per_vu:
                url = _replace_vu_placeholder(url, vu_rep)
            body = s0["bodyTemplate"]
            if per_vu:
                body = _replace_vu_placeholder(body, vu_rep)
            headers = dict(s0["headers"])
            if per_vu:
                headers = {k: _replace_vu_placeholder(v, vu_rep) for k, v in headers.items()}
            return json.dumps(
                {"url": url, "method": method, "headers": headers, "body": body},
                ensure_ascii=False,
            )
        method = (getattr(test, "http_method", None) or "GET").upper()
        base_url = (getattr(test, "target_url", None) or "").strip() or "https://httpbin.org/get"
        query_params = getattr(test, "query_params", None)
        vu_url_suffix = bool(getattr(test, "vu_url_suffix", False))
        if vu_url_suffix and VU_PLACEHOLDER not in base_url:
            base_url = _url_with_vu_suffix(base_url)
        url = _build_url_with_params(base_url, query_params)
        if _needs_per_vu(test):
            url = _replace_vu_placeholder(url, vu_rep)
        body = getattr(test, "request_body", None) or ""
        if body is not None:
            body = str(body).strip()
        else:
            body = ""
        if _needs_per_vu(test):
            body = _replace_vu_placeholder(body, vu_rep)
        headers = _parse_headers(getattr(test, "headers", None))
        if _needs_per_vu(test):
            headers = {k: _replace_vu_placeholder(v, vu_rep) for k, v in headers.items()}
        return json.dumps(
            {"url": url, "method": method, "headers": headers, "body": body},
            ensure_ascii=False,
        )
    except (TypeError, ValueError):
        return None


def _needs_per_vu(test: PerformanceTest) -> bool:
    """테스트가 VU별 변형({{VU}} 또는 vu_url_suffix)을 사용하는지."""
    built = _build_k6_scenario_step_payloads(test)
    if built is not None:
        _, per_vu = built
        return per_vu
    if getattr(test, "vu_url_suffix", False):
        return True
    base_url = (getattr(test, "target_url", None) or "").strip()
    if _contains_vu_placeholder(base_url):
        return True
    query_params = getattr(test, "query_params", None)
    if query_params:
        try:
            arr = json.loads(query_params)
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict) and _contains_vu_placeholder(item.get("value")):
                        return True
        except (json.JSONDecodeError, TypeError):
            pass
    headers = _parse_headers(getattr(test, "headers", None))
    for v in headers.values():
        if _contains_vu_placeholder(v):
            return True
    body = getattr(test, "request_body", None) or ""
    if _contains_vu_placeholder(body):
        return True
    return False


def generate_script(
    test: PerformanceTest,
    request_header_overrides: dict[str, str] | None = None,
) -> str:
    """테스트 파라미터로 k6 JS 스크립트 생성. handleSummary는 stdout으로 JSON 출력."""
    rd = getattr(test, "request_delay", None)
    sleep_s = float(rd) if rd is not None and float(rd) >= 0 else 1
    rules = parse_error_rules_from_test(test)
    error_rules_js = json.dumps(rules, ensure_ascii=False) if rules else None
    options_js = _build_options_js(test)
    hdr_ov = _normalize_run_header_overrides(request_header_overrides)

    scenario = _build_k6_scenario_step_payloads(test)
    if scenario:
        steps_payload, _ = scenario
        if hdr_ov:
            steps_payload = [
                {
                    **step,
                    "headers": _merge_http_headers(step.get("headers") or {}, hdr_ov),
                }
                for step in steps_payload
            ]
        return _render_scenario_script(
            test,
            steps_payload,
            options_js=options_js,
            sleep_s=sleep_s,
            error_rules_js=error_rules_js,
        )

    method = (getattr(test, "http_method", None) or "GET").upper()
    base_url = (getattr(test, "target_url", None) or "").strip() or "https://httpbin.org/get"
    query_params = getattr(test, "query_params", None)
    body_raw = getattr(test, "request_body", None) or ""
    body = str(body_raw).strip() if body_raw is not None else ""
    headers = _parse_headers(getattr(test, "headers", None))
    if "Content-Type" not in headers and method in ("POST", "PUT", "PATCH"):
        headers["Content-Type"] = "application/json"
    if hdr_ov:
        headers = _merge_http_headers(headers, hdr_ov)
    vu_url_suffix = bool(getattr(test, "vu_url_suffix", False))

    per_vu = _needs_per_vu(test)
    if per_vu:
        # URL 템플릿: vu_url_suffix면 path 끝에 {{VU}} 붙이기, 아니면 base_url 그대로(이미 {{VU}} 있을 수 있음)
        base_url_template = base_url
        if vu_url_suffix and VU_PLACEHOLDER not in base_url:
            base_url_template = _url_with_vu_suffix(base_url)
        url_template = _build_url_with_params(base_url_template, query_params)
        url_template_js = json.dumps(url_template)
        headers_js = json.dumps(headers) if headers else "{}"
        body_template_js = json.dumps(body)
        method_js = json.dumps(method)
        # default function 안에서 __VU + 오프셋으로 치환 후 요청
        placeholder_js = json.dumps(VU_PLACEHOLDER)
        vu_off = _vu_start_from_test(test) - 1
        call_js = f"""  const vu = __VU + {vu_off};
  const replaceVu = (s) => (s == null ? '' : String(s).split({placeholder_js}).join(vu));
  const url = replaceVu(URL_TEMPLATE);
  const headersObj = {{}};
  for (const [k, v] of Object.entries(HEADERS_TEMPLATE)) {{ headersObj[k] = replaceVu(v); }}
  const bodyStr = replaceVu(BODY_TEMPLATE);
  const res = (method === 'GET') ? http.get(url, {{ headers: headersObj }})
    : (method === 'POST') ? http.post(url, bodyStr, {{ headers: headersObj }})
    : (method === 'PUT') ? http.put(url, bodyStr, {{ headers: headersObj }})
    : (method === 'DELETE') ? http.del(url, {{ headers: headersObj }})
    : http.request(method, url, bodyStr, {{ headers: headersObj }});
  const requestArgs = {{ url, method, headers: headersObj, body: bodyStr }};"""
    else:
        url = _build_url_with_params(base_url, query_params)
        headers_js = json.dumps(headers) if headers else "{}"
        method_js = json.dumps(method)
        body_js = json.dumps(body) if body else '""'
        # non-per-VU: 변수로 url/method/headers/body 정의 후 요청·requestArgs 로그
        call_js = f"""  const url = {json.dumps(url)};
  const method = {method_js};
  const headers = {headers_js};
  const body = {body_js};
  const res = (method === 'GET') ? http.get(url, {{ headers }})
    : (method === 'POST') ? http.post(url, body, {{ headers }})
    : (method === 'PUT') ? http.put(url, body, {{ headers }})
    : (method === 'DELETE') ? http.del(url, {{ headers }})
    : http.request(method, url, body, {{ headers }});
  const requestArgs = {{ url, method, headers, body }};"""

    ctx = {
        "per_vu": per_vu,
        "options_js": options_js,
        "call_js": call_js,
        "sleep_s": sleep_s,
        "url_template_js": url_template_js if per_vu else "",
        "headers_js": headers_js if per_vu else "{}",
        "body_template_js": body_template_js if per_vu else '""',
        "method_js": method_js if per_vu else '""',
        "error_rules_js": error_rules_js,
    }
    return _K6_SCRIPT_TEMPLATE.render(**ctx)


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
        # k6 counter: 일부 버전은 "count", 일부는 "value" 사용
        count = int(_metric_val(hr_reqs, "count") or _metric_val(hr_reqs, "value"))
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
_REQ_PREFIX = "__REQ__"
_REQ_END = "__REQEND__"
_MAX_REQUEST_RESPONSES = 10_000


def _append_log(run_id: str, line: str, stream: str = "stdout") -> None:
    """로그 버퍼에 한 줄 추가. stream이 stderr면 [stderr] 접두사."""
    if not line and stream == "stdout":
        return
    text = f"[stderr] {line}" if stream == "stderr" else line
    with _log_lock:
        buf = _log_buffers.setdefault(run_id, [])
        buf.append(text)
        if len(buf) > _MAX_LOG_LINES:
            del buf[: len(buf) - _MAX_LOG_LINES]


def get_logs(run_id: str) -> list[str]:
    """run_id에 해당하는 k6 실행 로그 라인 목록 반환 (복사)."""
    with _log_lock:
        return list(_log_buffers.get(run_id, []))


def _parse_one_req_obj(obj: dict) -> dict | None:
    """파싱된 JSON 객체 하나를 저장용 dict로 변환. status는 숫자/문자열 모두 허용. requestArgs 있으면 request_args(JSON 문자열)로 저장."""
    try:
        status = obj.get("status")
        duration = obj.get("duration")
        body = obj.get("body")
        requested_at = None
        raw = obj.get("requestedAt") or obj.get("requested_at")
        if raw and isinstance(raw, str):
            try:
                s = raw.strip().replace("Z", "+00:00")
                # 초 이하 6자리(microsecond); 초과 분은 버림
                s = re.sub(r"(\.\d+)", lambda m: (m.group(1) + "000000")[:7], s)
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is not None:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                requested_at = dt
            except (ValueError, TypeError):
                pass
        status_code = None
        if status is not None:
            try:
                status_code = int(status) if not isinstance(status, int) else status
            except (TypeError, ValueError):
                pass
        request_args = None
        ra = obj.get("requestArgs") or obj.get("request_args")
        merged: dict = {}
        if ra is not None and isinstance(ra, dict):
            merged.update(ra)
        vu_top = obj.get("vu")
        if vu_top is not None:
            merged["vu"] = vu_top
        sit = obj.get("scenarioIter")
        if sit is None:
            sit = obj.get("iter")
        if sit is not None:
            merged["scenarioIter"] = sit
        if merged:
            request_args = json.dumps(merged, ensure_ascii=False)
        failed = obj.get("failed")
        if failed is not None and not isinstance(failed, bool):
            failed = bool(failed)
        elif failed is None:
            failed = False  # 구버전 __REQ__ 로그에는 failed 없음 → 실패 아님으로 저장
        return {
            "status_code": status_code if (status_code is None or 0 <= status_code <= 999) else None,
            "response_time_ms": float(duration) if duration is not None else None,
            "body_preview": (body if body is not None else None) or None,
            "requested_at": requested_at,
            "request_args": request_args,
            "failed": failed,
        }
    except (TypeError, ValueError, KeyError):
        return None


def _extract_req_json(line_str: str) -> str | None:
    """__REQ__ 와 __REQEND__ 사이 문자열 반환. k6가 두 마커로 감싸서 출력."""
    a = line_str.find(_REQ_PREFIX)
    if a < 0:
        return None
    start = a + len(_REQ_PREFIX)
    b = line_str.find(_REQ_END, start)
    if b < 0:
        return None
    return line_str[start:b].strip()


def _parse_one_req_line(line_str: str) -> dict | None:
    """한 줄에서 __REQ__...__REQEND__ 구간 추출 후 JSON 파싱해 row dict 반환."""
    json_str = _extract_req_json(line_str)
    if not json_str:
        return None
    # k6 stderr가 msg="..." 로 감쌀 때 \" 만 치환 (복잡한 이스케이프 파싱 없음)
    if "\\\"" in json_str or '\\"' in json_str:
        json_str = json_str.replace("\\\\", "\\").replace("\\\"", "\"")
    try:
        obj = json.loads(json_str)
        return _parse_one_req_obj(obj)
    except (json.JSONDecodeError, TypeError, ValueError, KeyError):
        return None


def _parse_request_responses(stdout_bytes: bytes) -> list[dict]:
    """stdout에서 __REQ__...__REQEND__ 포함 줄 파싱."""
    out: list[dict] = []
    req_end_b = _REQ_END.encode("utf-8")
    for line in stdout_bytes.splitlines():
        if _REQ_PREFIX.encode("utf-8") not in line or req_end_b not in line:
            continue
        line_str = line.decode("utf-8", errors="replace")
        row = _parse_one_req_line(line_str)
        if row:
            out.append(row)
        if len(out) >= _MAX_REQUEST_RESPONSES:
            break
    return out


def _parse_request_responses_from_stderr(stderr_bytes: bytes) -> list[dict]:
    """stderr에서 __REQ__...__REQEND__ 포함 줄 파싱."""
    out: list[dict] = []
    req_end_b = _REQ_END.encode("utf-8")
    for line in stderr_bytes.splitlines():
        if _REQ_PREFIX.encode("utf-8") not in line or req_end_b not in line:
            continue
        line_str = line.decode("utf-8", errors="replace")
        row = _parse_one_req_line(line_str)
        if row:
            out.append(row)
        if len(out) >= _MAX_REQUEST_RESPONSES:
            break
    return out


def start(
    run_id: str,
    test: PerformanceTest,
    on_complete: Callable[[str, int, dict | None, str | None], None] | None = None,
    request_header_overrides: dict[str, str] | None = None,
) -> None:
    """백그라운드에서 k6 실행. 스크립트는 stdin으로 전달(k6 run -). stdout/stderr는 스레드로 읽어 로그 버퍼에 적재, 요약은 누적 stdout에서 파싱."""
    script = generate_script(test, request_header_overrides=request_header_overrides)
    script_bytes = script.encode("utf-8")

    with _processes_lock:
        if run_id in _processes:
            return
        with _log_lock:
            _log_buffers[run_id] = []
        k6_cmd = ["k6", "run", "-"]
        influx_url = (INFLUXDB_URL or "").strip().rstrip("/")
        if influx_url:
            k6_cmd = ["k6", "run", "--out", f"influxdb={influx_url}/k6", "-"]
        try:
            proc = subprocess.Popen(
                k6_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            with _log_lock:
                _log_buffers.pop(run_id, None)
            raise K6NotFoundError(
                "k6가 설치되어 있지 않거나 PATH에 없습니다. "
                "로컬에서는 k6를 설치하거나 Docker로 API를 실행하세요."
            )
        _processes[run_id] = proc

    try:
        proc.stdin.write(script_bytes)
        proc.stdin.close()
    except (OSError, BrokenPipeError):
        with _processes_lock:
            _processes.pop(run_id, None)
        with _log_lock:
            _log_buffers.pop(run_id, None)
        if on_complete:
            on_complete(run_id, -1, None, "스크립트 전달 실패")
        return

    run_timeout = min(
        max(int(test.duration or 60) + 60, 120),
        7200,
    )
    stdout_accumulator: list[bytes] = []
    stderr_accumulator: list[bytes] = []

    def read_stdout():
        try:
            for raw in iter(proc.stdout.readline, b""):
                stdout_accumulator.append(raw)
                try:
                    line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
                    if not line.startswith(_REQ_PREFIX):
                        _append_log(run_id, line, "stdout")
                except Exception:
                    pass
        except Exception:
            pass
        try:
            proc.stdout.close()
        except Exception:
            pass

    def read_stderr():
        try:
            for raw in iter(proc.stderr.readline, b""):
                stderr_accumulator.append(raw)
                try:
                    line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
                    _append_log(run_id, line, "stderr")
                except Exception:
                    pass
        except Exception:
            pass
        try:
            proc.stderr.close()
        except Exception:
            pass

    def wait_and_cleanup():
        exit_code = -1
        summary = None
        error_output = None
        t_stdout = threading.Thread(target=read_stdout, daemon=True)
        t_stderr = threading.Thread(target=read_stderr, daemon=True)
        t_stdout.start()
        t_stderr.start()
        try:
            exit_code = proc.wait(timeout=run_timeout)
            if exit_code is None:
                exit_code = -1
        except subprocess.TimeoutExpired:
            proc.kill()
            exit_code = -9
            error_output = "프로세스 타임아웃으로 종료"
            _append_log(run_id, error_output, "stderr")
        finally:
            try:
                proc.stdout.close()
            except Exception:
                pass
            try:
                proc.stderr.close()
            except Exception:
                pass
            t_stdout.join(timeout=2.0)
            t_stderr.join(timeout=2.0)

        stdout_bytes = b"".join(stdout_accumulator)
        if not error_output and exit_code != 0:
            with _log_lock:
                buf = _log_buffers.get(run_id, [])
                stderr_lines = [x for x in buf if x.startswith("[stderr] ")]
                if stderr_lines:
                    error_output = "\n".join(
                        x.replace("[stderr] ", "", 1) for x in stderr_lines
                    ).strip() or None
        if not error_output and exit_code == -9:
            error_output = "프로세스 타임아웃으로 종료"
        if stdout_bytes and _SUMMARY_MARKER in stdout_bytes and _SUMMARY_END in stdout_bytes:
            try:
                start_i = stdout_bytes.index(_SUMMARY_MARKER) + len(_SUMMARY_MARKER)
                end_i = stdout_bytes.index(_SUMMARY_END)
                json_str = stdout_bytes[start_i:end_i].decode("utf-8", errors="replace")
                summary = _parse_k6_summary(json.loads(json_str))
            except (ValueError, json.JSONDecodeError, TypeError, KeyError):
                pass
        stderr_bytes = b"".join(stderr_accumulator)
        req_from_stdout = _parse_request_responses(stdout_bytes)
        req_from_stderr = _parse_request_responses_from_stderr(stderr_bytes)
        request_responses = (req_from_stdout + req_from_stderr)[:_MAX_REQUEST_RESPONSES]
        if not request_responses and (
            _REQ_END.encode("utf-8") in stdout_bytes or _REQ_END.encode("utf-8") in stderr_bytes
        ):
            logger.warning(
                "k6 __REQ__...__REQEND__ 파싱 결과 0건 (stdout %s bytes, stderr %s bytes).",
                len(stdout_bytes),
                len(stderr_bytes),
            )
        # 저장하는 요청 수는 실제 파싱한 __REQ__ 건수로 통일 (summary와 불일치 방지)
        if summary is not None:
            summary = {**summary, "request_count": len(request_responses)}
        with _processes_lock:
            _processes.pop(run_id, None)
        if on_complete:
            try:
                on_complete(
                    run_id,
                    exit_code,
                    summary,
                    error_output,
                    request_responses=request_responses,
                )
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
