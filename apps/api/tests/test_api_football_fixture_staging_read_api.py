from __future__ import annotations

from datetime import date, datetime, timezone
import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import api_football_fixture_staging_read_api as read_api_module
from app.modules.providers.api_football_fixture_staging_read_api import (
    ALLOWED_FIXTURE_STAGING_OUTPUT_FIELDS,
    ApiFootballFixtureStagingReadApiValidationError,
    build_fixture_staging_read_query,
    serialize_fixture_staging_rows,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "59_INTERNAL_READ_ONLY_FIXTURES_API.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "040-phase-40-internal-read-only-fixtures-api.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "040-phase-40-internal-read-only-fixtures-api.md"
)

EXPECTED_RESPONSE_KEYS = {
    "provider",
    "mode",
    "target_table",
    "read_only",
    "db_writes",
    "prediction_created",
    "betting_created",
    "filters",
    "limit",
    "offset",
    "count",
    "fixtures",
}
FORBIDDEN_FIXTURE_OUTPUT_FIELDS = {
    "raw_payload",
    "api_key",
    "secret",
    "auth",
    "token",
    "odds",
    "bookmaker",
    "stake",
    "prediction",
    "predictions",
    "betting",
    "model_output",
    "confidence_score",
}


def _literal(*parts: str) -> str:
    return "".join(parts)


def _fixture_row() -> dict[str, object]:
    return {
        "provider": "api-football",
        "provider_fixture_id": 101,
        "provider_league_id": 39,
        "provider_season": 2026,
        "fixture_date": datetime(2026, 7, 7, 18, 0, tzinfo=timezone.utc),
        "fixture_timezone": "UTC",
        "fixture_status_short": "NS",
        "fixture_status_long": "Not Started",
        "home_team_provider_id": 33,
        "home_team_name": "Home FC",
        "away_team_provider_id": 34,
        "away_team_name": "Away FC",
        "goals_home": None,
        "goals_away": None,
        "score_halftime_home": None,
        "score_halftime_away": None,
        "score_fulltime_home": None,
        "score_fulltime_away": None,
        "payload_hash": "abc123",
        "payload_top_level_keys": ("response", "results"),
        "fetched_at": datetime(2026, 7, 7, 12, 0, tzinfo=timezone.utc),
        "source_mode": "phase_40_read_only_test",
        "raw_payload": {"provider": "body"},
        "api_key": "blocked",
        "secret": "blocked",
        "auth": "blocked",
        "token": "blocked",
        "odds": {"home": 1.5},
        "bookmaker": "blocked",
        "stake": 100,
        "prediction": "blocked",
        "predictions": ["blocked"],
        "betting": "blocked",
        "model_output": {"blocked": True},
        "confidence_score": 0.9,
    }


def test_fixture_staging_read_api_module_and_functions_exist() -> None:
    assert hasattr(read_api_module, "build_fixture_staging_read_query")
    assert hasattr(read_api_module, "serialize_fixture_staging_rows")
    assert callable(build_fixture_staging_read_query)
    assert callable(serialize_fixture_staging_rows)


def test_fixture_staging_read_query_defaults_to_api_football() -> None:
    query = build_fixture_staging_read_query()

    assert query == {
        "provider": "api-football",
        "mode": "fixture_staging_internal_read_only_api",
        "target_table": "api_football_fixture_staging",
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
        "filters": {},
        "limit": 50,
        "offset": 0,
    }


def test_fixture_staging_read_query_rejects_other_provider() -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        build_fixture_staging_read_query(provider="other-provider")


def test_fixture_staging_read_query_rejects_limit_above_one_hundred() -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        build_fixture_staging_read_query(limit=101)


@pytest.mark.parametrize("limit", [0, -1, True, "50"])
def test_fixture_staging_read_query_rejects_invalid_limits(limit: object) -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        build_fixture_staging_read_query(limit=limit)  # type: ignore[arg-type]


@pytest.mark.parametrize("offset", [-1, True, "0"])
def test_fixture_staging_read_query_rejects_invalid_offsets(offset: object) -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        build_fixture_staging_read_query(offset=offset)  # type: ignore[arg-type]


def test_fixture_staging_read_query_accepts_filters() -> None:
    query = build_fixture_staging_read_query(
        provider_league_id=39,
        provider_season=2026,
        fixture_status_short=" NS ",
        date_from="2026-07-01",
        date_to="2026-07-31",
        limit=25,
        offset=10,
    )

    assert query["filters"] == {
        "provider_league_id": 39,
        "provider_season": 2026,
        "fixture_status_short": "NS",
        "date_from": "2026-07-01",
        "date_to": "2026-07-31",
    }
    assert query["limit"] == 25
    assert query["offset"] == 10


