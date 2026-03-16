"""DB 스키마: performance_test, test_run, test_result. SQLAlchemy 2.0 + SQLite."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""


class PerformanceTest(Base):
    """성능 테스트 정의. id는 UUID."""

    __tablename__ = "performance_test"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    runs: Mapped[list["TestRun"]] = relationship("TestRun", back_populates="test")


class TestRun(Base):
    """테스트 실행 1건. id는 UUID. status: Ready | Running | Finished | Failed."""

    __tablename__ = "test_run"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    test_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("performance_test.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Ready")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    test: Mapped["PerformanceTest"] = relationship("PerformanceTest", back_populates="runs")
    result: Mapped["TestResult | None"] = relationship(
        "TestResult", back_populates="run", uselist=False
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
    failure_rate: Mapped[float] = mapped_column(Float, nullable=False)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False)
    tps_or_rps: Mapped[float] = mapped_column(Float, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False)  # seconds
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)  # k6 stderr 등 실패 사유

    run: Mapped["TestRun"] = relationship("TestRun", back_populates="result")


def init_db(engine: Any) -> None:
    """Create all tables. Call with create_engine(...)."""
    Base.metadata.create_all(bind=engine)
