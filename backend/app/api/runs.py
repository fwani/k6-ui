"""테스트 실행 API: POST /tests/:testId/runs, POST /runs/:runId/stop, GET /runs/:runId."""

import logging
import re
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.schemas.result import ResultResponse
from app.api.schemas.run import (
    ResultSummaryResponse,
    RunResponse,
    RunSummaryResponse,
    StartRunRequest,
)
from app.api.schemas.run_request import RunRequestResponseResponse
from app.database import SessionLocal, get_db
from app.models.db import TestRun
from app.services import (
    browser_runner,
    k6_runner,
    result_repository,
    run_repository,
    run_request_repository,
    test_repository,
)
from app.services.browser_runner import BrowserNotFoundError
from app.services.k6_runner import K6NotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["runs"])


def _to_response(orm: TestRun) -> dict:
    return RunResponse.model_validate(orm).model_dump(by_alias=True)


def _on_run_complete(
    run_id: str,
    exit_code: int,
    summary: dict | None = None,
    error_output: str | None = None,
    *,
    request_responses: list[dict] | None = None,
) -> None:
    """k6 프로세스 종료 시 Run 상태 갱신, 결과 저장, 요청별 응답 bulk 저장."""
    db = SessionLocal()
    try:
        r = run_repository.get(db, run_id)
        if r and r.status == "Running":
            finished_at = datetime.utcnow()
            status = "Finished" if exit_code == 0 else "Failed"
            run_repository.update_status(
                db, r, status=status, finished_at=finished_at
            )
            exec_sec = 0.0
            if r.started_at and finished_at:
                exec_sec = max(0, (finished_at - r.started_at).total_seconds())
            err_msg = (error_output or "").strip()[:8000] or None
            if status == "Failed" and not err_msg:
                err_msg = f"프로세스가 비정상 종료했습니다 (exit code: {exit_code}). 사용자 중지 또는 k6 오류일 수 있습니다."
            if summary:
                result_repository.create(
                    db,
                    run_id=run_id,
                    avg_response_time=summary["avg_response_time"],
                    max_response_time=summary["max_response_time"],
                    failure_rate=summary["failure_rate"],
                    request_count=summary["request_count"],
                    tps_or_rps=summary["tps_or_rps"],
                    execution_time=summary["execution_time"],
                    error_message=err_msg,
                    lcp_ms=summary.get("lcp_ms"),
                    fcp_ms=summary.get("fcp_ms"),
                    cls=summary.get("cls"),
                    ttfb_ms=summary.get("ttfb_ms"),
                )
            else:
                result_repository.create(
                    db,
                    run_id=run_id,
                    avg_response_time=0.0,
                    max_response_time=0.0,
                    failure_rate=0.0,
                    request_count=0,
                    tps_or_rps=0.0,
                    execution_time=exec_sec,
                    error_message=err_msg,
                )
            if request_responses:
                run_request_repository.bulk_create(db, run_id=run_id, rows=request_responses)
    finally:
        db.close()


@router.post("/tests/{test_id}/runs", response_model=dict, status_code=201)
def start_run(
    test_id: str,
    body: StartRunRequest | None = Body(None),
    db: Session = Depends(get_db),
):
    """POST /tests/:testId/runs. 테스트에 저장된 engine(http|browser) 사용. 400 if another run running."""
    test = test_repository.get(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="테스트를 찾을 수 없습니다.")
    engine = (getattr(test, "engine", None) or "http").strip().lower()
    if engine not in ("http", "browser"):
        engine = "http"
    running = run_repository.get_running(db)
    if running:
        raise HTTPException(
            status_code=400,
            detail="이미 실행 중인 테스트가 있습니다. 먼저 중지하세요.",
        )
    run = run_repository.create(db, test_id=test_id, engine=engine)
    run_repository.update_status(
        db, run, status="Running", started_at=datetime.utcnow()
    )
    logger.info("run_started run_id=%s test_id=%s engine=%s", run.id, test_id, engine)
    test = test_repository.get(db, test_id)
    if not test:
        run_repository.update_status(
            db, run, status="Failed", finished_at=datetime.utcnow()
        )
        raise HTTPException(status_code=404, detail="테스트를 찾을 수 없습니다.")
    try:
        if engine == "browser":
            browser_runner.start(run.id, test, on_complete=_on_run_complete)
        else:
            k6_runner.start(run.id, test, on_complete=_on_run_complete)
    except (K6NotFoundError, BrowserNotFoundError) as e:
        run_repository.update_status(
            db, run, status="Failed", finished_at=datetime.utcnow()
        )
        raise HTTPException(status_code=503, detail=str(e))
    return _to_response(run)


