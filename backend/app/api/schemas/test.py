"""Pydantic 스키마: Test 생성/수정/응답. API는 camelCase."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.services.error_page_rules import serialize_error_rules_for_db

_VAR_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

_TAG_MAX_LEN = 32
_TAG_MAX_COUNT = 32

logger = logging.getLogger(__name__)


def normalize_tag_list(raw: list[str] | None) -> list[str]:
    """태그 trim, 빈 값 제거, 중복 제거(순서 유지), 길이·개수 상한."""
    if not raw:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for s in raw:
        t = (s or "").strip()[:_TAG_MAX_LEN]
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= _TAG_MAX_COUNT:
            break
    return out


class HttpScenarioQueryParam(BaseModel):
    """단계별 쿼리스트링 항목."""

    model_config = ConfigDict(populate_by_name=True)

    key: str
    value: str = ""


class HttpScenarioCapture(BaseModel):
    """응답 본문(JSON) 또는 응답 헤더에서 값 추출 (다음 단계 {{var}} 치환용)."""

    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field("json", alias="from")
    path: str | None = Field(None, description="from=json 일 때 JSON 점 경로")
    header: str | None = Field(None, description="from=header 일 때 응답 헤더 이름")
    cookie_name: str | None = Field(
        None,
        alias="cookieName",
        description="from=header 일 때 선택. Set-Cookie 등에서 이 쿠키 이름의 값만 추출(세미콜론 앞까지).",
    )
    var: str = Field(..., min_length=1)

    @field_validator("from_", mode="before")
    @classmethod
    def normalize_from(cls, v: str) -> str:
        s = (v or "json").strip().lower()
        if s not in ("json", "header"):
            raise ValueError('capture.from 은 "json" 또는 "header" 만 지원합니다.')
        return s

    @field_validator("path", mode="before")
    @classmethod
    def strip_path(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("header", mode="before")
    @classmethod
    def strip_header(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("cookie_name", mode="before")
    @classmethod
    def strip_cookie_name(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("var")
    @classmethod
    def var_name(cls, v: str) -> str:
        v = (v or "").strip()
        if v.upper() == "VU":
            raise ValueError('capture.var 에 "VU" 는 사용할 수 없습니다. ({{VU}} 예약)')
        if not _VAR_NAME_RE.match(v):
            raise ValueError("capture.var 은 영문/숫자/밑줄로 시작하는 식별자여야 합니다.")
        return v

    @model_validator(mode="after")
    def path_or_header_by_from(self) -> HttpScenarioCapture:
        if self.from_ == "json":
            if not self.path:
                raise ValueError("capture.path 는 from=json 일 때 필수입니다.")
        else:
            if not self.header:
                raise ValueError("capture.header 는 from=header 일 때 필수입니다.")
        if self.cookie_name and self.from_ != "header":
            raise ValueError("capture.cookieName 은 from=header 일 때만 사용할 수 있습니다.")
        return self


class HttpScenarioMultipart(BaseModel):
    """multipart/form-data: 파일 1파트(디스크 경로) + 텍스트 필드."""

    model_config = ConfigDict(populate_by_name=True)

    file_path: str = Field(..., alias="filePath", min_length=1)
    file_field: str = Field(
        ...,
        alias="fileField",
        min_length=1,
        description="파일이 붙는 폼 필드명",
    )
    filename: str | None = Field(
        None,
        description="Content-Disposition 파일명(비우면 upload.bin)",
    )
    content_type: str | None = Field(
        None,
        alias="contentType",
        description="파일 파트 MIME(비우면 application/octet-stream)",
    )
    fields: dict[str, str] = Field(
        default_factory=dict,
        description="파일 외 텍스트 파트(키=폼 이름)",
    )

    @field_validator("file_path", "file_field", mode="before")
    @classmethod
    def strip_required_paths(cls, v: object) -> str:
        if v is None:
            return ""
        return str(v).strip()

    @field_validator("filename", "content_type", mode="before")
    @classmethod
    def strip_optional_str(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("fields", mode="before")
    @classmethod
    def normalize_fields(cls, v: object) -> dict[str, str]:
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("multipart.fields 는 객체여야 합니다.")
        out: dict[str, str] = {}
        for k, val in v.items():
            key = str(k).strip()
            if not key:
                continue
            out[key] = "" if val is None else str(val)
        return out


class HttpScenarioPoll(BaseModel):
    """같은 요청을 간격마다 반복하다가 조건 만족 또는 최대 시간 초과."""

    model_config = ConfigDict(populate_by_name=True)

    interval_seconds: float = Field(
        ...,
        alias="intervalSeconds",
        ge=0.1,
        le=60,
        description="시도 사이 대기(초).",
    )
    max_duration_seconds: float = Field(
        ...,
        alias="maxDurationSeconds",
        ge=0.5,
        le=600,
        description="첫 시도 시각 기준 최대 대기(초).",
    )
    until_json_path: str | None = Field(
        None,
        alias="untilJsonPath",
        description="2xx 응답 JSON에서 점(.) 경로. untilEquals 와 함께 쓰면 값이 같을 때 성공.",
    )
    until_equals: str | None = Field(
        None,
        alias="untilEquals",
        description="untilJsonPath 값과 문자열 비교( trim 없이 String() 후 비교는 k6 쪽). {{VU}}·캡처 변수 치환.",
    )
    until_status_in: list[int] | None = Field(
        None,
        alias="untilStatusIn",
        description="HTTP status 가 목록에 있으면 성공. untilJsonPath 조건과 OR.",
    )
    while_json_path: str | None = Field(
        None,
        alias="whileJsonPath",
        description="2xx JSON에서 이 값이 whileEquals 와 같으면 재시도. until 성공 전에만 평가.",
    )
    while_equals: str | None = Field(
        None,
        alias="whileEquals",
        description="whileJsonPath 값과 문자열 비교. {{VU}}·캡처 변수 치환은 k6.",
    )

    @field_validator("until_json_path", mode="before")
    @classmethod
    def strip_until_path(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("until_equals", mode="before")
    @classmethod
    def coerce_until_equals(cls, v: object) -> str | None:
        if v is None:
            return None
        return str(v)

    @field_validator("until_status_in", mode="before")
    @classmethod
    def normalize_status_in(cls, v: object) -> list[int] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("poll.untilStatusIn 은 정수 배열이어야 합니다.")
        out: list[int] = []
        for x in v:
            try:
                out.append(int(x))
            except (TypeError, ValueError) as e:
                raise ValueError("poll.untilStatusIn 항목은 정수여야 합니다.") from e
        return out

    @field_validator("while_json_path", mode="before")
    @classmethod
    def strip_while_path(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("while_equals", mode="before")
    @classmethod
    def coerce_while_equals(cls, v: object) -> str | None:
        if v is None:
            return None
        return str(v)

    @model_validator(mode="after")
    def at_least_one_success_condition(self) -> HttpScenarioPoll:
        has_json = (self.until_json_path or "").strip() and self.until_equals is not None
        has_status = bool(self.until_status_in)
        if not has_json and not has_status:
            raise ValueError(
                "poll 은 untilJsonPath·untilEquals 쌍 또는 untilStatusIn 중 하나는 필요합니다."
            )
        if (self.until_json_path or "").strip() and self.until_equals is None:
            raise ValueError("untilJsonPath 가 있으면 untilEquals 가 필요합니다.")
        return self

    @model_validator(mode="after")
    def while_pair_consistent(self) -> HttpScenarioPoll:
        wp = (self.while_json_path or "").strip()
        if wp and self.while_equals is None:
            raise ValueError("whileJsonPath 가 있으면 whileEquals 가 필요합니다.")
        if self.while_equals is not None and not wp:
            raise ValueError("whileEquals 는 whileJsonPath 와 함께 사용해야 합니다.")
        return self


class ErrorPageRule(BaseModel):
    """에러 페이지 판별 한 줄. 여러 줄은 OR(하나라도 실패 조건이면 실패)."""

    model_config = ConfigDict(populate_by_name=True)

    pattern: str = ""
    match_mode: str = Field("contains", alias="matchMode")

    @field_validator("match_mode")
    @classmethod
    def match_mode_ok(cls, v: str) -> str:
        s = (v or "contains").strip()
        return s if s in ("contains", "not_contains") else "contains"


class HttpScenarioStep(BaseModel):
    """k6 다단계 시나리오의 한 단계."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    method: str
    url: str
    query_params: list[HttpScenarioQueryParam] | None = Field(None, alias="queryParams")
    headers: dict[str, str] | None = None
    body: str | None = None
    multipart: HttpScenarioMultipart | None = None
    capture: HttpScenarioCapture | None = None
    poll: HttpScenarioPoll | None = None
    sleep_after_seconds: float | None = Field(
        None,
        ge=0,
        le=600,
        alias="sleepAfterSeconds",
        description="이 스텝 요청·로그 후 다음 스텝 전까지 대기(초). 0/생략이면 스텝 간 대기 없음.",
    )
    error_page_rules: list[ErrorPageRule] | None = Field(
        None,
        alias="errorPageRules",
        description="스텝 전용 에러 판별. 유효한 규칙이 없으면 테스트 전역 규칙을 따름(k6).",
    )

    @field_validator("method")
    @classmethod
    def method_upper(cls, v: str) -> str:
        m = (v or "GET").strip().upper()
        if m not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            raise ValueError("지원 메서드: GET, POST, PUT, PATCH, DELETE")
        return m

    @field_validator("url")
    @classmethod
    def url_strip(cls, v: str) -> str:
        return (v or "").strip()

    @model_validator(mode="after")
    def multipart_vs_body_and_headers(self) -> HttpScenarioStep:
        if self.multipart is not None:
            if (self.body or "").strip():
                raise ValueError("multipart 가 있으면 body 는 비워야 합니다.")
            if self.method not in ("POST", "PUT", "PATCH"):
                raise ValueError("multipart 는 POST, PUT, PATCH 만 사용할 수 있습니다.")
            for hk in self.headers or {}:
                if str(hk).strip().lower() == "content-type":
                    raise ValueError(
                        "multipart 스텝에서는 Content-Type 헤더를 넣을 수 없습니다."
                    )
        return self


