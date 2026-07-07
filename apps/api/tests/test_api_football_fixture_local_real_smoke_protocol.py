from __future__ import annotations

import inspect
import json
import socket
from pathlib import Path

import pytest

from scripts import api_football_fixture_local_real_smoke_protocol as protocol_module
from scripts.api_football_fixture_local_real_smoke_protocol import (
    FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENDPOINT,
    FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES,
    FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_MODE,
    FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_PROVIDER,
    ApiFootballFixtureLocalRealSmokeProtocolResult,
    assert_api_football_fixture_local_real_smoke_protocol_output_safe,
    main,
    run_api_football_fixture_local_real_smoke_protocol,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "49_API_FOOTBALL_FIXTURE_LOCAL_ONLY_REAL_SMOKE_PROTOCOL.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"


def _literal(*parts: str) -> str:
    return "".join(parts)


def fixture_protocol_environ(**overrides: str | None) -> dict[str, str]:
    environ = {
        "APP_ENV": "development",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED": "1",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE": "2026-07-07",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE": "Africa/Kinshasa",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY": "1",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD": "1",
        "URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED": "1",
        "URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED": "1",
        "URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED": "1",
    }
    for key, value in overrides.items():
        if value is None:
            environ.pop(key, None)
        else:
            environ[key] = value
    return environ


def assert_protocol_summary_has_no_leaks(summary: dict[str, object]) -> None:
    serialized = json.dumps(summary, sort_keys=True).lower()
    forbidden_fragments = (
        _literal("http", "://"),
        _literal("https", "://"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("x", "-rapid", "api"),
        _literal("api", "_key"),
        _literal("author", "ization"),
        _literal("bear", "er"),
        "credential",
        _literal("provider", "_credentials"),
        "password",
        "secret",
        "token",
        _literal("raw", "_payload"),
        _literal("smoke", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized
    for env_name in FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_fixture_local_real_smoke_protocol_without_env_is_not_ready() -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(environ={})
    summary = result.public_safe_summary()

    assert result.provider == FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_PROVIDER
    assert result.endpoint == FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENDPOINT
    assert result.mode == FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_MODE
    assert result.executed is False
    assert result.ready_for_fixture_real_smoke is False
    assert "approved_query" not in summary
    assert "development_environment_missing" in result.blocking_reasons
    assert "fixture_smoke_not_explicitly_enabled" in result.blocking_reasons
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert_protocol_summary_has_no_leaks(summary)


def test_fixture_local_real_smoke_protocol_with_complete_env_is_ready() -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ()
    )
    summary = result.public_safe_summary()

    assert result.executed is False
    assert result.ready_for_fixture_real_smoke is True
    assert result.blocking_reasons == ()
    assert summary["approved_query"] == {
        "date": "2026-07-07",
        "timezone": "Africa/Kinshasa",
    }
    assert summary["db_writes"] is False
    assert summary["prediction_created"] is False
    assert summary["betting_created"] is False
    assert_protocol_summary_has_no_leaks(summary)


def test_fixture_local_real_smoke_protocol_refuses_production() -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ(APP_ENV="production")
    )

    assert result.ready_for_fixture_real_smoke is False
    assert "production_environment_refused" in result.blocking_reasons


@pytest.mark.parametrize(
    "date_value",
    ["2026/07/07", "2026-7-07", "2026-07-7", "2026-02-30", ""],
)
def test_fixture_local_real_smoke_protocol_refuses_invalid_date(date_value: str) -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ(
            URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE=date_value
        )
    )

    assert result.ready_for_fixture_real_smoke is False
    assert any(reason.startswith("fixture_smoke_date") for reason in result.blocking_reasons)


def test_fixture_local_real_smoke_protocol_refuses_empty_timezone() -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ(
            URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE="   "
        )
    )

    assert result.ready_for_fixture_real_smoke is False
    assert "fixture_smoke_timezone_missing" in result.blocking_reasons


