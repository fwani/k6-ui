"""Pydantic 스키마: Result 응답. API는 camelCase."""

from pydantic import BaseModel, ConfigDict, Field


class ResultResponse(BaseModel):
    """GET /runs/:runId/result 응답."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    run_id: str = Field(alias="runId")
    avg_response_time: float = Field(alias="avgResponseTime")
    max_response_time: float = Field(alias="maxResponseTime")
    failure_rate: float = Field(alias="failureRate")
    request_count: int = Field(alias="requestCount")
    tps_or_rps: float = Field(alias="tpsOrRps")
    execution_time: float = Field(alias="executionTime")
    error_message: str | None = Field(None, alias="errorMessage")  # 실패 사유 (k6 stderr 등)
