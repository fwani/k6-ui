"""브라우저(Chromium) 렌더링 테스트 실행. Playwright로 페이지 로드 후 Web Vitals 수집."""

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.parse import quote

from app.config import INFLUXDB_URL
from app.models.db import PerformanceTest
from app.services import influxdb_writer
from app.services.error_page_rules import parse_error_rules_from_test

logger = logging.getLogger(__name__)

# k6_runner.VU_PLACEHOLDER 와 동일. k6_runner 임포트는 순환 참조를 피하기 위해 여기서 문자열 상수만 둠.
VU_PLACEHOLDER = "{{VU}}"

# k6_runner와 동일한 로그 버퍼 키 사용 시 순환 참조 가능하므로 별도 버퍼 유지.
# runs.py get_run_logs에서 run.engine으로 분기해 호출함.
_log_buffers: dict[str, list[str]] = {}
_log_lock = threading.Lock()

_running: dict[str, dict] = {}  # run_id -> { "stop_requested": bool, "context": ... }
_running_lock = threading.Lock()


class BrowserNotFoundError(Exception):
    """Playwright/Chromium 미설치 또는 실행 실패."""


# 표준 HTTP 헤더 이름 (서버가 대소문자 구분하는 경우 대비)
_HEADER_NAME_CANONICAL = {
    "authorization": "Authorization",
    "content-type": "Content-Type",
    "accept": "Accept",
    "accept-language": "Accept-Language",
    "user-agent": "User-Agent",
}


def _parse_headers(headers: str | None) -> dict[str, str]:
    """테스트 headers JSON 문자열 → 요청에 쓸 dict. Authorization 등 표준 이름으로 정규화."""
    if not headers or not headers.strip():
        return {}
    try:
        d = json.loads(headers)
        if not isinstance(d, dict):
            return {}
        out = {}
        for k, v in d.items():
            key = str(k).strip()
            if not key:
                continue
            val = str(v) if v is not None else ""
            canonical = _HEADER_NAME_CANONICAL.get(key.lower())
            out[canonical if canonical else key] = val
        return out
    except (json.JSONDecodeError, TypeError):
        return {}


def _apply_header_overrides(
    base: dict[str, str], overrides: dict[str, str] | None
) -> dict[str, str]:
    """실행 시 헤더를 테스트 헤더 위에 덮어씀. 표준 헤더 이름은 _parse_headers와 동일 규칙."""
    if not overrides:
        return dict(base)
    out = dict(base)
    for k, v in overrides.items():
        key = str(k).strip()
        if not key:
            continue
        val = "" if v is None else str(v)
        canonical = _HEADER_NAME_CANONICAL.get(key.lower())
        out[canonical if canonical else key] = val
    return out


def _headers_for_vu(
    headers_str: str,
    request_header_overrides: dict[str, str] | None,
    vu_display: str,
) -> dict[str, str]:
    """테스트 저장 헤더 + 실행 시 오버라이드를 합친 뒤 값에 {{VU}} 치환(k6와 동일)."""
    merged = _apply_header_overrides(
        _parse_headers(headers_str), request_header_overrides
    )
    if not merged:
        return {}
    vu = str(vu_display)
    return {k: str(v).replace(VU_PLACEHOLDER, vu) for k, v in merged.items()}


def _cookie_header_to_playwright(cookie_header: str, page_url: str) -> list[dict[str, str]]:
    """Cookie 헤더 문자열(name=value; …)을 Playwright add_cookies 형태로. Chromium은 Cookie 헤더를 extra로 잘 못 실음."""
    out: list[dict[str, str]] = []
    url = (page_url or "").strip()
    if not url:
        return out
    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        name, value = name.strip(), value.strip()
        if not name:
            continue
        if name.lower() in (
            "expires",
            "max-age",
            "domain",
            "path",
            "secure",
            "httponly",
            "samesite",
        ):
            continue
        out.append({"name": name, "value": value, "url": url})
    return out


def _playwright_context_options(
    merged_headers: dict[str, str], page_url: str
) -> tuple[dict, list[dict[str, str]], dict[str, str]]:
    """new_context kwargs, add_cookies 목록, route로 합칠 헤더(Authorization 등). Cookie/User-Agent는 여기서 제외."""
    inject: dict[str, str] = {}
    user_agent: str | None = None
    cookie_strs: list[str] = []

    for k, v in merged_headers.items():
        lk = str(k).lower()
        if lk == "cookie":
            if v is not None and str(v).strip():
                cookie_strs.append(str(v).strip())
            continue
        if lk == "user-agent":
            vs = str(v).strip() if v is not None else ""
            if vs:
                user_agent = vs
            continue
        inject[str(k)] = "" if v is None else str(v)

    cookies: list[dict[str, str]] = []
    for cs in cookie_strs:
        cookies.extend(_cookie_header_to_playwright(cs, page_url))

    ctx_kwargs: dict = {}
    if user_agent:
        ctx_kwargs["user_agent"] = user_agent
    return ctx_kwargs, cookies, inject


