"""Test Result CRUD. Run 1:1."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db import TestResult


def create(
    db: Session,
    *,
    run_id: str,
    avg_response_time: float,
    max_response_time: float,
    failure_rate: float,
    request_count: int,
    tps_or_rps: float,
    execution_time: float,
    error_message: str | None = None,
    lcp_ms: float | None = None,
    fcp_ms: float | None = None,
    cls: float | None = None,
    ttfb_ms: float | None = None,
) -> TestResult:
    r = TestResult(
        id=str(uuid.uuid4()),
        run_id=run_id,
        avg_response_time=avg_response_time,
        max_response_time=max_response_time,
        failure_rate=failure_rate,
        request_count=request_count,
        tps_or_rps=tps_or_rps,
        execution_time=execution_time,
        error_message=error_message,
        lcp_ms=lcp_ms,
        fcp_ms=fcp_ms,
        cls=cls,
        ttfb_ms=ttfb_ms,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_by_run_id(db: Session, run_id: str) -> "TestResult | None":
    stmt = select(TestResult).where(TestResult.run_id == run_id).limit(1)
    return db.execute(stmt).scalars().first()
