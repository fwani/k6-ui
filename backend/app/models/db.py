"""DB 스키마: performance_test, test_run, test_result. SQLAlchemy 2.0 + SQLite."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""


performance_test_tag = Table(
    "performance_test_tag",
    Base.metadata,
    Column("test_id", String(36), ForeignKey("performance_test.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """테스트에 붙는 태그 마스터. 이름 유일."""

    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    tests: Mapped[list["PerformanceTest"]] = relationship(
        secondary=performance_test_tag,
        back_populates="tags",
    )


class PerformanceTest(Base):
    """성능 테스트 정의. id는 UUID."""

    __tablename__ = "performance_test"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    engine: Mapped[str] = mapped_column(String(32), nullable=False, default="http")  # http=k6, browser=Playwright
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)  # base URL (no query)
    query_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array [{"key":"k","value":"v"},...]
    http_method: Mapped[str] = mapped_column(String(16), nullable=False)
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    headers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    vus: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # seconds
    request_delay: Mapped[float | None] = mapped_column(Float, nullable=True)
    ramp_up: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # seconds, 0 = no ramp
    iterations: Mapped[int | None] = mapped_column(Integer, nullable=True)  # total iterations; null = duration mode
    body_preview_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=500
    )  # 결과 화면에서 응답 본문을 잘라 보여줄 글자 수(저장 길이와 무관)
    vu_url_suffix: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 경로 끝에 {{VU}} 붙이기
    vu_start: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # {{VU}} 치환 시 첫 VU(__VU=1)에 넣을 값
    # 요청 URL 또는 응답 본문 판별. error_page_rules: JSON [{"pattern":"...","matchMode":"contains"|"not_contains"},...] (하나라도 실패 조건이면 실패)
    error_page_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_page_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)  # 첫 규칙과 동기화(레거시/API 호환)
    error_page_match_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="contains")
    # k6 전용: JSON 배열(단계). 비우면 단일 요청 모드(target_url 등).
    http_scenario: Mapped[str | None] = mapped_column(Text, nullable=True)
    # browser 전용: 로드 후 Playwright 액션 JSON 배열 (wait_selector | click | sleep).
    browser_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    runs: Mapped[list["TestRun"]] = relationship("TestRun", back_populates="test")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=performance_test_tag,
        back_populates="tests",
        order_by=Tag.name,
    )


class TestRun(Base):
    """테스트 실행 1건. id는 UUID. status: Ready | Running | Finished | Failed."""

    __tablename__ = "test_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    test_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("performance_test.id", ondelete="CASCADE"), nullable=False
    )
    engine: Mapped[str] = mapped_column(String(32), nullable=False, default="http")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Ready")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    test: Mapped["PerformanceTest"] = relationship("PerformanceTest", back_populates="runs")
    result: Mapped["TestResult | None"] = relationship(
        "TestResult", back_populates="run", uselist=False, cascade="all, delete-orphan"
    )
    request_responses: Mapped[list["RunRequestResponse"]] = relationship(
        "RunRequestResponse", back_populates="run", cascade="all, delete-orphan"
    )


class TestResult(Base):
    """테스트 실행 결과 요약. id는 UUID. Run 1:1."""

    __tablename__ = "test_result"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_run.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    avg_response_time: Mapped[float] = mapped_column(Float, nullable=False)
    max_response_time: Mapped[float] = mapped_column(Float, nullable=False)
    failure_rate: Mapped[float] = mapped_column(Float, nullable=False)  # k6 http_req_failed 등 HTTP 관점
    overall_failure_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 행 기준 HTTP 비-2xx 또는 failed
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    tps_or_rps: Mapped[float] = mapped_column(Float, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)  # seconds
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)  # k6 stderr 등 실패 사유
    # 브라우저(렌더링) Run 전용 메트릭 (nullable)
    lcp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    fcp_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    cls: Mapped[float | None] = mapped_column(Float, nullable=True)
    ttfb_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    run: Mapped["TestRun"] = relationship("TestRun", back_populates="result")


class RunRequestResponse(Base):
    """실행 시 각 HTTP 요청별 응답 (상태코드, 응답시간, 본문, 요청 시각). run당 최대 1만 건."""

    __tablename__ = "run_request_response"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_run.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-based order
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)  # HTTP: 응답 본문 전체, browser: innerText
    requested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # 요청 시각
    request_args: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: url, method, headers, body (해당 요청 기준)
    screenshot: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)  # 브라우저 Run VU별 PNG
    failed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # 200이어도 에러 페이지 등으로 실패한 경우 True

    run: Mapped["TestRun"] = relationship("TestRun", back_populates="request_responses")


def init_db(engine: Any) -> None:
    """Create all tables. Call with create_engine(...)."""
    Base.metadata.create_all(bind=engine)
