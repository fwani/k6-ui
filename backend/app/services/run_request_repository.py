"""Run 요청별 응답 CRUD. bulk_create, get_by_run_id."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db import RunRequestResponse


def bulk_create(
    db: Session,
    *,
    run_id: str,
    rows: list[dict],
) -> list[RunRequestResponse]:
    """rows: [{status_code, response_time_ms, body_preview, requested_at, request_args?, screenshot?, failed?}, ...]. seq는 1부터 부여."""
    if not rows:
        return []
    entities = []
    for seq, row in enumerate(rows, start=1):
        status_code = row.get("status_code")
        response_time_ms = row.get("response_time_ms")
        body_preview = row.get("body_preview")
        requested_at = row.get("requested_at")
        request_args = row.get("request_args")
        screenshot = row.get("screenshot")  # bytes | None
        failed = row.get("failed")  # bool | None
        entities.append(
            RunRequestResponse(
                id=str(uuid.uuid4()),
                run_id=run_id,
                seq=seq,
                status_code=status_code,
                response_time_ms=response_time_ms,
                body_preview=body_preview,
                requested_at=requested_at,
                request_args=request_args,
                screenshot=screenshot,
                failed=failed,
            )
        )
    db.add_all(entities)
    db.commit()
    for e in entities:
        db.refresh(e)
    return entities


def get_by_run_id(
    db: Session,
    run_id: str,
    limit: int = 1000,
    offset: int = 0,
) -> tuple[list[RunRequestResponse], int]:
    """run_id에 해당하는 요청 목록(seq 순)과 전체 개수. (items, total)."""
    count_stmt = select(func.count()).select_from(RunRequestResponse).where(RunRequestResponse.run_id == run_id)
    total = db.execute(count_stmt).scalar() or 0
    stmt = (
        select(RunRequestResponse)
        .where(RunRequestResponse.run_id == run_id)
        .order_by(RunRequestResponse.seq)
        .offset(offset)
        .limit(limit)
    )
    items = list(db.execute(stmt).scalars().all())
    return items, int(total)


def get_screenshot(db: Session, run_id: str, seq: int) -> bytes | None:
    """run_id, seq(1-based)에 해당하는 row의 screenshot 바이트 반환. 없으면 None."""
    stmt = (
        select(RunRequestResponse.screenshot)
        .where(RunRequestResponse.run_id == run_id, RunRequestResponse.seq == seq)
    )
    return db.execute(stmt).scalar_one_or_none()
