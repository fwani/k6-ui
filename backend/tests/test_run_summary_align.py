"""http 엔진 결과 확정 정책: 통계는 k6 요약 그대로, 실행 시간만 벽시계 보정."""

from app.api.runs import _finalize_http_summary


def test_stats_kept_from_k6_summary_only_exec_time_corrected() -> None:
    summary = {
        "avg_response_time": 1.0,
        "max_response_time": 99.0,
        "failure_rate": 0.1,
        "request_count": 999,
        "tps_or_rps": 50.0,
        "execution_time": 2.0,
    }
    out = _finalize_http_summary(summary, exec_sec_wall=10.0)
    # 응답시간·요청수·TPS·실패율은 k6 요약값 유지 (절단된 행으로 덮어쓰지 않음)
    assert out["avg_response_time"] == 1.0
    assert out["max_response_time"] == 99.0
    assert out["request_count"] == 999
    assert out["tps_or_rps"] == 50.0
    assert out["failure_rate"] == 0.1
    # 실행 시간만 실제 벽시계로 보정
    assert out["execution_time"] == 10.0


def test_zero_wall_clock_keeps_k6_execution_time() -> None:
    summary = {"execution_time": 1.5, "request_count": 0, "tps_or_rps": 1.0}
    out = _finalize_http_summary(summary, exec_sec_wall=0.0)
    assert out["execution_time"] == 1.5
