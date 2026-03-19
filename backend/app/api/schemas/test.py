"""Pydantic 스키마: Test 생성/수정/응답. API는 camelCase."""

from datetime import datetime

import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class TestCreate(BaseModel):
    """POST /tests 요청. JSON camelCase → snake_case."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1)
    engine: str = Field("http", alias="engine")  # http=k6, browser=Playwright
    target_url: str = Field(..., alias="targetUrl")  # base URL (no query)
    query_params: str | None = Field(None, alias="queryParams")  # JSON array [{"key":"k","value":"v"},...]
    http_method: str = Field(..., alias="httpMethod")
    request_body: str | None = Field(None, alias="requestBody")
    headers: str | None = Field(None, alias="headers")
    vus: int = Field(..., gt=0, alias="vus")
    duration: int = Field(..., gt=0, alias="duration")
    request_delay: float | None = Field(None, ge=0, alias="requestDelay")
    ramp_up: int = Field(0, ge=0, alias="rampUp")
    iterations: int | None = Field(None, gt=0, alias="iterations")
    body_preview_size: int = Field(500, ge=0, le=10000, alias="bodyPreviewSize")
    vu_url_suffix: bool = Field(False, alias="vuUrlSuffix")
    error_page_pattern: str | None = Field(None, alias="errorPagePattern")
    error_page_match_mode: str = Field("contains", alias="errorPageMatchMode")  # contains=포함 시 실패, not_contains=미포함 시 실패

    @field_validator("target_url")
    @classmethod
    def target_url_format(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("대상 URL을 입력하세요.")
        if not re.match(r"^https?://[^\s]+$", v):
            raise ValueError("유효한 URL 형식이 아닙니다. (예: https://example.com)")
        return v


class TestUpdate(BaseModel):
    """PUT /tests/:id 요청. 부분 수정."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(None, min_length=1)
    engine: str | None = Field(None, alias="engine")
    target_url: str | None = Field(None, alias="targetUrl")
    query_params: str | None = Field(None, alias="queryParams")
    http_method: str | None = Field(None, alias="httpMethod")
    request_body: str | None = Field(None, alias="requestBody")
    headers: str | None = Field(None, alias="headers")
    vus: int | None = Field(None, gt=0, alias="vus")
    duration: int | None = Field(None, gt=0, alias="duration")
    request_delay: float | None = Field(None, ge=0, alias="requestDelay")
    ramp_up: int | None = Field(None, ge=0, alias="rampUp")
    iterations: int | None = Field(None, gt=0, alias="iterations")
    body_preview_size: int | None = Field(None, ge=0, le=10000, alias="bodyPreviewSize")
    vu_url_suffix: bool | None = Field(None, alias="vuUrlSuffix")
    error_page_pattern: str | None = Field(None, alias="errorPagePattern")
    error_page_match_mode: str | None = Field(None, alias="errorPageMatchMode")


class TestResponse(BaseModel):
    """GET/POST/PUT 응답. from_attributes로 ORM 로드, by_alias=True 시 camelCase 출력."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str
    name: str
    engine: str = Field("http", alias="engine")
    target_url: str = Field(alias="targetUrl")
    query_params: str | None = Field(None, alias="queryParams")
    http_method: str = Field(alias="httpMethod")
    request_body: str | None = Field(None, alias="requestBody")
    headers: str | None = Field(None, alias="headers")
    vus: int
    duration: int
    request_delay: float | None = Field(None, alias="requestDelay")
    ramp_up: int = Field(alias="rampUp")
    iterations: int | None = Field(None, alias="iterations")
    body_preview_size: int = Field(500, alias="bodyPreviewSize")
    vu_url_suffix: bool = Field(False, alias="vuUrlSuffix")
    error_page_pattern: str | None = Field(None, alias="errorPagePattern")
    error_page_match_mode: str = Field("contains", alias="errorPageMatchMode")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
