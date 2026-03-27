"""k6 결과 요약을 저장 __REQ__ 행과 맞추는 로직."""

from app.api.runs import _align_k6_summary_with_stored_rows


def test_align_overwrites_avg_max_tps_from_rows() -> None:
    summary = {
        "avg_response_time": 1.0,
        "max_response_time": 99.0,
        "failure_rate": 0.1,
        "request_count": 999,
        "tps_or_rps": 50.0,
        "execution_time": 2.0,
    }
    rows = [
        {"response_time_ms": 100.0},
        {"response_time_ms": 300.0},
    ]
    out = _align_k6_summary_with_stored_rows(summary, rows, exec_sec_wall=10.0)
    assert out["request_count"] == 2
    assert out["avg_response_time"] == 200.0
    assert out["max_response_time"] == 300.0
    assert out["execution_time"] == 10.0
    assert out["tps_or_rps"] == 0.2
    assert out["failure_rate"] == 0.1


def test_align_empty_rows_only_wall_clock() -> None:
    summary = {"execution_time": 1.5, "request_count": 0, "tps_or_rps": 1.0}
    out = _align_k6_summary_with_stored_rows(summary, [], exec_sec_wall=8.0)
    assert out["execution_time"] == 8.0