@pytest.mark.parametrize(
    "kwargs",
    [
        {"provider_league_id": 0},
        {"provider_league_id": True},
        {"provider_league_id": "39"},
        {"provider_season": 1899},
        {"provider_season": 2101},
        {"provider_season": True},
        {"fixture_status_short": "   "},
        {"fixture_status_short": 123},
    ],
)
def test_fixture_staging_read_query_rejects_invalid_filters(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        build_fixture_staging_read_query(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["date_from", "date_to"])
@pytest.mark.parametrize("value", ["2026-7-01", "2026-02-30", 20260701])
def test_fixture_staging_read_query_rejects_invalid_dates(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        build_fixture_staging_read_query(**{field_name: value})  # type: ignore[arg-type]


def test_fixture_staging_read_query_rejects_inverted_date_range() -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError, match="date_from"):
        build_fixture_staging_read_query(
            date_from="2026-08-01",
            date_to="2026-07-01",
        )


def test_fixture_staging_serializer_returns_default_public_safe_shape() -> None:
    result = serialize_fixture_staging_rows([])

    assert set(result) == EXPECTED_RESPONSE_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "fixture_staging_internal_read_only_api"
    assert result["target_table"] == "api_football_fixture_staging"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["betting_created"] is False
    assert result["filters"] == {}
    assert result["limit"] == 50
    assert result["offset"] == 0
    assert result["count"] == 0
    assert result["fixtures"] == []


def test_fixture_staging_serializer_uses_query_context() -> None:
    query = build_fixture_staging_read_query(
        provider_league_id=39,
        provider_season=2026,
        limit=2,
        offset=4,
    )

    result = serialize_fixture_staging_rows([_fixture_row()], query=query)

    assert result["filters"] == {"provider_league_id": 39, "provider_season": 2026}
    assert result["limit"] == 2
    assert result["offset"] == 4
    assert result["count"] == 1


def test_fixture_staging_serializer_returns_only_allowed_fixture_fields() -> None:
    result = serialize_fixture_staging_rows([_fixture_row()])
    fixture = result["fixtures"][0]

    assert set(fixture) == set(ALLOWED_FIXTURE_STAGING_OUTPUT_FIELDS)
    assert FORBIDDEN_FIXTURE_OUTPUT_FIELDS.isdisjoint(fixture)
    assert fixture["fixture_date"] == "2026-07-07T18:00:00+00:00"
    assert fixture["fetched_at"] == "2026-07-07T12:00:00+00:00"
    assert fixture["payload_top_level_keys"] == ["response", "results"]

    serialized_fixture = json.dumps(fixture, sort_keys=True)
    for forbidden_field in FORBIDDEN_FIXTURE_OUTPUT_FIELDS:
        assert forbidden_field not in serialized_fixture


def test_fixture_staging_serializer_handles_date_and_payload_key_variants() -> None:
    row = _fixture_row()
    row["fixture_date"] = date(2026, 7, 7)
    row["payload_top_level_keys"] = {"results": True, "response": True}

    result = serialize_fixture_staging_rows([row])
    fixture = result["fixtures"][0]

    assert fixture["fixture_date"] == "2026-07-07"
    assert fixture["payload_top_level_keys"] == ["response", "results"]


def test_fixture_staging_serializer_rejects_invalid_query_context() -> None:
    with pytest.raises(ApiFootballFixtureStagingReadApiValidationError):
        serialize_fixture_staging_rows([], query={"filters": []})


def test_fixture_staging_read_api_source_has_no_writes_provider_calls_or_secret_material() -> None:
    module_source = inspect.getsource(read_api_module).lower()

    forbidden_fragments = (
        _literal("in", "sert"),
        _literal("up", "date"),
        _literal("del", "ete"),
        "upsert",
        "session.add",
        ".execute(",
        "sqlalchemy",
        "commit",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "urlopen",
        "socket",
        _literal("api", "_key"),
        _literal("x", "-apisports-key"),
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("rapid", "api"),
        _literal("au", "th"),
        _literal("head", "er"),
        _literal("bear", "er"),
        _literal("tok", "en"),
        _literal("sec", "ret"),
        _literal("raw", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source


def test_fixture_staging_read_api_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 40" in doc_text
    assert "internal read-only only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no prediction" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "no public free endpoint" in doc_lower
    assert "phase 41" in doc_lower
    assert "data freshness" in doc_lower
    assert "provider audit trail" in doc_lower


def test_fixture_staging_read_api_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "59_INTERNAL_READ_ONLY_FIXTURES_API.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