@pytest.mark.parametrize(
    ("missing_env", "expected_reason"),
    [
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY", "read_only_confirmation_missing"),
        ("URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED", "no_db_write_confirmation_missing"),
        ("URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED", "no_prediction_confirmation_missing"),
        ("URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED", "no_betting_confirmation_missing"),
    ],
)
def test_fixture_local_real_smoke_protocol_refuses_missing_confirmations(
    missing_env: str,
    expected_reason: str,
) -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ(**{missing_env: None})
    )

    assert result.ready_for_fixture_real_smoke is False
    assert expected_reason in result.blocking_reasons


@pytest.mark.parametrize(
    ("extra_env", "expected_reason"),
    [
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_LEAGUE", "unsupported_fixture_query_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_TEAM", "unsupported_fixture_query_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_SEASON", "unsupported_fixture_query_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_ODDS", "forbidden_fixture_smoke_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_BOOKMAKER", "forbidden_fixture_smoke_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_STAKE", "forbidden_fixture_smoke_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_PREDICTIONS", "forbidden_fixture_smoke_parameter_present"),
        ("URIM_API_FOOTBALL_FIXTURE_SMOKE_BETTING", "forbidden_fixture_smoke_parameter_present"),
    ],
)
def test_fixture_local_real_smoke_protocol_refuses_out_of_scope_params(
    extra_env: str,
    expected_reason: str,
) -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ(**{extra_env: "1"})
    )

    assert result.ready_for_fixture_real_smoke is False
    assert expected_reason in result.blocking_reasons


def test_fixture_local_real_smoke_protocol_requires_no_key_or_provider_url() -> None:
    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ()
    )

    assert result.ready_for_fixture_real_smoke is True
    assert_protocol_summary_has_no_leaks(result.public_safe_summary())


def test_fixture_local_real_smoke_protocol_does_not_open_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("fixture protocol must not open network connections")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_api_football_fixture_local_real_smoke_protocol(
        environ=fixture_protocol_environ()
    )

    assert result.ready_for_fixture_real_smoke is True


def test_fixture_local_real_smoke_protocol_output_validator_rejects_constructed_leaks() -> None:
    unsafe_result = ApiFootballFixtureLocalRealSmokeProtocolResult(
        approved_query={"date": "2026-07-07", "timezone": _literal("http", "://unsafe")}
    )

    with pytest.raises(RuntimeError, match="non-public material"):
        assert_api_football_fixture_local_real_smoke_protocol_output_safe(unsafe_result)


def test_fixture_local_real_smoke_protocol_main_prints_safe_json(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for env_name in FIXTURE_LOCAL_REAL_SMOKE_PROTOCOL_ENV_NAMES:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    exit_code = main()
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["executed"] is False
    assert payload["ready_for_fixture_real_smoke"] is False
    assert payload["db_writes"] is False
    assert payload["prediction_created"] is False
    assert payload["betting_created"] is False
    assert_protocol_summary_has_no_leaks(payload)


def test_fixture_local_real_smoke_protocol_source_has_no_network_or_auth_material() -> None:
    source = inspect.getsource(protocol_module).lower()

    forbidden_fragments = (
        _literal("request", "s"),
        _literal("http", "x"),
        _literal("aio", "http"),
        _literal("url", "open"),
        _literal("url", "lib"),
        "create_connection",
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("x", "-rapid", "api-key"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("raw", "_payload"),
        _literal('"', "response", '":'),
        _literal('"', "parameters", '":'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_fixture_local_real_smoke_protocol_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")

    assert "Phase 30" in doc_text
    assert "## No real API call" in doc_text
    assert "## No quota" in doc_text
    assert "## Minimal query" in doc_text
    assert "## No DB ingestion" in doc_text
    assert "## No prediction" in doc_text
    assert "## No betting/odds" in doc_text
    assert "Phase 31: Fixture First Real Local Smoke Execution" in doc_text


def test_fixture_local_real_smoke_protocol_index_references_phase_30_doc() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "49_API_FOOTBALL_FIXTURE_LOCAL_ONLY_REAL_SMOKE_PROTOCOL.md" in index_text
