from __future__ import annotations

from pathlib import Path
import inspect
import json
import socket
import subprocess
import sys
from urllib.error import HTTPError

import pytest

from scripts import api_football_fixture_first_real_local_smoke as smoke_module
from scripts.api_football_fixture_first_real_local_smoke import (
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_ALLOWED_AUTH_HEADER,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENDPOINT,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENV_NAMES,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_MODE,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_PROVIDER,
    ApiFootballFixtureFirstRealLocalSmokeResult,
    assert_api_football_fixture_first_real_local_smoke_output_safe,
    run_api_football_fixture_first_real_local_smoke,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "50_API_FOOTBALL_FIXTURE_FIRST_REAL_LOCAL_SMOKE_EXECUTION.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"


def _literal(*parts: str) -> str:
    return "".join(parts)


def fixture_smoke_environ(**overrides: str | None) -> dict[str, str]:
    environ = {
        "APP_ENV": "development",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED": "1",
        FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV: "LOCAL_ONLY_FAKE_PHASE31_AUTH",
        FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV: _literal(
            "https",
            "://example.invalid/fixtures",
        ),
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


def fake_payload() -> dict[str, object]:
    return {
        "get": "fixtures",
        "parameters": {"date": "2026-07-07", "timezone": "Africa/Kinshasa"},
        "errors": [],
        "results": 1,
        "paging": {"current": 1, "total": 1},
        "response": [
            {
                "fixture": {
                    "id": 101,
                    "date": "2026-07-07T18:00:00+00:00",
                    "timezone": "UTC",
                    "status": {"short": "NS", "long": "Not Started"},
                    "venue": {"name": "Ignored Stadium"},
                },
                "league": {"id": 39, "season": 2026, "name": "Ignored League"},
                "teams": {
                    "home": {"id": 33, "name": "Home FC"},
                    "away": {"id": 34, "name": "Away FC"},
                },
                "goals": {"home": 1, "away": 2},
                "score": {
                    "halftime": {"home": 0, "away": 1},
                    "fulltime": {"home": 1, "away": 2},
                },
                "ignored_provider_field": "must not be returned",
            }
        ],
    }


def assert_summary_has_no_fixture_smoke_leaks(summary: dict[str, object]) -> None:
    serialized = json.dumps(summary, sort_keys=True).lower()
    forbidden_fragments = (
        "local_only_fake_phase31_auth",
        "example.invalid",
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("x", "-rapid", "api-key"),
        _literal("api", "_key"),
        "credential",
        _literal("provider", "_credentials"),
        "password",
        "secret",
        "token",
        _literal("raw", "_payload"),
        _literal("smoke", "_payload"),
        "ignored_provider_field",
        "Ignored Stadium",
        "Ignored League",
    )
    for fragment in forbidden_fragments:
        assert fragment.lower() not in serialized
    for env_name in FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENV_NAMES:
        assert env_name.lower() not in serialized


def test_fixture_first_real_local_smoke_without_env_is_not_ready() -> None:
    result = run_api_football_fixture_first_real_local_smoke(environ={})
    summary = result.public_safe_summary()

    assert result.provider == FIXTURE_FIRST_REAL_LOCAL_SMOKE_PROVIDER
    assert result.endpoint == FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENDPOINT
    assert result.mode == FIXTURE_FIRST_REAL_LOCAL_SMOKE_MODE
    assert result.status == FIXTURE_FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    assert result.executed is False
    assert "fixture_protocol_not_ready" in result.blocking_reasons
    assert "local_auth_material_missing" in result.blocking_reasons
    assert "local_provider_reference_missing" in result.blocking_reasons
    assert result.db_writes is False
    assert result.prediction_created is False
    assert result.betting_created is False
    assert_summary_has_no_fixture_smoke_leaks(summary)


def test_fixture_first_real_local_smoke_with_fake_transport_executes() -> None:
    captured: dict[str, object] = {}

    def fake_request_callable(
        base_url: str,
        auth_material: str,
        query: dict[str, str],
    ) -> dict[str, object]:
        captured["base_url"] = base_url
        captured["auth_material"] = auth_material
        captured["query"] = query
        return fake_payload()

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(),
        request_callable=fake_request_callable,
    )
    summary = result.public_safe_summary()

    assert captured["base_url"] == fixture_smoke_environ()[FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV]
    assert captured["auth_material"] == fixture_smoke_environ()[FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV]
    assert captured["query"] == {"date": "2026-07-07", "timezone": "Africa/Kinshasa"}
    assert result.status == FIXTURE_FIRST_REAL_LOCAL_SMOKE_COMPLETED_STATUS
    assert result.executed is True
    assert summary["request_query"] == {"date": "2026-07-07", "timezone": "Africa/Kinshasa"}
    assert summary["normalized_count"] == 1
    assert isinstance(summary["payload_hash"], str)
    assert len(summary["payload_hash"]) == 64
    assert summary["payload_top_level_keys"] == [
        "errors",
        "get",
        "paging",
        "parameters",
        "response",
        "results",
    ]
    assert summary["fixtures"] == [
        {
            "provider": "api-football",
            "provider_fixture_id": 101,
            "provider_league_id": 39,
            "provider_season": 2026,
            "fixture_date": "2026-07-07T18:00:00+00:00",
            "fixture_timezone": "UTC",
            "fixture_status_short": "NS",
            "fixture_status_long": "Not Started",
            "home_team_provider_id": 33,
            "home_team_name": "Home FC",
            "away_team_provider_id": 34,
            "away_team_name": "Away FC",
            "goals_home": 1,
            "goals_away": 2,
            "score_halftime_home": 0,
            "score_halftime_away": 1,
            "score_fulltime_home": 1,
            "score_fulltime_away": 2,
        }
    ]
    assert summary["db_writes"] is False
    assert summary["prediction_created"] is False
    assert summary["betting_created"] is False
    assert_summary_has_no_fixture_smoke_leaks(summary)


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"APP_ENV": "production"}, "production_environment_refused"),
        ({FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV: None}, "local_auth_material_missing"),
        ({FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV: None}, "local_provider_reference_missing"),
        ({"URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE": "2026-02-30"}, "fixture_smoke_date_invalid"),
        ({"URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE": "   "}, "fixture_smoke_timezone_missing"),
        ({"URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY": None}, "read_only_confirmation_missing"),
        ({"URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED": None}, "no_db_write_confirmation_missing"),
        ({"URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED": None}, "no_prediction_confirmation_missing"),
        ({"URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED": None}, "no_betting_confirmation_missing"),
    ],
)
def test_fixture_first_real_local_smoke_refuses_missing_or_unsafe_conditions(
    overrides: dict[str, str | None],
    expected_reason: str,
) -> None:
    def fail_request_callable(
        _base_url: str,
        _auth_material: str,
        _query: dict[str, str],
    ) -> dict[str, object]:
        raise AssertionError("request callable must not be used")

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(**overrides),
        request_callable=fail_request_callable,
    )

    assert result.executed is False
    assert expected_reason in result.blocking_reasons
    assert_summary_has_no_fixture_smoke_leaks(result.public_safe_summary())


