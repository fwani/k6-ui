"""Test Run CRUD. 생성 시 Ready, 시작 시 Running."""

from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.db import TestRun


def create(db: Session, *, test_id: str) -> TestRun:
    r = TestRun(
        id=str(uuid.uuid4()),
        test_id=test_id,
        status="Ready",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get(db: Session, id: str) -> TestRun | None:
    return db.get(TestRun, id)


def get_running(db: Session) -> TestRun | None:
    """MVP: 동시에 하나만 Running 허용. Running인 Run이 있으면 반환."""
    stmt = select(TestRun).where(TestRun.status == "Running").limit(1)
    return db.execute(stmt).scalars().first()


def update_status(
    db: Session,
    r: TestRun,
    *,
    status: str,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> TestRun:
    r.status = status
    if started_at is not None:
        r.started_at = started_at
    if finished_at is not None:
        r.finished_at = finished_at
    db.commit()
    db.refresh(r)
    return r


def list_with_summary(
    db: Session,
    *,
    page: int = 1,
    limit: int = 20,
    test_id: str | None = None,
) -> list[TestRun]:
    """Run 목록 (test, result eager load). testId 필터, created_at 내림차순."""
    stmt = (
        select(TestRun)
        .options(
            joinedload(TestRun.test),
            joinedload(TestRun.result),
        )
        .order_by(TestRun.created_at.desc())
    )
    if test_id:
        stmt = stmt.where(TestRun.test_id == test_id)
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    return list(db.execute(stmt).scalars().unique().all())
