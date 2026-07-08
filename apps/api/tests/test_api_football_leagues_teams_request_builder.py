from __future__ import annotations

import inspect
import json
import socket
from pathlib import Path
from typing import Callable

import pytest

from app.modules.providers import api_football_leagues_teams_request_builder as builder_module
from app.modules.providers.api_football_leagues_teams_request_builder import (
    API_FOOTBALL_LEAGUES_ALLOWED_QUERY_KEYS,
    API_FOOTBALL_LEAGUES_REQUEST_ENDPOINT,
    API_FOOTBALL_LEAGUES_TEAMS_FORBIDDEN_QUERY_KEYS,
    API_FOOTBALL_LEAGUES_TEAMS_REQUEST_METHOD,
    API_FOOTBALL_LEAGUES_TEAMS_REQUEST_PROVIDER,
    API_FOOTBALL_TEAMS_ALLOWED_QUERY_KEYS,
    API_FOOTBALL_TEAMS_REQUEST_ENDPOINT,
    ApiFootballLeaguesTeamsRequestValidationError,
    build_api_football_leagues_request,
    build_api_football_teams_request,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = (
    REPO_ROOT / "docs" / "56_API_FOOTBALL_LEAGUES_TEAMS_READ_ONLY_BUILDERS.md"
)
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "037-phase-37-api-football-leagues-teams-read-only-builders.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "037-phase-37-api-football-leagues-teams-read-only-builders.md"
)

Builder = Callable[[dict[object, object] | None], dict[str, object]]


def _literal(*parts: str) -> str:
    return "".join(parts)


def test_leagues_builder_builds_empty_public_safe_request() -> None:
    request = build_api_football_leagues_request()

    assert request == {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_REQUEST_PROVIDER,
        "endpoint": API_FOOTBALL_LEAGUES_REQUEST_ENDPOINT,
        "method": API_FOOTBALL_LEAGUES_TEAMS_REQUEST_METHOD,
        "read_only": True,
        "query": {},
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }


def test_teams_builder_builds_empty_public_safe_request() -> None:
    request = build_api_football_teams_request()

    assert request == {
        "provider": API_FOOTBALL_LEAGUES_TEAMS_REQUEST_PROVIDER,
        "endpoint": API_FOOTBALL_TEAMS_REQUEST_ENDPOINT,
        "method": API_FOOTBALL_LEAGUES_TEAMS_REQUEST_METHOD,
        "read_only": True,
        "query": {},
        "db_writes": False,
        "prediction_created": False,
        "betting_created": False,
    }


def test_leagues_builder_accepts_allowed_query_in_stable_order() -> None:
    request = build_api_football_leagues_request(
        {
            "last": 5,
            "search": " Premier ",
            "current": True,
            "type": " league ",
            "team": 33,
            "season": 2026,
            "code": " CD ",
            "country": " Congo DR ",
            "name": " Linafoot ",
            "id": 39,
        }
    )

    expected_query = {
        "id": 39,
        "name": "Linafoot",
        "country": "Congo DR",
        "code": "CD",
        "season": 2026,
        "team": 33,
        "type": "league",
        "current": True,
        "search": "Premier",
        "last": 5,
    }
    assert request["provider"] == "api-football"
    assert request["endpoint"] == "/leagues"
    assert request["method"] == "GET"
    assert request["read_only"] is True
    assert list(request["query"]) == list(API_FOOTBALL_LEAGUES_ALLOWED_QUERY_KEYS)
    assert request["query"] == expected_query


def test_teams_builder_accepts_allowed_query_in_stable_order() -> None:
    request = build_api_football_teams_request(
        {
            "search": " home ",
            "venue": 44,
            "code": " KIN ",
            "country": " Congo DR ",
            "season": 2026,
            "league": 39,
            "name": " Local Team ",
            "id": 33,
        }
    )

    expected_query = {
        "id": 33,
        "name": "Local Team",
        "league": 39,
        "season": 2026,
        "country": "Congo DR",
        "code": "KIN",
        "venue": 44,
        "search": "home",
    }
    assert request["provider"] == "api-football"
    assert request["endpoint"] == "/teams"
    assert request["method"] == "GET"
    assert request["read_only"] is True
    assert list(request["query"]) == list(API_FOOTBALL_TEAMS_ALLOWED_QUERY_KEYS)
    assert request["query"] == expected_query


@pytest.mark.parametrize(
    "builder",
    [build_api_football_leagues_request, build_api_football_teams_request],
)
def test_leagues_teams_builders_reject_non_mapping_params(builder: Builder) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError):
        builder(["id"])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "builder",
    [build_api_football_leagues_request, build_api_football_teams_request],
)
def test_leagues_teams_builders_reject_non_string_keys(builder: Builder) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError):
        builder({1: 39})


@pytest.mark.parametrize(
    ("builder", "unknown_key"),
    [
        (build_api_football_leagues_request, "timezone"),
        (build_api_football_teams_request, "team"),
    ],
)
def test_leagues_teams_builders_reject_unknown_keys(
    builder: Builder,
    unknown_key: str,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError, match="Unknown"):
        builder({unknown_key: "value"})