@pytest.mark.parametrize(
    "base_url",
    [
        _literal("https", "://example.invalid/predictions"),
        _literal("https", "://example.invalid/odds"),
    ],
)
def test_fixture_first_real_local_smoke_refuses_forbidden_provider_endpoints(
    base_url: str,
) -> None:
    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(
            **{FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV: base_url}
        ),
        request_callable=lambda _base_url, _auth_material, _query: fake_payload(),
    )

    assert result.executed is False
    assert "forbidden_provider_endpoint_reference" in result.blocking_reasons


def test_fixture_first_real_local_smoke_standard_request_uses_only_allowed_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(fake_payload()).encode("utf-8")

    def fake_urlopen(request: object, timeout: int) -> FakeResponse:
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(smoke_module, "urlopen", fake_urlopen)

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ()
    )

    request = captured["request"]
    headers = {key.lower(): value for key, value in request.headers.items()}
    assert result.executed is True
    assert captured["timeout"] == 10
    assert headers[FIXTURE_FIRST_REAL_LOCAL_SMOKE_ALLOWED_AUTH_HEADER] == (
        fixture_smoke_environ()[FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV]
    )
    assert "accept" in headers
    assert _literal("author", "ization") not in headers
    assert _literal("x", "-rapid", "api-key") not in headers
    assert all(_literal("bear", "er") not in str(value).lower() for value in headers.values())


