"""Performance Test CRUD."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.schemas.test import normalize_tag_list
from app.models.db import PerformanceTest, Tag
from app.services.error_page_rules import ERROR_RULES_UNCHANGED

# update(..., http_scenario=...) 에서 생략 시 DB 값 유지
HTTP_SCENARIO_UNCHANGED = object()
BROWSER_ACTIONS_UNCHANGED = object()
TAGS_UNCHANGED = object()


def _get_or_create_tag(db: Session, name: str) -> Tag:
    stmt = select(Tag).where(Tag.name == name)
    row = db.execute(stmt).scalar_one_or_none()
    if row:
        return row
    t = Tag(name=name)
    db.add(t)
    db.flush()
    return t


def _sync_tags_to_test(db: Session, test: PerformanceTest, names: list[str]) -> None:
    normalized = normalize_tag_list(names)
    test.tags.clear()
    for name in normalized:
        tag = _get_or_create_tag(db, name)
        test.tags.append(tag)


def create(
    db: Session,
    *,
    name: str,
    target_url: str,
    http_method: str,
    vus: int,
    duration: int,
    engine: str = "http",
    request_body: str | None = None,
    headers: str | None = None,
    query_params: str | None = None,
    request_delay: float | None = None,
    ramp_up: int = 0,
    iterations: int | None = None,
    body_preview_size: int = 500,
    vu_url_suffix: bool = False,
    vu_start: int = 1,
    error_page_rules: str | None = None,
    error_page_pattern: str | None = None,
    error_page_match_mode: str = "contains",
    http_scenario: str | None = None,
    browser_actions: str | None = None,
    tags: list[str] | None = None,
) -> PerformanceTest:
    engine_val = "browser" if (engine or "").strip().lower() == "browser" else "http"
    t = PerformanceTest(
        id=str(uuid.uuid4()),
        name=name,
        engine=engine_val,
        target_url=target_url,
        query_params=query_params,
        http_method=http_method,
        request_body=request_body,
        headers=headers,
        vus=vus,
        duration=duration,
        request_delay=request_delay,
        ramp_up=ramp_up,
        iterations=iterations,
        body_preview_size=body_preview_size,
        vu_url_suffix=vu_url_suffix,
        vu_start=max(1, int(vu_start or 1)),
        error_page_rules=error_page_rules,
        error_page_pattern=error_page_pattern,
        error_page_match_mode=(error_page_match_mode if error_page_match_mode in ("contains", "not_contains") else "contains"),
        http_scenario=http_scenario,
        browser_actions=browser_actions,
    )
    db.add(t)
    db.flush()
    _sync_tags_to_test(db, t, tags or [])
    db.commit()
    db.refresh(t)
    return t


def get(db: Session, id: str) -> PerformanceTest | None:
    stmt = (
        select(PerformanceTest)
        .options(selectinload(PerformanceTest.tags))
        .where(PerformanceTest.id == id)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_all_tag_names(db: Session) -> list[str]:
    """등록된 태그 이름 전체(가나다·abc 순)."""
    stmt = select(Tag.name).order_by(Tag.name)
    return list(db.execute(stmt).scalars().all())


def list_all(db: Session, tag: str | None = None) -> list[PerformanceTest]:
    needle = (tag or "").strip()
    stmt = select(PerformanceTest).options(selectinload(PerformanceTest.tags)).order_by(
        PerformanceTest.created_at.desc()
    )
    if needle:
        stmt = (
            select(PerformanceTest)
            .join(PerformanceTest.tags)
            .where(Tag.name == needle)
            .options(selectinload(PerformanceTest.tags))
            .order_by(PerformanceTest.created_at.desc())
        )
    return list(db.execute(stmt).scalars().all())


def update(
    db: Session,
    t: PerformanceTest,
    *,
    name: str | None = None,
    target_url: str | None = None,
    query_params: str | None = None,
    http_method: str | None = None,
    request_body: str | None = None,
    headers: str | None = None,
    vus: int | None = None,
    duration: int | None = None,
    engine: str | None = None,
    request_delay: float | None = None,
    ramp_up: int | None = None,
    iterations: int | None = None,
    body_preview_size: int | None = None,
    vu_url_suffix: bool | None = None,
    vu_start: int | None = None,
    error_rules: Any = ERROR_RULES_UNCHANGED,
    http_scenario: Any = HTTP_SCENARIO_UNCHANGED,
    browser_actions: Any = BROWSER_ACTIONS_UNCHANGED,
    tags: Any = TAGS_UNCHANGED,
) -> PerformanceTest:
    if name is not None:
        t.name = name
    if target_url is not None:
        t.target_url = target_url
    if engine is not None:
        t.engine = "browser" if (engine or "").strip().lower() == "browser" else "http"
    if query_params is not None:
        t.query_params = query_params
    if http_method is not None:
        t.http_method = http_method
    if request_body is not None:
        t.request_body = request_body
    if headers is not None:
        t.headers = headers
    if vus is not None:
        t.vus = vus
    if duration is not None:
        t.duration = duration
    if request_delay is not None:
        t.request_delay = request_delay
    if ramp_up is not None:
        t.ramp_up = ramp_up
    # None 허용: 반복 횟수 비움(제한 시간만 사용)으로 업데이트 가능하도록
    t.iterations = iterations
    if body_preview_size is not None:
        t.body_preview_size = body_preview_size
    if vu_url_suffix is not None:
        t.vu_url_suffix = vu_url_suffix
    if vu_start is not None:
        t.vu_start = max(1, int(vu_start))
    if error_rules is not ERROR_RULES_UNCHANGED:
        r_json, r_pat, r_mode = error_rules
        t.error_page_rules = r_json
        t.error_page_pattern = r_pat
        t.error_page_match_mode = r_mode if r_mode in ("contains", "not_contains") else "contains"
    if http_scenario is not HTTP_SCENARIO_UNCHANGED:
        t.http_scenario = http_scenario
    if browser_actions is not BROWSER_ACTIONS_UNCHANGED:
        t.browser_actions = browser_actions
    if tags is not TAGS_UNCHANGED:
        _sync_tags_to_test(db, t, tags)
    db.commit()
    db.refresh(t)
    return t


def delete(db: Session, t: PerformanceTest) -> None:
    db.delete(t)
    db.commit()
