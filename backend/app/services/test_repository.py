"""Performance Test CRUD."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db import PerformanceTest


def create(
    db: Session,
    *,
    name: str,
    target_url: str,
    http_method: str,
    vus: int,
    duration: int,
    request_body: str | None = None,
    headers: str | None = None,
    query_params: str | None = None,
    request_delay: float | None = None,
    ramp_up: int = 0,
    iterations: int | None = None,
) -> PerformanceTest:
    t = PerformanceTest(
        id=str(uuid.uuid4()),
        name=name,
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
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def get(db: Session, id: str) -> PerformanceTest | None:
    return db.get(PerformanceTest, id)


def list_all(db: Session) -> list[PerformanceTest]:
    stmt = select(PerformanceTest).order_by(PerformanceTest.created_at.desc())
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
    request_delay: float | None = None,
    ramp_up: int | None = None,
    iterations: int | None = None,
) -> PerformanceTest:
    if name is not None:
        t.name = name
    if target_url is not None:
        t.target_url = target_url
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
    if iterations is not None:
        t.iterations = iterations
    db.commit()
    db.refresh(t)
    return t


def delete(db: Session, t: PerformanceTest) -> None:
    db.delete(t)
    db.commit()