@pytest.mark.parametrize("key", API_FOOTBALL_LEAGUES_TEAMS_FORBIDDEN_QUERY_KEYS)
@pytest.mark.parametrize(
    "builder",
    [build_api_football_leagues_request, build_api_football_teams_request],
)
def test_leagues_teams_builders_reject_forbidden_keys(
    builder: Builder,
    key: str,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError, match="forbidden"):
        builder({key: "value"})


@pytest.mark.parametrize(
    "key",
    [
        " Odds ",
        "BookMaker",
        "STAKE",
        "Prediction",
        "PREDICTIONS",
        "BETTING",
        _literal("raw", "_", "payload"),
        _literal("api", "_", "key"),
        "AUTH",
        "Secret",
    ],
)
def test_leagues_builder_rejects_normalized_forbidden_keys(key: str) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError, match="forbidden"):
        build_api_football_leagues_request({key: "value"})


@pytest.mark.parametrize(
    ("builder", "key"),
    [
        (build_api_football_leagues_request, "id"),
        (build_api_football_leagues_request, "team"),
        (build_api_football_leagues_request, "last"),
        (build_api_football_teams_request, "id"),
        (build_api_football_teams_request, "league"),
        (build_api_football_teams_request, "venue"),
    ],
)
@pytest.mark.parametrize("value", [0, -1, True, "1", 1.5, None])
def test_leagues_teams_builders_reject_invalid_positive_ints(
    builder: Builder,
    key: str,
    value: object,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError):
        builder({key: value})


@pytest.mark.parametrize(
    "builder",
    [build_api_football_leagues_request, build_api_football_teams_request],
)
@pytest.mark.parametrize(
    "value",
    [0, -1, True, "2026", 2026.0, None, 1899, 2101, 999, 10000],
)
def test_leagues_teams_builders_reject_invalid_seasons(
    builder: Builder,
    value: object,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError):
        builder({"season": value})


@pytest.mark.parametrize("value", ["true", 1, 0, None])
def test_leagues_builder_rejects_invalid_current_values(value: object) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError):
        build_api_football_leagues_request({"current": value})


@pytest.mark.parametrize(
    ("builder", "key"),
    [
        (build_api_football_leagues_request, "name"),
        (build_api_football_leagues_request, "country"),
        (build_api_football_leagues_request, "code"),
        (build_api_football_leagues_request, "type"),
        (build_api_football_leagues_request, "search"),
        (build_api_football_teams_request, "name"),
        (build_api_football_teams_request, "country"),
        (build_api_football_teams_request, "code"),
        (build_api_football_teams_request, "search"),
    ],
)
@pytest.mark.parametrize("value", ["", "   ", 123, None, True])
def test_leagues_teams_builders_reject_blank_or_non_string_text_fields(
    builder: Builder,
    key: str,
    value: object,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsRequestValidationError):
        builder({key: value})


def test_leagues_teams_builders_do_not_require_network_or_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    assert build_api_football_leagues_request({"id": 39})["query"] == {"id": 39}
    assert build_api_football_teams_request({"id": 33})["query"] == {"id": 33}


def test_leagues_teams_request_builder_source_has_no_transport_or_db_write() -> None:
    module_source = inspect.getsource(builder_module)
    module_source_lower = module_source.lower()

    forbidden_fragments = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "urlopen",
        "socket",
        "session.add",
        "insert into",
        "upsert",
        _literal("api-football", ".com"),
        _literal("api", "-sports"),
        _literal("raw", "_", "payload"),
        _literal("api", "_", "key"),
        _literal("author", "ization"),
        _literal("bear", "er"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source_lower


def test_leagues_teams_request_builder_public_summary_serializes_safely() -> None:
    serialized = json.dumps(
        build_api_football_leagues_request(
            {"id": 39, "season": 2026, "current": False}
        ),
        sort_keys=True,
    )
    serialized_lower = serialized.lower()

    safe_fragments = (
        '"db_writes": false',
        '"prediction_created": false',
        '"betting_created": false',
        '"read_only": true',
    )
    for fragment in safe_fragments:
        assert fragment in serialized_lower

    forbidden_fragments = (
        _literal("api", "key"),
        _literal("credential", "="),
        _literal("secret", "="),
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("header", "s"),
        _literal("api-football", ".com"),
        _literal("raw", "_payload"),
        _literal("db_writes", '": true'),
        _literal("prediction_created", '": true'),
        _literal("betting_created", '": true'),
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized_lower


def test_leagues_teams_request_builder_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 37" in doc_text
    assert "read-only only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion" in doc_lower
    assert "no prediction" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 38" in doc_lower
    assert "normalizers leagues/teams" in doc_lower


def test_leagues_teams_request_builder_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "56_API_FOOTBALL_LEAGUES_TEAMS_READ_ONLY_BUILDERS.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