def scenario_steps_to_json(steps: list[HttpScenarioStep]) -> str:
    return json.dumps(
        [s.model_dump(mode="json", by_alias=True) for s in steps],
        ensure_ascii=False,
    )


class BrowserActionStep(BaseModel):
    """브라우저 로드 후 Playwright 단계 (wait_selector | click | sleep)."""

    model_config = ConfigDict(populate_by_name=True)

    kind: Literal["wait_selector", "click", "sleep"] = Field(
        ..., alias="type", description='wait_selector | click | sleep'
    )
    selector: str | None = None
    timeout_ms: int = Field(
        30_000,
        ge=1_000,
        le=60_000,
        alias="timeoutMs",
        description="wait_selector / click 대기(ms).",
    )
    sleep_ms: int | None = Field(
        None,
        ge=0,
        le=30_000,
        alias="sleepMs",
        description="type=sleep 일 때만(ms).",
    )

    @field_validator("selector", mode="before")
    @classmethod
    def strip_selector(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("kind", mode="before")
    @classmethod
    def normalize_kind(cls, v: object) -> str:
        s = (str(v) if v is not None else "").strip()
        if s not in ("wait_selector", "click", "sleep"):
            raise ValueError(
                'type 은 "wait_selector", "click", "sleep" 중 하나여야 합니다.'
            )
        return s

    @model_validator(mode="after")
    def selector_and_sleep(self) -> BrowserActionStep:
        if self.kind in ("wait_selector", "click"):
            if not self.selector:
                raise ValueError(f"type={self.kind} 일 때 selector 는 필수입니다.")
        else:
            if self.sleep_ms is None:
                raise ValueError("type=sleep 일 때 sleepMs 가 필요합니다.")
        return self


def browser_actions_to_json(steps: list[BrowserActionStep] | None) -> str | None:
    if not steps:
        return None
    return json.dumps(
        [s.model_dump(mode="json", by_alias=True) for s in steps],
        ensure_ascii=False,
    )


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
    body_preview_size: int = Field(
        500,
        ge=0,
        le=10000,
        alias="bodyPreviewSize",
        description="결과 화면 목록에서 응답 본문을 잘라 보여줄 글자 수. DB에는 전체 본문이 저장됩니다.",
    )
    vu_url_suffix: bool = Field(False, alias="vuUrlSuffix")
    vu_start: int = Field(1, ge=1, alias="vuStart")
    error_page_rules: list[ErrorPageRule] | None = Field(None, alias="errorPageRules")
    error_page_pattern: str | None = Field(None, alias="errorPagePattern")
    error_page_match_mode: str = Field("contains", alias="errorPageMatchMode")
    http_scenario: list[HttpScenarioStep] | None = Field(None, alias="httpScenario")
    browser_actions: list[BrowserActionStep] | None = Field(
        None, alias="browserActions"
    )
    tags: list[str] = Field(default_factory=list, alias="tags")

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags_create(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            return []
        return normalize_tag_list([str(x) for x in v])

    @staticmethod
    def _url_ok(u: str) -> bool:
        u = (u or "").strip()
        return bool(u) and bool(re.match(r"^https?://[^\s]+$", u))

    @model_validator(mode="after")
    def validate_scenario_or_single_url(self) -> TestCreate:
        steps = self.http_scenario
        if steps:
            if (self.engine or "http").strip().lower() == "browser":
                raise ValueError("브라우저 모드에서는 다단계 시나리오를 사용할 수 없습니다.")
            for i, s in enumerate(steps):
                if not self._url_ok(s.url):
                    raise ValueError(f"시나리오 {i + 1}단계 URL이 올바르지 않습니다.")
            first = steps[0]
            return self.model_copy(
                update={
                    "target_url": first.url.strip(),
                    "http_method": first.method,
                }
            )
        u = (self.target_url or "").strip()
        if not u:
            raise ValueError("대상 URL을 입력하세요.")
        if not self._url_ok(u):
            raise ValueError("유효한 URL 형식이 아닙니다. (예: https://example.com)")
        return self.model_copy(update={"target_url": u})

    @model_validator(mode="after")
    def normalize_error_page_rules(self) -> TestCreate:
        """errorPageRules 미전달 시 단일 errorPagePattern으로 보완. 전달 시 빈 pattern 행은 무시."""
        rules_in = self.error_page_rules
        if rules_in is None:
            pat = (self.error_page_pattern or "").strip()
            if pat:
                mode = (
                    "not_contains"
                    if (self.error_page_match_mode or "").strip() == "not_contains"
                    else "contains"
                )
                merged = [ErrorPageRule(pattern=pat, match_mode=mode)]
            else:
                merged = []
        else:
            merged = [r for r in rules_in if (r.pattern or "").strip()]
        _, first_pat, first_mode = serialize_error_rules_for_db(merged)
        return self.model_copy(
            update={
                "error_page_rules": merged,
                "error_page_pattern": first_pat,
                "error_page_match_mode": first_mode,
            }
        )

    @model_validator(mode="after")
    def normalize_browser_actions_for_engine(self) -> TestCreate:
        if (self.engine or "http").strip().lower() != "browser":
            return self.model_copy(update={"browser_actions": None})
        if not self.browser_actions:
            return self.model_copy(update={"browser_actions": None})
        return self


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
    body_preview_size: int | None = Field(
        None,
        ge=0,
        le=10000,
        alias="bodyPreviewSize",
        description="결과 화면 본문 표시 글자 수(저장 길이와 무관).",
    )
    vu_url_suffix: bool | None = Field(None, alias="vuUrlSuffix")
    vu_start: int | None = Field(None, ge=1, alias="vuStart")
    error_page_rules: list[ErrorPageRule] | None = Field(None, alias="errorPageRules")
    error_page_pattern: str | None = Field(None, alias="errorPagePattern")
    error_page_match_mode: str | None = Field(None, alias="errorPageMatchMode")
    http_scenario: list[HttpScenarioStep] | None = Field(None, alias="httpScenario")
    browser_actions: list[BrowserActionStep] | None = Field(
        None, alias="browserActions"
    )
    tags: list[str] | None = Field(None, alias="tags")

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags_update(cls, v: Any) -> list[str] | None:
        if v is None:
            return None
        if not isinstance(v, list):
            return []
        return normalize_tag_list([str(x) for x in v])

    @field_validator("target_url")
    @classmethod
    def target_url_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = (v or "").strip()
        if not v:
            raise ValueError("대상 URL을 입력하세요.")
        if not re.match(r"^https?://[^\s]+$", v):
            raise ValueError("유효한 URL 형식이 아닙니다. (예: https://example.com)")
        return v

    @model_validator(mode="after")
    def validate_scenario(self) -> TestUpdate:
        steps = self.http_scenario
        if not steps:
            return self
        for i, s in enumerate(steps):
            if not TestCreate._url_ok(s.url):
                raise ValueError(f"시나리오 {i + 1}단계 URL이 올바르지 않습니다.")
        return self


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
    body_preview_size: int = Field(
        500,
        alias="bodyPreviewSize",
        description="결과 화면에서 본문 미리보기 글자 수.",
    )
    vu_url_suffix: bool = Field(False, alias="vuUrlSuffix")
    vu_start: int = Field(1, alias="vuStart")
    error_page_rules: list[ErrorPageRule] = Field(default_factory=list, alias="errorPageRules")
    error_page_pattern: str | None = Field(None, alias="errorPagePattern")
    error_page_match_mode: str = Field("contains", alias="errorPageMatchMode")
    http_scenario: list[Any] | None = Field(None, alias="httpScenario")
    browser_actions: list[Any] | None = Field(None, alias="browserActions")
    tags: list[str] = Field(default_factory=list, alias="tags")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    @field_validator("error_page_rules", mode="before")
    @classmethod
    def coerce_error_page_rules(cls, v: Any) -> Any:
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip():
                return []
            try:
                data = json.loads(v)
                return data if isinstance(data, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        return v

    @model_validator(mode="after")
    def fill_error_rules_from_legacy(self) -> TestResponse:
        if self.error_page_rules:
            return self
        pat = (self.error_page_pattern or "").strip()
        if pat:
            mode = (
                "not_contains"
                if (self.error_page_match_mode or "").strip() == "not_contains"
                else "contains"
            )
            self.error_page_rules = [ErrorPageRule(pattern=pat, match_mode=mode)]
        return self

    @field_validator("http_scenario", mode="before")
    @classmethod
    def parse_http_scenario(cls, v: Any) -> list[Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                data = json.loads(v)
                return data if isinstance(data, list) else None
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @field_validator("browser_actions", mode="before")
    @classmethod
    def parse_browser_actions(cls, v: Any) -> list[Any] | None:
        if v is None or v == "":
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                data = json.loads(v)
                return data if isinstance(data, list) else None
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("browser_actions JSON 파싱 실패, null 처리: %s", e)
                return None
        return None

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags_response(cls, v: Any) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, list):
            if not v:
                return []
            if isinstance(v[0], str):
                return normalize_tag_list([str(x) for x in v])
            return normalize_tag_list([str(getattr(x, "name", "")) for x in v])
        if isinstance(v, str):
            try:
                data = json.loads(v)
                if isinstance(data, list):
                    return normalize_tag_list([str(x) for x in data])
            except (json.JSONDecodeError, TypeError):
                return []
            return []
        return []
