"""k6 시나리오: 폴링은 poll이 있는 스텝만, 스크립트는 runScenarioStep + 단일 while(true)."""

from types import SimpleNamespace

from app.services.k6_runner import _build_k6_scenario_step_payloads, generate_script


def _fake_test(http_scenario_json: str) -> SimpleNamespace:
    return SimpleNamespace(
        http_scenario=http_scenario_json,
        vu_url_suffix=False,
        vus=1,
        duration=1,
        request_delay=0,
        ramp_up=0,
        iterations=None,
        error_page_rules=None,
        error_page_pattern=None,
        error_page_match_mode="contains",
        vu_start=1,
        http_method="GET",
        target_url="https://a.com",
        query_params=None,
        headers=None,
        request_body=None,
    )


def test_payload_only_polling_step_has_poll_key() -> None:
    raw = """[
  {"url":"https://a.com","method":"GET"},
  {"url":"https://b.com","method":"GET","poll":{"intervalSeconds":1,"maxDurationSeconds":5,"untilStatusIn":[200]}},
  {"url":"https://c.com","method":"GET"},
  {"url":"https://d.com","method":"GET"}
]"""
    test = _fake_test(raw)
    built = _build_k6_scenario_step_payloads(test)
    assert built is not None
    steps, _ = built
    assert len(steps) == 4
    with_poll = [i for i, s in enumerate(steps) if s.get("poll")]
    assert with_poll == [1]


def test_invalid_poll_not_attached_to_step() -> None:
    """interval/max만 있고 성공 조건 없으면 poll 키 없음."""
    raw = """[
  {"url":"https://a.com","method":"GET","poll":{"intervalSeconds":1,"maxDurationSeconds":5}},
  {"url":"https://b.com","method":"GET"}
]"""
    test = _fake_test(raw)
    steps, _ = _build_k6_scenario_step_payloads(test)  # type: ignore[misc]
    assert not any(s.get("poll") for s in steps)


def test_generated_script_uses_run_scenario_step_and_single_poll_loop() -> None:
    raw = """[
  {"url":"https://a.com","method":"GET"},
  {"url":"https://b.com","method":"GET","poll":{"intervalSeconds":1,"maxDurationSeconds":5,"untilStatusIn":[200]}},
  {"url":"https://c.com","method":"GET"}
]"""
    js = generate_script(_fake_test(raw))
    assert "function runScenarioStep(step, si)" in js
    assert "for (var si = 0; si < STEPS.length; si++)" in js
    assert js.count("while (true)") == 1
    assert "pollTotalAttempts: pollAttempt" in js
    assert ", pollAttempt: pollAttempt" not in js
    assert js.count("__REQ__") == js.count("__REQEND__")
    assert js.count("'__REQ__'") == 2
