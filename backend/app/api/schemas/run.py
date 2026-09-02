"""Pydantic 스키마: Run 요청/응답. API는 camelCase."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StartRunRequest(BaseModel):
    """POST /tests/:testId/runs 요청 body. engine 생략 시 http."""

    model_config = ConfigDict(populate_by_name=True)

    engine: str = Field("http", alias="engine")  # http | browser
    request_header_overrides: dict[str, str] | None = Field(
        None,
        alias="requestHeaderOverrides",
        description="실행 시에만 대상 요청 헤더에 합침. 테스트 저장 헤더보다 우선.",
    )
    show_browser: bool = Field(
        False,
        alias="showBrowser",
        description="engine=browser 일 때만: Chromium 창을 띄움(로컬 API·GUI 또는 DISPLAY/xvfb 필요).",
    )

    @field_validator("request_header_overrides", mode="before")
    @classmethod
    def coerce_request_header_overrides(cls, v: Any) -> dict[str, str] | None:
        if v is None:
            return None
        if not isinstance(v, dict):
            return None
        out: dict[str, str] = {}
        for k, val in v.items():
            key = str(k).strip()
            if not key:
                continue
            out[key] = "" if val is None else str(val)
        return out or None


class ResultSummaryResponse(BaseModel):
    """RunSummary 내 resultSummary (요약 필드 일부)."""

    model_config = ConfigDict(populate_by_name=True)

    avg_response_time: float = Field(alias="avgResponseTime")
    failure_rate: float = Field(alias="failureRate")
    overall_failure_rate: float = Field(alias="overallFailureRate")


class RunSummaryResponse(BaseModel):
    """GET /runs 목록 항목."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    test_id: str = Field(alias="testId")
    test_name: str = Field(alias="testName")
    engine: str = Field("http", alias="engine")
    status: str
    started_at: datetime | None = Field(None, alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    created_at: datetime = Field(alias="createdAt")
    result_summary: ResultSummaryResponse | None = Field(None, alias="resultSummary")


class RunResponse(BaseModel):
    """GET /runs/:id, POST /tests/:testId/runs, POST /runs/:id/stop 응답."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    test_id: str = Field(alias="testId")
    test_name: str | None = Field(None, alias="testName")
    engine: str = Field("http", alias="engine")
    status: str  # Ready | Running | Finished | Failed
    started_at: datetime | None = Field(None, alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    created_at: datetime = Field(alias="createdAt")
