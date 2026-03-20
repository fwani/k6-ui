"""Pydantic 스키마: Run 요청별 응답. API는 camelCase."""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer


def _format_utc_iso6(dt: datetime | None) -> str | None:
    """UTC 기준 ISO 8601, 초 이하 6자리. naive는 UTC로 간주."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    frac = f"{dt.microsecond:06d}"
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S.{frac}Z")


class RunRequestResponseResponse(BaseModel):
    """요청 1건 응답: seq, statusCode, responseTimeMs, bodyPreview(전체 본문), requestedAt, requestArgs."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    seq: int = Field(alias="seq")
    status_code: int | None = Field(None, alias="statusCode")
    response_time_ms: float | None = Field(None, alias="responseTimeMs")
    body_preview: str | None = Field(
        None,
        alias="bodyPreview",
        description="k6: 응답 본문 전체. browser: 페이지 innerText.",
    )
    requested_at: datetime | None = Field(None, alias="requestedAt")
    request_args: str | None = Field(None, alias="requestArgs")  # JSON: url, method, headers, body
    failed: bool | None = Field(None, alias="failed")  # 200이어도 에러 페이지 등으로 실패한 경우 true

    @field_serializer("requested_at")
    def serialize_requested_at(self, dt: datetime | None) -> str | None:
        return _format_utc_iso6(dt)
