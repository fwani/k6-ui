"""Pydantic 스키마: Result 응답. API는 camelCase."""

from pydantic import BaseModel, ConfigDict, Field


class StepSummaryResponse(BaseModel):
    """시나리오 스텝별 요청 행 집계 (GET /runs/:id/result 에 포함)."""

    model_config = ConfigDict(populate_by_name=True)

    step_index: int = Field(alias="stepIndex")
    step_name: str | None = Field(None, alias="stepName")
    request_count: int = Field(alias="requestCount")
    avg_response_time: float = Field(alias="avgResponseTime")
    max_response_time: float = Field(alias="maxResponseTime")
    failure_rate: float = Field(alias="failureRate")
    tps_or_rps: float = Field(alias="tpsOrRps")


class ResultResponse(BaseModel):
    """GET /runs/:runId/result 응답."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    run_id: str = Field(alias="runId")
    avg_response_time: float = Field(alias="avgResponseTime")
    max_response_time: float = Field(alias="maxResponseTime")
    failure_rate: float = Field(alias="failureRate")
    overall_failure_rate: float = Field(alias="overallFailureRate")
    request_count: int = Field(alias="requestCount")
    tps_or_rps: float = Field(alias="tpsOrRps")
    execution_time: float = Field(alias="executionTime")
    error_message: str | None = Field(None, alias="errorMessage")  # 실패 사유 (k6 stderr 등)
    lcp_ms: float | None = Field(None, alias="lcpMs")
    fcp_ms: float | None = Field(None, alias="fcpMs")
    cls: float | None = Field(None, alias="cls")
    ttfb_ms: float | None = Field(None, alias="ttfbMs")
    # 연결된 테스트 정의 값(ORM에 없음). GET /runs/:id/result 에서 run.test 기준으로 채움.
    body_preview_size: int | None = Field(None, alias="bodyPreviewSize")
    step_summaries: list[StepSummaryResponse] | None = Field(None, alias="stepSummaries")
