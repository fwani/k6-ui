"""HttpScenarioPoll while/until 검증."""

import pytest
from pydantic import ValidationError

from app.api.schemas.test import HttpScenarioPoll


def test_poll_until_json_and_while_ok() -> None:
    p = HttpScenarioPoll(
        intervalSeconds=1,
        maxDurationSeconds=30,
        untilJsonPath="a",
        untilEquals="c",
        whileJsonPath="a",
        whileEquals="b",
    )
    assert p.until_json_path == "a"
    assert p.while_json_path == "a"
    assert p.while_equals == "b"


def test_poll_until_status_only_with_while_ok() -> None:
    p = HttpScenarioPoll(
        intervalSeconds=1,
        maxDurationSeconds=30,
        untilStatusIn=[200],
        whileJsonPath="status",
        whileEquals="pending",
    )
    assert p.until_status_in == [200]
    assert p.while_json_path == "status"


def test_poll_while_equals_without_path_fails() -> None:
    with pytest.raises(ValidationError) as exc:
        HttpScenarioPoll(
            intervalSeconds=1,
            maxDurationSeconds=30,
            untilJsonPath="a",
            untilEquals="c",
            whileEquals="orphan",
        )
    assert "whileJsonPath" in str(exc.value).lower() or "whileEquals" in str(exc.value)


def test_poll_while_path_without_equals_fails() -> None:
    with pytest.raises(ValidationError) as exc:
        HttpScenarioPoll(
            intervalSeconds=1,
            maxDurationSeconds=30,
            untilJsonPath="a",
            untilEquals="c",
            whileJsonPath="status",
        )
    assert "whileEquals" in str(exc.value)