@router.post("/runs/{run_id}/stop", response_model=dict)
def stop_run(run_id: str, db: Session = Depends(get_db)):
    """POST /runs/:runId/stop. Run 상태를 Failed로 설정하고 k6 중지."""
    run = run_repository.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    if run.status == "Running":
        if getattr(run, "engine", "http") == "browser":
            browser_runner.stop(run_id)
        else:
            k6_runner.stop(run_id)
        run_repository.update_status(
            db, run, status="Failed", finished_at=datetime.utcnow()
        )
        logger.info("run_stopped run_id=%s", run_id)
    return _to_response(run)


@router.get("/runs", response_model=dict)
def list_runs(
    db: Session = Depends(get_db),
    page: int = 1,
    limit: int = 20,
    test_id: str | None = None,
):
    """GET /runs. page, limit, testId(선택). { items: RunSummary[] }."""
    runs = run_repository.list_with_summary(db, page=page, limit=limit, test_id=test_id)
    items = []
    for r in runs:
        result_summary = None
        if r.result:
            result_summary = ResultSummaryResponse(
                avg_response_time=r.result.avg_response_time,
                failure_rate=r.result.failure_rate,
            )
        items.append(
            RunSummaryResponse(
                id=r.id,
                test_id=r.test_id,
                test_name=r.test.name,
                engine=getattr(r, "engine", "http"),
                status=r.status,
                started_at=r.started_at,
                finished_at=r.finished_at,
                created_at=r.created_at,
                result_summary=result_summary,
            )
        )
    return {"items": [x.model_dump(by_alias=True) for x in items]}


@router.get("/runs/{run_id}", response_model=dict)
def get_run(run_id: str, db: Session = Depends(get_db)):
    """GET /runs/:runId. Run id, testId, testName, status, startedAt, finishedAt, createdAt."""
    run = run_repository.get_with_test(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    out = _to_response(run)
    if run.test:
        out["testName"] = run.test.name
    return out


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(run_id: str, db: Session = Depends(get_db)):
    """DELETE /runs/:runId. Running이면 400."""
    run = run_repository.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    if run.status == "Running":
        raise HTTPException(
            status_code=400,
            detail="실행 중인 Run은 중지 후 삭제하세요.",
        )
    run_repository.delete(db, run)
    return None


@router.get("/runs/{run_id}/logs", response_model=dict)
def get_run_logs(run_id: str, db: Session = Depends(get_db)):
    """GET /runs/:runId/logs. k6 또는 브라우저 러너 로그."""
    run = run_repository.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    if getattr(run, "engine", "http") == "browser":
        lines = browser_runner.get_logs(run_id)
    else:
        lines = k6_runner.get_logs(run_id)
    return {"log": "\n".join(lines) if lines else ""}


@router.get("/runs/{run_id}/requests", response_model=dict)
def get_run_requests(
    run_id: str,
    db: Session = Depends(get_db),
    limit: int = 1000,
    offset: int = 0,
):
    """GET /runs/:runId/requests. 요청별 응답 목록(페이지네이션)."""
    run = run_repository.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    items, total = run_request_repository.get_by_run_id(db, run_id=run_id, limit=limit, offset=offset)
    return {
        "items": [RunRequestResponseResponse.model_validate(x).model_dump(by_alias=True) for x in items],
        "total": total,
    }


@router.get("/runs/{run_id}/result", response_model=dict)
def get_run_result(run_id: str, db: Session = Depends(get_db)):
    """GET /runs/:runId/result. 404 if run or result not found."""
    run = run_repository.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    result = result_repository.get_by_run_id(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="결과가 아직 없습니다.")
    logger.info("result_read run_id=%s", run_id)
    return ResultResponse.model_validate(result).model_dump(by_alias=True)


_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


@router.get("/runs/{run_id}/screenshots/{vu_index}")
def get_run_screenshot(
    run_id: str,
    vu_index: int,
    db: Session = Depends(get_db),
):
    """GET /runs/:runId/screenshots/:vuIndex. run_request_response에 저장된 스크린샷(JPEG) 반환. 404 if not found."""
    if not _UUID_RE.match(run_id) or vu_index < 0:
        raise HTTPException(status_code=404, detail="스크린샷을 찾을 수 없습니다.")
    seq = vu_index + 1
    data = run_request_repository.get_screenshot(db, run_id=run_id, seq=seq)
    if not data:
        raise HTTPException(status_code=404, detail="스크린샷을 찾을 수 없습니다.")
    return Response(content=data, media_type="image/jpeg")
