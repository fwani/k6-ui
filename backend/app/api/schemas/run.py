"""Pydantic 스키마: Run 응답. API는 camelCase."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResultSummaryResponse(BaseModel):
    """RunSummary 내 resultSummary (요약 필드 일부)."""

    model_config = ConfigDict(populate_by_name=True)

    avg_response_time: float = Field(alias="avgResponseTime")
    failure_rate: float = Field(alias="failureRate")


class RunSummaryResponse(BaseModel):
    """GET /runs 목록 항목."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    test_id: str = Field(alias="testId")
    test_name: str = Field(alias="testName")
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
    status: str  # Ready | Running | Finished | Failed
    started_at: datetime | None = Field(None, alias="startedAt")
    finished_at: datetime | None = Field(None, alias="finishedAt")
    created_at: datetime = Field(alias="createdAt")
