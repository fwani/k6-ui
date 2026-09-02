"""테스트 CRUD API: POST/GET/PUT/DELETE /tests."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.test import (
    TestCreate,
    TestResponse,
    TestUpdate,
    browser_actions_to_json,
    scenario_steps_to_json,
)
from app.database import get_db
from app.models.db import PerformanceTest
from app.services import test_repository
from app.services.error_page_rules import (
    resolve_error_rules_for_update,
    serialize_error_rules_for_db,
)
from app.services.test_repository import (
    BROWSER_ACTIONS_UNCHANGED,
    DB_FIELD_UNCHANGED,
    HTTP_SCENARIO_UNCHANGED,
    TAGS_UNCHANGED,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tests", tags=["tests"])


def _to_response(orm: PerformanceTest) -> dict:
    # mode='json': datetime 등 JSON 직렬화 가능한 형태로 통일
    return TestResponse.model_validate(orm).model_dump(by_alias=True, mode="json")


@router.post("", response_model=dict, status_code=201)
def create_test(body: TestCreate, db: Session = Depends(get_db)):
    """POST /tests. 400 on validation (URL format, required)."""
    scenario_json = scenario_steps_to_json(body.http_scenario) if body.http_scenario else None
    browser_json = browser_actions_to_json(body.browser_actions)
    er_json, er_pat, er_mode = serialize_error_rules_for_db(body.error_page_rules or [])
    t = test_repository.create(
        db,
        name=body.name,
        target_url=body.target_url,
        query_params=body.query_params,
        http_method=body.http_method,
        request_body=body.request_body,
        headers=body.headers,
        vus=body.vus,
        duration=body.duration,
        engine=getattr(body, "engine", None) or "http",
        request_delay=body.request_delay,
        ramp_up=body.ramp_up,
        iterations=body.iterations,
        body_preview_size=body.body_preview_size,
        vu_url_suffix=body.vu_url_suffix,
        vu_start=body.vu_start,
        error_page_rules=er_json,
        error_page_pattern=er_pat,
        error_page_match_mode=er_mode,
        http_scenario=scenario_json,
        browser_actions=browser_json,
        db_driver=body.db_driver,
        db_query=body.db_query,
        tags=body.tags,
    )
    logger.info("test_created test_id=%s name=%s", t.id, t.name)
    return _to_response(t)


@router.get("", response_model=dict)
def list_tests(tag: str | None = None, db: Session = Depends(get_db)):
    """GET /tests → { items: [ Test ] }. 선택 쿼리 tag= 로 해당 태그가 정확히 포함된 테스트만."""
    items = test_repository.list_all(db, tag=tag)
    return {"items": [_to_response(x) for x in items]}


@router.get("/tags", response_model=dict)
def list_test_tags(db: Session = Depends(get_db)):
    """GET /tests/tags → { items: [ str ] }. DB에 있는 태그 이름 목록(자동완성용)."""
    names = test_repository.list_all_tag_names(db)
    return {"items": names}


@router.get("/{id}", response_model=dict)
def get_test(id: str, db: Session = Depends(get_db)):
    """GET /tests/:id. 404 if not found."""
    t = test_repository.get(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="테스트를 찾을 수 없습니다.")
    return _to_response(t)


@router.put("/{id}", response_model=dict)
def update_test(id: str, body: TestUpdate, db: Session = Depends(get_db)):
    """PUT /tests/:id. 404 if not found."""
    t = test_repository.get(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="테스트를 찾을 수 없습니다.")
    patch = body.model_dump(exclude_unset=True)
    new_engine = (body.engine if body.engine is not None else t.engine or "http").strip().lower()
    if new_engine in ("browser", "db"):
        http_scenario_kw: object | str | None = None
    elif "http_scenario" in patch:
        http_scenario_kw = (
            scenario_steps_to_json(body.http_scenario) if body.http_scenario else None
        )
    else:
        http_scenario_kw = HTTP_SCENARIO_UNCHANGED
    if new_engine in ("http", "db"):
        browser_actions_kw: object | str | None = None
    elif "browser_actions" in patch:
        browser_actions_kw = browser_actions_to_json(body.browser_actions)
    else:
        browser_actions_kw = BROWSER_ACTIONS_UNCHANGED
    if new_engine == "db":
        db_driver_kw: object | str | None = (
            (body.db_driver or "postgres").strip().lower() if "db_driver" in patch or body.db_driver else "postgres"
        )
        db_query_kw: object | str | None = body.db_query if "db_query" in patch else DB_FIELD_UNCHANGED
    else:
        # db 엔진이 아니면 db 전용 필드 비움
        db_driver_kw = None
        db_query_kw = None
    target_kw = body.target_url
    method_kw = body.http_method
    if "http_scenario" in patch and body.http_scenario:
        target_kw = body.http_scenario[0].url.strip()
        method_kw = body.http_scenario[0].method
    error_rules_kw = resolve_error_rules_for_update(body, t)
    tags_kw: object = TAGS_UNCHANGED
    if "tags" in patch:
        tags_kw = body.tags
    test_repository.update(
        db,
        t,
        name=body.name,
        target_url=target_kw,
        query_params=body.query_params,
        http_method=method_kw,
        request_body=body.request_body,
        headers=body.headers,
        vus=body.vus,
        duration=body.duration,
        engine=body.engine,
        request_delay=body.request_delay,
        ramp_up=body.ramp_up,
        iterations=body.iterations,
        body_preview_size=body.body_preview_size,
        vu_url_suffix=body.vu_url_suffix,
        vu_start=body.vu_start,
        error_rules=error_rules_kw,
        http_scenario=http_scenario_kw,
        browser_actions=browser_actions_kw,
        db_driver=db_driver_kw,
        db_query=db_query_kw,
        tags=tags_kw,
    )
    return _to_response(t)


@router.delete("/{id}", status_code=204)
def delete_test(id: str, db: Session = Depends(get_db)):
    """DELETE /tests/:id. 404 if not found."""
    t = test_repository.get(db, id)
    if not t:
        raise HTTPException(status_code=404, detail="테스트를 찾을 수 없습니다.")
    test_repository.delete(db, t)
    return None
