from __future__ import annotations

import inspect
import json
import socket
from pathlib import Path

import pytest

from app.modules.providers import api_football_leagues_teams_response_normalizer as normalizer_module
from app.modules.providers.api_football_leagues_teams_response_normalizer import (
    API_FOOTBALL_LEAGUES_NORMALIZER_ENDPOINT,
    API_FOOTBALL_LEAGUES_NORMALIZER_MODE,
    API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER,
    API_FOOTBALL_TEAMS_NORMALIZER_ENDPOINT,
    API_FOOTBALL_TEAMS_NORMALIZER_MODE,
    ApiFootballLeaguesTeamsResponseNormalizationError,
    normalize_api_football_leagues_response,
    normalize_api_football_teams_response,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = (
    REPO_ROOT / "docs" / "57_API_FOOTBALL_LEAGUES_TEAMS_RESPONSE_NORMALIZERS.md"
)
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "038-phase-38-api-football-leagues-teams-normalizers.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "038-phase-38-api-football-leagues-teams-normalizers.md"
)


def _literal(*parts: str) -> str:
    return "".join(parts)


def _leagues_payload(response: list[object]) -> dict[str, object]:
    return {
        "get": "leagues",
        "parameters": {"season": "2026"},
        "errors": [],
        "results": len(response),
        "paging": {"current": 1, "total": 1},
        "response": response,
    }


def _teams_payload(response: list[object]) -> dict[str, object]:
    return {
        "get": "teams",
        "parameters": {"league": "39", "season": "2026"},
        "errors": [],
        "results": len(response),
        "paging": {"current": 1, "total": 1},
        "response": response,
    }


def _complete_league() -> dict[str, object]:
    return {
        "league": {
            "id": 39,
            "name": "Test League",
            "type": "League",
            "logo": "ignored_league_logo",
        },
        "country": {
            "name": "Test Country",
            "code": "TC",
            "flag": "ignored_country_flag",
        },
        "seasons": [
            {
                "year": 2026,
                "start": "2026-01-01",
                "end": "2026-12-31",
                "current": True,
                "coverage": {"fixtures": {"events": True}},
            },
            {
                "year": 2027,
                "start": "2027-01-01",
                "end": "2027-12-31",
                "current": False,
            },
        ],
    }


def _complete_team() -> dict[str, object]:
    return {
        "team": {
            "id": 33,
            "name": "Test Team",
            "code": "TST",
            "country": "Test Country",
            "founded": 1999,
            "national": False,
            "logo": "ignored_team_logo",
        },
        "venue": {
            "id": 44,
            "name": "Test Venue",
            "city": "Test City",
            "capacity": 12000,
            "image": "ignored_venue_image",
        },
    }


def test_leagues_response_normalizer_normalizes_fake_league_seasons() -> None:
    output = normalize_api_football_leagues_response(
        _leagues_payload([_complete_league()])
    )

    assert output["provider"] == API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER
    assert output["endpoint"] == API_FOOTBALL_LEAGUES_NORMALIZER_ENDPOINT
    assert output["mode"] == API_FOOTBALL_LEAGUES_NORMALIZER_MODE
    assert isinstance(output["payload_hash"], str)
    assert len(output["payload_hash"]) == 64
    assert output["payload_top_level_keys"] == [
        "errors",
        "get",
        "paging",
        "parameters",
        "response",
        "results",
    ]
    assert output["normalized_count"] == 2
    assert output["db_writes"] is False
    assert output["prediction_created"] is False
    assert output["betting_created"] is False
    assert output["leagues"] == [
        {
            "provider": "api-football",
            "provider_league_id": 39,
            "league_name": "Test League",
            "league_type": "League",
            "country_name": "Test Country",
            "country_code": "TC",
            "season": 2026,
            "season_start": "2026-01-01",
            "season_end": "2026-12-31",
            "season_current": True,
        },
        {
            "provider": "api-football",
            "provider_league_id": 39,
            "league_name": "Test League",
            "league_type": "League",
            "country_name": "Test Country",
            "country_code": "TC",
            "season": 2027,
            "season_start": "2027-01-01",
            "season_end": "2027-12-31",
            "season_current": False,
        },
    ]


def test_leagues_response_normalizer_handles_missing_seasons() -> None:
    output = normalize_api_football_leagues_response(
        _leagues_payload(
            [
                {
                    "league": {"id": 40, "name": "No Season League", "type": "Cup"},
                    "country": {"name": "Test Country", "code": "TC"},
                }
            ]
        )
    )

    assert output["normalized_count"] == 1
    assert output["leagues"] == [
        {
            "provider": "api-football",
            "provider_league_id": 40,
            "league_name": "No Season League",
            "league_type": "Cup",
            "country_name": "Test Country",
            "country_code": "TC",
            "season": None,
            "season_start": None,
            "season_end": None,
            "season_current": None,
        }
    ]


def test_leagues_response_normalizer_handles_empty_response() -> None:
    output = normalize_api_football_leagues_response(_leagues_payload([]))

    assert output["normalized_count"] == 0
    assert output["leagues"] == []


