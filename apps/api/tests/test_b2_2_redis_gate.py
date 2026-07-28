from __future__ import annotations

import pytest

from scripts import b2_2_redis_gate


@pytest.mark.parametrize(
    ("value", "reason"),
    (
        (None, "REDIS_URL_MISSING"),
        ("", "REDIS_URL_MISSING"),
        ("not-a-redis-url", "REDIS_URL_INVALID"),
        ("redis://localhost:6379", "REDIS_URL_LOCAL_FORBIDDEN"),
        ("redis://127.0.0.1:6379", "REDIS_URL_LOCAL_FORBIDDEN"),
        ("redis://placeholder.invalid:6379", "REDIS_URL_PLACEHOLDER_FORBIDDEN"),
    ),
)
def test_render_gate_refuses_missing_local_fake_or_invalid_urls(
    value: str | None,
    reason: str,
) -> None:
    assert b2_2_redis_gate.validate_redis_url(value) == (False, reason)


def test_render_gate_accepts_a_nonlocal_runtime_redis_url() -> None:
    valid, reason = b2_2_redis_gate.validate_redis_url(
        "redis://private.internal:6379"
    )

    assert valid is True
    assert reason == "REDIS_URL_ACCEPTED"


def test_render_gate_missing_configuration_is_public_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)

    assert b2_2_redis_gate.main() == 2

    output = capsys.readouterr().out
    assert output.splitlines() == [
        "REDIS_URL_PRESENT=false",
        "REDIS_URL_VALID=false",
        "REDIS_GATE_STATUS=REFUSED",
        "REDIS_GATE_REASON=REDIS_URL_MISSING",
    ]


def test_render_gate_never_prints_connection_details_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    connection_url = "redis://private.internal:6379"
    credential_canary = "runtime-sensitive-value"

    def fail_from_url(*args: object, **kwargs: object) -> object:
        raise RuntimeError(f"{credential_canary} {connection_url}")

    monkeypatch.setenv("REDIS_URL", connection_url)
    monkeypatch.setattr(
        b2_2_redis_gate.Redis,
        "from_url",
        fail_from_url,
    )

    assert b2_2_redis_gate.main() == 2

    output = capsys.readouterr().out
    assert connection_url not in output
    assert credential_canary not in output
    assert "private.internal" not in output
    assert "REDIS_GATE_STATUS=FAIL" in output


def test_render_gate_fail_closed_probe_neutralizes_internal_details() -> None:
    assert b2_2_redis_gate._fail_closed_probe() is True