def test_fixture_first_real_local_smoke_does_not_open_real_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("tests must not open real network connections")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(),
        request_callable=lambda _base_url, _auth_material, _query: fake_payload(),
    )

    assert result.executed is True


def test_fixture_first_real_local_smoke_http_error_is_public_safe() -> None:
    def failing_request_callable(
        base_url: str,
        _auth_material: str,
        _query: dict[str, str],
    ) -> dict[str, object]:
        raise HTTPError(base_url, 429, "Too Many Requests", hdrs=None, fp=None)

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(),
        request_callable=failing_request_callable,
    )
    summary = result.public_safe_summary()

    assert result.executed is False
    assert result.status == "provider_http_error"
    assert summary["http_status"] == 429
    assert "provider_http_error" in summary["blocking_reasons"]
    assert "traceback" not in json.dumps(summary).lower()
    assert_summary_has_no_fixture_smoke_leaks(summary)


def test_fixture_first_real_local_smoke_rejects_constructed_leaks() -> None:
    unsafe_result = ApiFootballFixtureFirstRealLocalSmokeResult(
        status=fixture_smoke_environ()[FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV]
    )

    with pytest.raises(RuntimeError, match="non-public provider material"):
        assert_api_football_fixture_first_real_local_smoke_output_safe(
            unsafe_result,
            environ=fixture_smoke_environ(),
        )


def test_fixture_first_real_local_smoke_script_without_sensitive_env_outputs_safe_json() -> None:
    env = {
        key: value
        for key, value in os_environ_without_fixture_smoke().items()
        if key not in FIXTURE_FIRST_REAL_LOCAL_SMOKE_ENV_NAMES
    }
    env["APP_ENV"] = "development"

    completed = subprocess.run(
        [sys.executable, "scripts/api_football_fixture_first_real_local_smoke.py"],
        cwd=REPO_ROOT / "apps" / "api",
        env=env,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["executed"] is False
    assert payload["status"] == FIXTURE_FIRST_REAL_LOCAL_SMOKE_NOT_READY_STATUS
    assert payload["db_writes"] is False
    assert payload["prediction_created"] is False
    assert payload["betting_created"] is False
    assert_summary_has_no_fixture_smoke_leaks(payload)


def os_environ_without_fixture_smoke() -> dict[str, str]:
    import os

    return dict(os.environ)


def test_fixture_first_real_local_smoke_source_has_no_disallowed_clients_or_headers() -> None:
    source = inspect.getsource(smoke_module).lower()

    forbidden_fragments = (
        "requests",
        "httpx",
        "aiohttp",
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("x", "-rapid", "api-key"),
        _literal("raw", "_payload"),
        _literal('"', "response", '":'),
        _literal('"', "parameters", '":'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_fixture_first_real_local_smoke_doc_exists_and_documents_manual_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_text_lower = doc_text.lower()

    assert "Phase 31" in doc_text
    assert "manual" in doc_text
    assert "local" in doc_text
    assert "controlled" in doc_text
    assert "## No DB ingestion" in doc_text
    assert "## No prediction" in doc_text
    assert "## No betting/odds" in doc_text
    assert "no automated tests may call the real provider" in doc_text_lower


def test_fixture_first_real_local_smoke_index_references_phase_31_doc() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "50_API_FOOTBALL_FIXTURE_FIRST_REAL_LOCAL_SMOKE_EXECUTION.md" in index_text