def test_teams_response_normalizer_normalizes_fake_team_and_venue() -> None:
    output = normalize_api_football_teams_response(_teams_payload([_complete_team()]))

    assert output["provider"] == API_FOOTBALL_LEAGUES_TEAMS_NORMALIZER_PROVIDER
    assert output["endpoint"] == API_FOOTBALL_TEAMS_NORMALIZER_ENDPOINT
    assert output["mode"] == API_FOOTBALL_TEAMS_NORMALIZER_MODE
    assert isinstance(output["payload_hash"], str)
    assert len(output["payload_hash"]) == 64
    assert output["payload_top_level_keys"] == [
        "errors",
        "get",
        "paging",
        "parameters",
        "response",
        "results",
    ]
    assert output["normalized_count"] == 1
    assert output["db_writes"] is False
    assert output["prediction_created"] is False
    assert output["betting_created"] is False
    assert output["teams"] == [
        {
            "provider": "api-football",
            "provider_team_id": 33,
            "team_name": "Test Team",
            "team_code": "TST",
            "team_country": "Test Country",
            "team_founded": 1999,
            "team_national": False,
            "venue_provider_id": 44,
            "venue_name": "Test Venue",
            "venue_city": "Test City",
            "venue_capacity": 12000,
        }
    ]


def test_teams_response_normalizer_handles_missing_venue() -> None:
    output = normalize_api_football_teams_response(
        _teams_payload(
            [
                {
                    "team": {
                        "id": 34,
                        "name": "Venue Missing Team",
                        "code": "VMT",
                        "country": "Test Country",
                        "founded": None,
                        "national": True,
                    }
                }
            ]
        )
    )

    assert output["normalized_count"] == 1
    assert output["teams"] == [
        {
            "provider": "api-football",
            "provider_team_id": 34,
            "team_name": "Venue Missing Team",
            "team_code": "VMT",
            "team_country": "Test Country",
            "team_founded": None,
            "team_national": True,
            "venue_provider_id": None,
            "venue_name": None,
            "venue_city": None,
            "venue_capacity": None,
        }
    ]


def test_teams_response_normalizer_handles_empty_response() -> None:
    output = normalize_api_football_teams_response(_teams_payload([]))

    assert output["normalized_count"] == 0
    assert output["teams"] == []


def test_leagues_teams_response_normalizer_payload_hash_is_deterministic() -> None:
    payload_a = _leagues_payload([_complete_league()])
    payload_b = {
        "response": [_complete_league()],
        "paging": {"total": 1, "current": 1},
        "results": 1,
        "errors": [],
        "parameters": {"season": "2026"},
        "get": "leagues",
    }
    changed_payload = _leagues_payload([])

    output_a = normalize_api_football_leagues_response(payload_a)
    output_b = normalize_api_football_leagues_response(payload_b)
    changed_output = normalize_api_football_leagues_response(changed_payload)

    assert output_a["payload_hash"] == output_b["payload_hash"]
    assert output_a["payload_hash"] != changed_output["payload_hash"]


def test_leagues_teams_response_normalizers_do_not_return_provider_media_or_forbidden_fields() -> None:
    outputs = [
        normalize_api_football_leagues_response(_leagues_payload([_complete_league()])),
        normalize_api_football_teams_response(_teams_payload([_complete_team()])),
    ]

    serialized_normalized_rows = json.dumps(
        {
            "leagues": outputs[0]["leagues"],
            "teams": outputs[1]["teams"],
        },
        sort_keys=True,
    ).lower()

    forbidden_fragments = (
        _literal("raw", "_payload"),
        "logo",
        "flag",
        "image",
        "ignored_league_logo",
        "ignored_country_flag",
        "ignored_team_logo",
        "ignored_venue_image",
        "coverage",
        "odds",
        "bookmaker",
        "stake",
        "prediction",
        "betting",
    )
    for fragment in forbidden_fragments:
        assert fragment not in serialized_normalized_rows


@pytest.mark.parametrize(
    "normalizer",
    [normalize_api_football_leagues_response, normalize_api_football_teams_response],
)
def test_leagues_teams_response_normalizers_reject_non_mapping_payload(
    normalizer: object,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsResponseNormalizationError):
        normalizer(["response"])  # type: ignore[operator]


@pytest.mark.parametrize(
    "normalizer",
    [normalize_api_football_leagues_response, normalize_api_football_teams_response],
)
def test_leagues_teams_response_normalizers_reject_non_list_response(
    normalizer: object,
) -> None:
    with pytest.raises(ApiFootballLeaguesTeamsResponseNormalizationError, match="response"):
        normalizer({"response": {}})  # type: ignore[operator]


def test_leagues_teams_response_normalizers_do_not_use_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    assert normalize_api_football_leagues_response(
        _leagues_payload([_complete_league()])
    )["normalized_count"] == 2
    assert normalize_api_football_teams_response(
        _teams_payload([_complete_team()])
    )["normalized_count"] == 1


def test_leagues_teams_response_normalizer_source_has_no_transport_db_or_secret_material() -> None:
    module_source = inspect.getsource(normalizer_module)
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
        _literal("rapid", "api"),
        _literal("x", "-apisports-key"),
        _literal("api", "_key"),
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("raw", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source_lower


def test_leagues_teams_response_normalizer_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 38" in doc_text
    assert "read-only normalizer only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion" in doc_lower
    assert "no prediction" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 39" in doc_lower
    assert "fixtures + leagues + teams" in doc_lower


def test_leagues_teams_response_normalizer_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "57_API_FOOTBALL_LEAGUES_TEAMS_RESPONSE_NORMALIZERS.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