# script/stylesheet/image 등에 Authorization이 붙으면 정적 서버가 403·CORS로 막아 빈 화면이 되는 경우가 많음.
_HEADER_INJECT_RESOURCE_TYPES = frozenset(
    {"document", "fetch", "xhr", "eventsource"}
)


def _merge_outgoing_headers(
    request_headers: dict[str, str], inject: dict[str, str]
) -> dict[str, str]:
    """기존 요청 헤더에 inject를 덮어씀. 같은 의미(대소문자 무시)의 키는 inject로 통일."""
    inj_lower = {str(k).lower() for k in inject}
    out: dict[str, str] = {}
    for k, v in request_headers.items():
        if str(k).lower() in inj_lower:
            continue
        out[str(k)] = str(v) if v is not None else ""
    for k, v in inject.items():
        out[str(k)] = "" if v is None else str(v)
    return out


def _install_outgoing_header_route(context, inject: dict[str, str]) -> None:
    """document·fetch·xhr(SSE)·… 에만 Authorization 등 합침. script/CSS에는 붙이지 않음."""
    if not inject:
        return

    def _handler(route) -> None:
        try:
            req = route.request
            rtype = getattr(req, "resource_type", "") or ""
            if rtype == "websocket":
                route.continue_()
                return
            if rtype not in _HEADER_INJECT_RESOURCE_TYPES:
                route.continue_()
                return
            merged = _merge_outgoing_headers(dict(req.headers), inject)
            route.continue_(headers=merged)
        except Exception as ex:
            logger.debug("header route failed: %s", ex)
            try:
                route.continue_()
            except Exception:
                pass

    context.route("**/*", _handler)


def _build_url(base: str, query_params: str | None) -> str:
    """base URL + query_params(JSON array) → 최종 URL."""
    base = (base or "").strip() or "https://example.com"
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
            k = item.get("key")
            v = item.get("value", "")
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


def _append_log(run_id: str, line: str) -> None:
    with _log_lock:
        buf = _log_buffers.setdefault(run_id, [])
        buf.append(line)


def get_logs(run_id: str) -> list[str]:
    with _log_lock:
        return list(_log_buffers.get(run_id, []))


def _parse_browser_actions_json(raw: str | None) -> list[dict[str, Any]]:
    if not raw or not str(raw).strip():
        return []
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("browser_actions JSON invalid, ignoring: %s", e)
        return []
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def _run_browser_actions(
    page: Any,
    actions: list[dict[str, Any]],
    run_id: str,
    vu_display: int,
) -> None:
    """페이지 로드 후 순서대로 wait_selector / click / sleep 실행. 실패 시 예외."""
    n = len(actions)
    for i, act in enumerate(actions):
        kind = str(act.get("type") or act.get("kind") or "").strip()
        to_raw = act.get("timeoutMs", 30000)
        try:
            timeout_ms = int(to_raw)
        except (TypeError, ValueError):
            timeout_ms = 30_000
        timeout_ms = max(1_000, min(60_000, timeout_ms))

        if kind == "wait_selector":
            sel = str(act.get("selector") or "").strip()
            if not sel:
                raise ValueError("wait_selector: selector 가 비어 있습니다.")
            page.locator(sel).first.wait_for(state="visible", timeout=timeout_ms)
        elif kind == "click":
            sel = str(act.get("selector") or "").strip()
            if not sel:
                raise ValueError("click: selector 가 비어 있습니다.")
            # 클릭 후 라우팅/네비게이션까지 기다리면 SPA에서 타임아웃이 자주 남.
            # 다음 단계 wait_selector 등으로 화면을 맞추는 편이 안정적임.
            page.locator(sel).first.click(
                timeout=timeout_ms, no_wait_after=True
            )
        elif kind == "sleep":
            sm_raw = act.get("sleepMs")
            if sm_raw is None:
                raise ValueError("sleep: sleepMs 가 필요합니다.")
            try:
                sleep_ms = int(sm_raw)
            except (TypeError, ValueError) as e:
                raise ValueError("sleep: sleepMs 가 정수가 아닙니다.") from e
            sleep_ms = max(0, min(30_000, sleep_ms))
            page.wait_for_timeout(sleep_ms)
        else:
            raise ValueError(f'지원하지 않는 browser action type: "{kind}"')
        _append_log(
            run_id,
            f"VU {vu_display}: browser action {i + 1}/{n} ({kind}) 완료",
        )


