"""engine=db (k6 + xk6-sql) 스크립트 생성·요약 파싱·스키마 검증."""

from types import SimpleNamespace

import pytest

from app.api.schemas.test import TestCreate as TestCreateSchema
from app.services import k6_runner


def _db_test(**over):
    base = dict(
        engine="db",
        db_driver="postgres",
        target_url="postgres://u:p@h:5432/db?sslmode=disable",
        db_query="SELECT 1",
        request_delay=None,
        vus=5,
        duration=10,
        ramp_up=0,
        iterations=None,
    )
    base.update(over)
    return SimpleNamespace(**base)


def test_generate_db_script_has_sql_open_and_query():
    script = k6_runner.generate_script(_db_test())
    assert "import sql from 'k6/x/sql';" in script
    assert 'import driver from "k6/x/sql/driver/postgres";' in script
    assert "sql.open(driver, DSN)" in script
    assert "postgres://u:p@h:5432/db?sslmode=disable" in script
    assert '"SELECT 1"' in script
    # HTTP 마커 재사용 → 기존 __REQ__/summary 파이프라인과 호환
    assert "__REQ__" in script
    assert "__K6_SUMMARY_JSON__" in script


def test_generate_db_script_unknown_driver_falls_back_to_postgres():
    script = k6_runner.generate_script(_db_test(db_driver="oracle"))
    assert 'k6/x/sql/driver/postgres' in script


def test_db_script_respects_iterations_option():
    script = k6_runner.generate_script(_db_test(iterations=3, vus=4))
    # iterations * vus = 12
    assert "iterations: 12" in script


def test_parse_k6_db_summary_maps_custom_metrics():
    data = {
        "metrics": {
            "query_duration": {"avg": 12.5, "max": 40.0},
            "query_errors": {"rate": 0.25},
            "iterations": {"count": 100, "rate": 10.0},
        }
    }
    out = k6_runner._parse_k6_db_summary(data)
    assert out["avg_response_time"] == 12.5
    assert out["max_response_time"] == 40.0
    assert out["failure_rate"] == 0.25
    assert out["request_count"] == 100
    assert out["tps_or_rps"] == 10.0
    assert out["execution_time"] == pytest.approx(10.0)


def test_parse_k6_db_summary_handles_missing_metrics():
    out = k6_runner._parse_k6_db_summary({"metrics": {}})
    assert out["request_count"] == 0
    assert out["tps_or_rps"] == 0.0


def test_schema_db_engine_valid():
    t = TestCreateSchema.model_validate(
        {
            "name": "q",
            "engine": "db",
            "targetUrl": "postgres://u:p@h:5432/db",
            "dbQuery": "SELECT 1",
            "vus": 5,
            "duration": 10,
        }
    )
    assert t.engine == "db"
    assert t.db_driver == "postgres"
    assert t.http_method == "QUERY"
    assert t.db_query == "SELECT 1"


def test_schema_db_engine_requires_query():
    with pytest.raises(ValueError):
        TestCreateSchema.model_validate(
            {
                "name": "q",
                "engine": "db",
                "targetUrl": "postgres://x",
                "vus": 1,
                "duration": 1,
            }
        )


def test_schema_db_engine_rejects_unsupported_driver():
    with pytest.raises(ValueError):
        TestCreateSchema.model_validate(
            {
                "name": "q",
                "engine": "db",
                "targetUrl": "mysql://x",
                "dbDriver": "mysql",
                "dbQuery": "SELECT 1",
                "vus": 1,
                "duration": 1,
            }
        )
