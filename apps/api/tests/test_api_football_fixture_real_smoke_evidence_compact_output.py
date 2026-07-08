from __future__ import annotations

from pathlib import Path
import json
import socket

import pytest

from app.modules.providers.api_football_fixture_response_normalizer import (
    normalize_api_football_fixture_response,
)
from scripts.api_football_fixture_first_real_local_smoke import (
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV,
    FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV,
    run_api_football_fixture_first_real_local_smoke,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "51_API_FOOTBALL_FIXTURE_REAL_SMOKE_EVIDENCE_AND_COMPACT_OUTPUT.md"
)
INDEX_PATH = REPO_ROOT / "docs" / "index.md"

PUBLIC_SAFE_HASH = "a2ee84bc090fcbf0dd09ec9ab007d0c267fb95246f58390b382dc70900505c3a"
PUBLIC_SAFE_TOP_LEVEL_KEYS = ("errors", "get", "paging", "parameters", "response", "results")
REAL_TEAM_NAMES_FOR_NEGATIVE_DOC_CHECKS = (
    "Dayton Dutch Lions",
    "Kings Hammer Columbus",
    "Belgium",
    "USA",
    "FC Copenhagen",
)


def _literal(*parts: str) -> str:
    return "".join(parts)


def fixture_smoke_environ(**overrides: str | None) -> dict[str, str]:
    environ = {
        "APP_ENV": "development",
        "URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED": "1",
        FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV: "LOCAL_ONLY_FAKE_PHASE32_AUTH",
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


def _fake_payload_with_fixture_details() -> dict[str, object]:
    return {
        "get": "fixtures",
        "parameters": {"date": "2026-07-07", "timezone": "Africa/Kinshasa"},
        "errors": [],
        "results": 1,
        "paging": {"current": 1, "total": 1},
        "response": [
            {
                "fixture": {
                    "id": 777001,
                    "date": "2026-07-07T18:00:00+00:00",
                    "timezone": "UTC",
                    "status": {"short": "NS", "long": "Not Started"},
                },
                "league": {"id": 39, "season": 2026, "name": "Test League"},
                "teams": {
                    "home": {"id": 33, "name": "Compact Home FC"},
                    "away": {"id": 34, "name": "Compact Away FC"},
                },
                "goals": {"home": 1, "away": 2},
                "score": {
                    "halftime": {"home": 0, "away": 1},
                    "fulltime": {"home": 1, "away": 2},
                },
            }
        ],
    }


def _read_phase_32_doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_fixture_real_smoke_evidence_doc_exists_and_records_compact_result() -> None:
    doc_text = _read_phase_32_doc()

    assert "Phase 32" in doc_text
    assert "status=completed_fixture_first_real_local_smoke" in doc_text
    assert "executed=true" in doc_text
    assert "provider=api-football" in doc_text
    assert "endpoint=/fixtures" in doc_text
    assert "mode=fixture_first_real_local_smoke_only" in doc_text
    assert "request_query.date=2026-07-07" in doc_text
    assert "request_query.timezone=Africa/Kinshasa" in doc_text
    assert "normalized_count=108" in doc_text
    assert f"payload_hash={PUBLIC_SAFE_HASH}" in doc_text
    for key in PUBLIC_SAFE_TOP_LEVEL_KEYS:
        assert key in doc_text
    assert "db_writes=false" in doc_text
    assert "prediction_created=false" in doc_text
    assert "betting_created=false" in doc_text


def test_fixture_real_smoke_evidence_doc_has_no_provider_payload_or_fixture_list() -> None:
    doc_text = _read_phase_32_doc()
    doc_text_lower = doc_text.lower()

    forbidden_fragments = (
        _literal("http", "://"),
        _literal("https", "://"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("x", "-rapid", "api"),
        _literal("x", "-apisports-key"),
        _literal("api", "_key"),
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("credential", "="),
        _literal("token", "="),
        _literal("secret", "="),
        _literal("provider", "_credentials"),
        _literal("raw", "_payload"),
        _literal("```", "json"),
        _literal('"', "response", '":'),
        _literal('"', "parameters", '":'),
        _literal('"', "fixtures", '":'),
        "provider_fixture_id",
        "home_team_name",
        "away_team_name",
        "score_halftime_home",
        "score_fulltime_home",
        _literal("db_writes", "=true"),
        _literal("prediction_created", "=true"),
        _literal("betting_created", "=true"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in doc_text_lower
    for team_name in REAL_TEAM_NAMES_FOR_NEGATIVE_DOC_CHECKS:
        assert team_name.lower() not in doc_text_lower


def test_fixture_real_smoke_evidence_doc_is_referenced_by_index() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "51_API_FOOTBALL_FIXTURE_REAL_SMOKE_EVIDENCE_AND_COMPACT_OUTPUT.md" in index_text


def test_fixture_first_real_local_smoke_fake_transport_returns_compact_success() -> None:
    payload = _fake_payload_with_fixture_details()
    expected_normalized = normalize_api_football_fixture_response(payload)

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(),
        request_callable=lambda _base_url, _auth_material, _query: payload,
    )
    summary = result.public_safe_summary()

    assert summary["executed"] is True
    assert summary["status"] == "completed_fixture_first_real_local_smoke"
    assert summary["request_query"] == {
        "date": "2026-07-07",
        "timezone": "Africa/Kinshasa",
    }
    assert summary["normalized_count"] == expected_normalized["normalized_count"]
    assert summary["payload_hash"] == expected_normalized["payload_hash"]
    assert summary["payload_top_level_keys"] == expected_normalized["payload_top_level_keys"]
    assert summary["db_writes"] is False
    assert summary["prediction_created"] is False
    assert summary["betting_created"] is False
    assert "fixtures" not in summary


def test_fixture_first_real_local_smoke_compact_success_has_no_fixture_details() -> None:
    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(),
        request_callable=lambda _base_url, _auth_material, _query: _fake_payload_with_fixture_details(),
    )
    serialized_summary = json.dumps(result.public_safe_summary(), sort_keys=True)

    forbidden_fragments = (
        _literal('"', "fixtures", '":'),
        "provider_fixture_id",
        "home_team_provider_id",
        "away_team_provider_id",
        "home_team_name",
        "away_team_name",
        "goals_home",
        "goals_away",
        "score_halftime_home",
        "score_halftime_away",
        "score_fulltime_home",
        "score_fulltime_away",
        "Compact Home FC",
        "Compact Away FC",
        "777001",
        "Test League",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized_summary


def test_fixture_first_real_local_smoke_without_env_still_returns_safe_false() -> None:
    result = run_api_football_fixture_first_real_local_smoke(environ={})
    summary = result.public_safe_summary()

    assert summary["executed"] is False
    assert summary["status"] == "not_ready_for_fixture_first_real_local_smoke"
    assert summary["db_writes"] is False
    assert summary["prediction_created"] is False
    assert summary["betting_created"] is False
    assert "fixtures" not in summary


def test_fixture_first_real_local_smoke_compact_contract_uses_no_real_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create_connection(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("compact output tests must not open real network connections")

    monkeypatch.setattr(socket, "create_connection", fail_create_connection)

    result = run_api_football_fixture_first_real_local_smoke(
        environ=fixture_smoke_environ(
            **{
                FIXTURE_FIRST_REAL_LOCAL_SMOKE_AUTH_ENV: "LOCAL_ONLY_FAKE_PHASE32_AUTH",
                FIXTURE_FIRST_REAL_LOCAL_SMOKE_BASE_URL_ENV: _literal(
                    "https",
                    "://example.invalid/fixtures",
                ),
            }
        ),
        request_callable=lambda _base_url, _auth_material, _query: _fake_payload_with_fixture_details(),
    )

    assert result.executed is True