_WEB_VITALS_SCRIPT = """
() => new Promise((resolve) => {
  const out = { lcp_ms: null, fcp_ms: null, cls: null, ttfb_ms: null };
  const nav = performance.getEntriesByType('navigation')[0];
  if (nav && typeof nav.responseStart === 'number' && typeof nav.requestStart === 'number') {
    out.ttfb_ms = nav.responseStart - nav.requestStart;
  }
  try {
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length) out.fcp_ms = entries[entries.length - 1].startTime;
    }).observe({ type: 'first-contentful-paint', buffered: true });
  } catch (_) {}
  try {
    new PerformanceObserver((list) => {
      const entries = list.getEntries();
      if (entries.length) out.lcp_ms = entries[entries.length - 1].startTime;
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (_) {}
  let cls = 0;
  try {
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) { if (!e.hadRecentInput) cls += e.value; }
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (_) {}
  setTimeout(() => {
    out.cls = cls;
    if (out.fcp_ms == null && typeof performance.getEntriesByType === 'function') {
      const paints = performance.getEntriesByType('paint');
      for (let i = 0; i < paints.length; i++) {
        if (paints[i].name === 'first-contentful-paint') {
          out.fcp_ms = paints[i].startTime;
          break;
        }
      }
    }
    resolve(out);
  }, 2500);
})
"""


