"""에러 페이지 판별: DB JSON + 레거시 단일 필드. 여러 규칙 중 하나라도 실패 조건이면 iteration 실패(OR)."""

from __future__ import annotations

import json
from typing import Any

# test_repository.update(..., error_rules=...) 에서 생략 시 에러 판별 컬럼 유지
ERROR_RULES_UNCHANGED = object()


def parse_error_rules_json_array(data: list[Any]) -> list[dict[str, str]]:
    """JSON/API 배열 [{pattern, matchMode|match_mode}, ...] → k6·검증용."""
    out: list[dict[str, str]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        pat = (item.get("pattern") or "").strip()
        if not pat:
            continue
        mode = (item.get("matchMode") or item.get("match_mode") or "contains").strip()
        if mode not in ("contains", "not_contains"):
            mode = "contains"
        out.append({"pattern": pat, "matchMode": mode})
    return out


def parse_error_rules_from_list(raw: Any) -> list[dict[str, str]]:
    """http_scenario 스텝 필드 errorPageRules (이미 파싱된 list)."""
    if isinstance(raw, list):
        return parse_error_rules_json_array(raw)
    return []


def parse_error_rules_from_test(test: Any) -> list[dict[str, str]]:
    """k6/브라우저 공통. 각 항목: pattern, matchMode (contains | not_contains)."""
    raw = getattr(test, "error_page_rules", None)
    if raw and str(raw).strip():
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                out = parse_error_rules_json_array(data)
                if out:
                    return out
        except (json.JSONDecodeError, TypeError):
            pass
    pat = (getattr(test, "error_page_pattern", None) or "").strip()
    if not pat:
        return []
    mode = (getattr(test, "error_page_match_mode", None) or "contains").strip() or "contains"
    if mode not in ("contains", "not_contains"):
        mode = "contains"
    return [{"pattern": pat, "matchMode": mode}]


def serialize_error_rules_for_db(rules: list[Any]) -> tuple[str | None, str | None, str]:
    """(error_page_rules JSON, 레거시 pattern, 레거시 match_mode). 규칙 없으면 전부 비움."""
    filtered: list[dict[str, str]] = []
    for r in rules:
        if hasattr(r, "pattern"):
            pat = (getattr(r, "pattern", None) or "").strip()
            mode = getattr(r, "match_mode", None) or "contains"
        elif isinstance(r, dict):
            pat = str(r.get("pattern") or "").strip()
            mode = r.get("matchMode") or r.get("match_mode") or "contains"
        else:
            continue
        mode = str(mode).strip()
        if mode not in ("contains", "not_contains"):
            mode = "contains"
        if not pat:
            continue
        filtered.append({"pattern": pat, "matchMode": mode})
    if not filtered:
        return None, None, "contains"
    return json.dumps(filtered, ensure_ascii=False), filtered[0]["pattern"], filtered[0]["matchMode"]


def resolve_error_rules_for_update(body: Any, existing: Any) -> Any:
    """PUT 시 model_fields_set 기준으로 (error_page_rules JSON, pattern, mode) 또는 ERROR_RULES_UNCHANGED."""
    fs = getattr(body, "model_fields_set", None) or set()
    if not fs & {"error_page_rules", "error_page_pattern", "error_page_match_mode"}:
        return ERROR_RULES_UNCHANGED
    if "error_page_rules" in fs:
        rules = getattr(body, "error_page_rules", None)
        return serialize_error_rules_for_db(rules if rules is not None else [])
    cur = parse_error_rules_from_test(existing)
    if "error_page_pattern" in fs:
        pat = (getattr(body, "error_page_pattern", None) or "").strip()
        mode = (
            getattr(body, "error_page_match_mode", None)
            if "error_page_match_mode" in fs
            else getattr(existing, "error_page_match_mode", None)
        ) or "contains"
        if not pat:
            return serialize_error_rules_for_db([])
        m = "not_contains" if str(mode).strip() == "not_contains" else "contains"
        return serialize_error_rules_for_db([{"pattern": pat, "matchMode": m}])
    if "error_page_match_mode" in fs and cur:
        m = "not_contains" if str(getattr(body, "error_page_match_mode", None) or "").strip() == "not_contains" else "contains"
        return serialize_error_rules_for_db([{"pattern": r["pattern"], "matchMode": m} for r in cur])
    return ERROR_RULES_UNCHANGED
