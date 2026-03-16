"""테스트 실행 API: POST /tests/:testId/runs, POST /runs/:runId/stop, GET /runs/:runId."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.result import ResultResponse
from app.api.schemas.run import (
    ResultSummaryResponse,
    RunResponse,
    RunSummaryResponse,
)
from app.database import SessionLocal
from app.database import get_db
from app.models.db import PerformanceTest, TestRun
from app.services import k6_runner, result_repository, run_repository, test_repository
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
) -> None:
    """k6 프로세스 종료 시 Run 상태 갱신 및 결과 저장. 실패 시 error_output 저장."""
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
    finally:
        db.close()


@router.post("/tests/{test_id}/runs", response_model=dict, status_code=201)
def start_run(test_id: str, db: Session = Depends(get_db)):
    """POST /tests/:testId/runs. 400 if another run already Running."""
    test = test_repository.get(db, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="테스트를 찾을 수 없습니다.")
    running = run_repository.get_running(db)
    if running:
        raise HTTPException(
            status_code=400,
            detail="이미 실행 중인 테스트가 있습니다. 먼저 중지하세요.",
        )
    run = run_repository.create(db, test_id=test_id)
    run_repository.update_status(
        db, run, status="Running", started_at=datetime.utcnow()
    )
    logger.info("run_started run_id=%s test_id=%s", run.id, test_id)
    db.refresh(test)  # commit 후 세션 만료 방지, k6 스크립트에 인자 반영
    try:
        k6_runner.start(run.id, test, on_complete=_on_run_complete)
    except K6NotFoundError as e:
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
    """GET /runs/:runId. Run id, testId, status, startedAt, finishedAt, createdAt."""
    run = run_repository.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="실행을 찾을 수 없습니다.")
    return _to_response(run)


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