def start(
    run_id: str,
    test: PerformanceTest,
    on_complete: Callable[[str, int, dict | None, str | None], None] | None = None,
    request_header_overrides: dict[str, str] | None = None,
    *,
    headless: bool = True,
) -> None:
    """Chromium으로 test.target_url를 VUs 수만큼 로드 후 Web Vitals 수집, on_complete 호출.

    headless=False 이면 창을 띄움(로컬에서 API 실행·GUI 또는 DISPLAY/xvfb 필요). VU>1이면 창이 여러 개일 수 있음.
    """
    url = _build_url(
        getattr(test, "target_url", None) or "",
        getattr(test, "query_params", None),
    )
    vus = max(1, int(getattr(test, "vus", 1) or 1))
    try:
        vu_start = max(1, int(getattr(test, "vu_start", 1) or 1))
    except (TypeError, ValueError):
        vu_start = 1
    # 스레드에서 사용하므로 세션 종료 전에 헤더/에러패턴·판별방식 캡처
    headers_str = getattr(test, "headers", None) or ""
    error_rules = parse_error_rules_from_test(test)
    has_error_rules = bool(error_rules)

    def run_browser() -> None:
        summary: dict | None = None
        error_output: str | None = None
        exit_code = 0
        response_rows: list[tuple[int, dict]] = []  # (vu_index, row) for request_responses
        start_time = datetime.now(timezone.utc)
        vitals_list: list[dict] = []
        influx_points: list[tuple[dict, int]] = []

        with _running_lock:
            _running[run_id] = {"stop_requested": False}
        with _log_lock:
            _log_buffers[run_id] = []
        actions_list = _parse_browser_actions_json(getattr(test, "browser_actions", None))
        if actions_list:
            _append_log(run_id, f"로드 후 브라우저 동작 {len(actions_list)}단계 실행 예정")
        if not headless:
            _append_log(
                run_id,
                "Chromium 창 표시 모드입니다. API 프로세스에 디스플레이가 없으면 실패할 수 있습니다.",
            )

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            error_output = (
                "playwright가 설치되어 있지 않습니다. "
                "pip install playwright && playwright install chromium"
            )
            logger.exception("playwright import failed: %s", e)
            exit_code = 1
            if on_complete:
                try:
                    on_complete(run_id, exit_code, None, error_output, request_responses=[])
                except Exception as e2:
                    logger.exception("on_complete failed: %s", e2)
            with _running_lock:
                _running.pop(run_id, None)
            return

        results_lock = threading.Lock()

        def run_one_vu(vu_index: int) -> None:
            with _running_lock:
                if _running.get(run_id, {}).get("stop_requested"):
                    return
            _append_log(run_id, f"VU {vu_index + 1}/{vus} starting (concurrent)")
            vu_display = str(vu_index + vu_start)
            merged_headers = _headers_for_vu(
                headers_str, request_header_overrides, vu_display
            )
            load_url = (
                url.replace(VU_PLACEHOLDER, vu_display)
                if VU_PLACEHOLDER in url
                else url
            )
            ctx_kwargs, header_cookies, header_inject = _playwright_context_options(
                merged_headers, load_url
            )
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=headless)
                    try:
                        context = browser.new_context(**ctx_kwargs)
                        if header_cookies:
                            try:
                                context.add_cookies(header_cookies)
                            except Exception as ce:
                                logger.warning(
                                    "add_cookies failed VU %s: %s",
                                    vu_index + 1,
                                    ce,
                                )
                                _append_log(
                                    run_id,
                                    f"VU {vu_index + 1}: Cookie 설정 실패(형식·URL 도메인 확인): {ce}",
                                )
                        _install_outgoing_header_route(context, header_inject)
                        if merged_headers:
                            keys = sorted(merged_headers.keys())
                            via = []
                            if header_inject:
                                via.append("doc+api(route)")
                            if ctx_kwargs.get("user_agent"):
                                via.append("user_agent")
                            if header_cookies:
                                via.append(f"cookies({len(header_cookies)})")
                            _append_log(
                                run_id,
                                f"VU {vu_index + 1}: 적용 헤더 키 {keys} → "
                                + (", ".join(via) if via else "(없음)"),
                            )
                        with _running_lock:
                            if run_id in _running:
                                _running[run_id].setdefault("contexts", []).append(context)
                        try:
                            page = context.new_page()
                            page.set_viewport_size({"width": 1920, "height": 1080})
                            page.goto(load_url, wait_until="load", timeout=60000)
                            try:
                                page.wait_for_load_state(
                                    "networkidle", timeout=15000
                                )
                            except Exception:
                                pass
                            if actions_list:
                                _run_browser_actions(
                                    page,
                                    actions_list,
                                    run_id,
                                    vu_index + 1,
                                )
                            vitals = page.evaluate(_WEB_VITALS_SCRIPT)
                            body_text_stored = ""
                            try:
                                raw_bt = page.evaluate(
                                    "() => (document.body && document.body.innerText) || (document.documentElement && document.documentElement.innerText) || ''"
                                )
                                body_text_stored = "" if raw_bt is None else str(raw_bt)
                            except Exception:
                                body_text_stored = ""
                            # 200이어도 판별 조건에 따라 실패 처리: contains=패턴 포함 시 실패, not_contains=패턴 미포함 시 실패
                            is_error_page = False
                            if error_rules:
                                try:
                                    current_url = page.url or url
                                    u = current_url or ""
                                    b = body_text_stored or ""
                                    for rule in error_rules:
                                        pat = rule.get("pattern") or ""
                                        if not pat:
                                            continue
                                        not_contains = rule.get("matchMode") == "not_contains"
                                        found = pat in u or pat in b
                                        if not_contains:
                                            if not found:
                                                is_error_page = True
                                                break
                                        elif found:
                                            is_error_page = True
                                            break
                                except Exception:
                                    pass
                            screenshot_bytes: bytes | None = None
                            try:
                                screenshot_bytes = page.screenshot(type="jpeg", quality=20)
                            except Exception as scr_e:
                                logger.warning("screenshot failed VU %s: %s", vu_index + 1, scr_e)
                            iter_time = datetime.now(timezone.utc)
                            ts_ns = int(iter_time.timestamp() * 1e9)
                            if isinstance(vitals, dict):
                                lcp = vitals.get("lcp_ms")
                                fcp = vitals.get("fcp_ms")
                                cls_v = vitals.get("cls")
                                ttfb = vitals.get("ttfb_ms")
                                _append_log(
                                    run_id,
                                    f"VU {vu_index + 1} LCP: {lcp}ms, FCP: {fcp}ms, CLS: {cls_v}, TTFB: {ttfb}ms",
                                )
                                point = (
                                    {
                                        "lcp_ms": float(lcp) if lcp is not None else None,
                                        "fcp_ms": float(fcp) if fcp is not None else None,
                                        "ttfb_ms": float(ttfb) if ttfb is not None else None,
                                        "cls": float(cls_v) if cls_v is not None else None,
                                    },
                                    ts_ns,
                                )
                                resp_ms = lcp if lcp is not None else (ttfb if ttfb is not None else None)
                                with results_lock:
                                    vitals_list.append(vitals)
                                    influx_points.append(point)
                                    response_rows.append(
                                        (
                                            vu_index,
                                            {
                                                "status_code": 200,
                                                "response_time_ms": float(resp_ms) if resp_ms is not None else None,
                                                "body_preview": body_text_stored or None,
                                                "requested_at": iter_time,
                                                "request_args": json.dumps({"url": load_url, "headers": merged_headers}),
                                                "screenshot": screenshot_bytes,
                                                "failed": is_error_page,
                                            },
                                        )
                                    )
                            else:
                                with results_lock:
                                    vitals_list.append({})
                                    response_rows.append(
                                        (
                                            vu_index,
                                            {
                                                "status_code": 200,
                                                "response_time_ms": None,
                                                "body_preview": body_text_stored or None,
                                                "requested_at": iter_time,
                                                "request_args": json.dumps({"url": load_url, "headers": merged_headers}),
                                                "screenshot": screenshot_bytes,
                                                "failed": is_error_page,
                                            },
                                        )
                                    )
                        finally:
                            try:
                                context.close()
                            except Exception:
                                pass
                            with _running_lock:
                                entry = _running.get(run_id)
                                if entry and "contexts" in entry:
                                    try:
                                        entry["contexts"].remove(context)
                                    except ValueError:
                                        pass
                    finally:
                        browser.close()
            except Exception as e:
                logger.warning("browser_runner VU %s failed: %s", vu_index + 1, e)
                with results_lock:
                    vitals_list.append({})

        try:
            threads = [
                threading.Thread(target=run_one_vu, args=(i,), daemon=True)
                for i in range(vus)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=120)
        except Exception as e:
            logger.exception("browser_runner error: %s", e)
            error_output = str(e)[:8000]
            exit_code = 1

        with _running_lock:
            entry = _running.pop(run_id, None)
            if entry and entry.get("stop_requested"):
                exit_code = 1
                error_output = (error_output or "").strip() or "사용자에 의해 중지됨"

        end_time = datetime.now(timezone.utc)
        exec_sec = max(0.0, (end_time - start_time).total_seconds())
        n = len(vitals_list)

        def _mean(key: str) -> float | None:
            vals = [v.get(key) for v in vitals_list if v.get(key) is not None]
            if not vals:
                return None
            return sum(float(x) for x in vals) / len(vals)

        lcp_ms = _mean("lcp_ms")
        fcp_ms = _mean("fcp_ms")
        cls_val = _mean("cls")
        ttfb_ms = _mean("ttfb_ms")
        # 브라우저 Run 대표 응답 시간: 체감에 가까운 LCP → FCP → TTFB 순으로 사용
        avg_ms = (
            lcp_ms if lcp_ms is not None
            else (fcp_ms if fcp_ms is not None else (ttfb_ms if ttfb_ms is not None else 0.0))
        )
        max_lcp = max((v.get("lcp_ms") for v in vitals_list if v.get("lcp_ms") is not None), default=None)
        max_response = float(max_lcp) if max_lcp is not None else (lcp_ms if lcp_ms is not None else avg_ms)

        request_responses_sorted = [row for _, row in sorted(response_rows, key=lambda x: x[0])]
        failure_count = sum(1 for r in request_responses_sorted if r.get("failed"))
        failure_rate = (failure_count / n) if n else (1.0 if exit_code != 0 else 0.0)

        summary = {
            "avg_response_time": avg_ms,
            "max_response_time": max_response,
            "failure_rate": failure_rate if has_error_rules else (0.0 if exit_code == 0 else 1.0),
            "request_count": n,
            "tps_or_rps": n / exec_sec if exec_sec > 0 else 0.0,
            "execution_time": exec_sec,
            "lcp_ms": lcp_ms,
            "fcp_ms": fcp_ms,
            "cls": cls_val,
            "ttfb_ms": ttfb_ms,
        }

        if INFLUXDB_URL and influx_points:
            test_id_val = getattr(test, "id", "") or ""
            influxdb_writer.write_browser_vitals_batch(
                INFLUXDB_URL, run_id, test_id_val, influx_points
            )

        request_responses = request_responses_sorted
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
                logger.exception("on_complete failed: %s", e)

    t = threading.Thread(target=run_browser, daemon=True)
    t.start()


def stop(run_id: str) -> bool:
    """실행 중인 브라우저 Run 중지 요청. 모든 VU 컨텍스트를 닫음."""
    with _running_lock:
        entry = _running.get(run_id)
        if not entry:
            return False
        entry["stop_requested"] = True
        for ctx in entry.get("contexts", []):
            try:
                ctx.close()
            except Exception:
                pass
        entry["contexts"] = []
    return True


def is_running(run_id: str) -> bool:
    with _running_lock:
        return run_id in _running
