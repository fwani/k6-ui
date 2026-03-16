"""테스트 CRUD API: POST/GET/PUT/DELETE /tests."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.test import TestCreate, TestResponse, TestUpdate
from app.database import get_db
from app.models.db import PerformanceTest
from app.services import test_repository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tests", tags=["tests"])


def _to_response(orm: PerformanceTest) -> dict:
    return TestResponse.model_validate(orm).model_dump(by_alias=True)


@router.post("", response_model=dict, status_code=201)
def create_test(body: TestCreate, db: Session = Depends(get_db)):
    """POST /tests. 400 on validation (URL format, required)."""
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
        request_delay=body.request_delay,
        ramp_up=body.ramp_up,
        iterations=body.iterations,
    )
    logger.info("test_created test_id=%s name=%s", t.id, t.name)
    return _to_response(t)


@router.get("", response_model=dict)
def list_tests(db: Session = Depends(get_db)):
    """GET /tests → { items: [ Test ] }."""
    items = test_repository.list_all(db)
    return {"items": [_to_response(x) for x in items]}


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
    test_repository.update(
        db,
        t,
        name=body.name,
        target_url=body.target_url,
        query_params=body.query_params,
        http_method=body.http_method,
        request_body=body.request_body,
        headers=body.headers,
        vus=body.vus,
        duration=body.duration,
        request_delay=body.request_delay,
        ramp_up=body.ramp_up,
        iterations=body.iterations,
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
