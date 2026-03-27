"""Run 요청별 응답 CRUD. bulk_create, get_by_run_id."""

import uuid

from sqlalchemy import func, nullslast, select, text
from sqlalchemy.orm import Session

from app.models.db import RunRequestResponse

REQ_SORT_SEQ = "seq"
REQ_SORT_VU_TRACE = "vu_trace"


def normalize_requests_sort(sort: str | None) -> str:
    """API 쿼리: seq | vuTrace → 저장소 sort 키."""
    if sort is None or not str(sort).strip():
        return REQ_SORT_SEQ
    s = str(sort).strip().lower().replace("-", "_")
    if s in ("vu_trace", "vutrace"):
        return REQ_SORT_VU_TRACE
    return REQ_SORT_SEQ


def _order_clause_vu_trace():
    t = RunRequestResponse.__tablename__
    return (
        nullslast(text(f"CAST(json_extract({t}.request_args, '$.vu') AS INTEGER)")),
        nullslast(text(f"CAST(json_extract({t}.request_args, '$.scenarioIter') AS INTEGER)")),
        nullslast(text(f"CAST(json_extract({t}.request_args, '$.stepIndex') AS INTEGER)")),
        RunRequestResponse.seq,
    )


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
    *,
    sort: str = REQ_SORT_SEQ,
) -> tuple[list[RunRequestResponse], int]:
    """run_id에 해당하는 요청 목록과 전체 개수. sort: seq | vu_trace (VU·반복·스텝 순, SQLite json_extract)."""
    count_stmt = select(func.count()).select_from(RunRequestResponse).where(RunRequestResponse.run_id == run_id)
    total = db.execute(count_stmt).scalar() or 0
    order = _order_clause_vu_trace() if sort == REQ_SORT_VU_TRACE else (RunRequestResponse.seq,)
    stmt = (
        select(RunRequestResponse)
        .where(RunRequestResponse.run_id == run_id)
        .order_by(*order)
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


def aggregate_step_metrics(db: Session, run_id: str) -> list[dict]:
    """request_args.stepIndex 별 집계. SQLite json_extract 전용. stepIndex 없는 행은 제외.

    폴링 스텝(구버전): 요청마다 pollAttempt 가 찍혀 N건으로 집계되던 행은 제외하고, 스텝당 1건만 반영.
    신버전은 pollTotalAttempts 만 있는 단일 __REQ__ 행.

    행 실패 정의: failed(참) 또는 status_code가 2xx 아님 (runs._compute_overall_failure_rate 와 동일).
    """
    if getattr(db.bind, "dialect", None) is None or db.bind.dialect.name != "sqlite":
        return []
    t = RunRequestResponse.__tablename__
    sql = text(f"""
        SELECT
            CAST(json_extract(request_args, '$.stepIndex') AS INTEGER) AS step_index,
            MAX(json_extract(request_args, '$.step')) AS step_name,
            COUNT(*) AS request_count,
            COALESCE(AVG(response_time_ms), 0) AS avg_ms,
            COALESCE(MAX(response_time_ms), 0) AS max_ms,
            SUM(CASE
                WHEN COALESCE(failed, 0) != 0 THEN 1
                WHEN status_code IS NULL OR status_code < 200 OR status_code >= 300 THEN 1
                ELSE 0
            END) AS fail_count
        FROM {t}
        WHERE run_id = :run_id
          AND request_args IS NOT NULL
          AND trim(request_args) != ''
          AND json_extract(request_args, '$.stepIndex') IS NOT NULL
          AND NOT (
            json_extract(request_args, '$.poll') = 1
            AND json_type(request_args, '$.pollAttempt') IS NOT NULL
          )
        GROUP BY CAST(json_extract(request_args, '$.stepIndex') AS INTEGER)
        ORDER BY CAST(json_extract(request_args, '$.stepIndex') AS INTEGER)
    """)
    rows = db.execute(sql, {"run_id": run_id}).mappings().all()
    out: list[dict] = []
    for r in rows:
        si = r["step_index"]
        if si is None:
            continue
        n = int(r["request_count"] or 0)
        fn = int(r["fail_count"] or 0)
        out.append(
            {
                "step_index": int(si),
                "step_name": r["step_name"],
                "request_count": n,
                "avg_response_time": float(r["avg_ms"] or 0),
                "max_response_time": float(r["max_ms"] or 0),
                "failure_rate": (fn / n) if n else 0.0,
            }
        )
    return out
