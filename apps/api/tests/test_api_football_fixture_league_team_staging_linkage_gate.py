from __future__ import annotations

import inspect
import json
import socket
from pathlib import Path

import pytest

from app.modules.providers import (
    api_football_fixture_league_team_staging_linkage_gate as gate_module,
)
from app.modules.providers.api_football_fixture_league_team_staging_linkage_gate import (
    build_fixture_league_team_staging_linkage_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "58_API_FOOTBALL_FIXTURE_LEAGUE_TEAM_STAGING_LINKAGE_GATE.md"
)
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "039-phase-39-fixtures-leagues-teams-staging-linkage-gate.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "039-phase-39-fixtures-leagues-teams-staging-linkage-gate.md"
)

EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "target_table",
    "db_writes",
    "prediction_created",
    "betting_created",
    "source_mode",
    "fixture_count",
    "league_count",
    "team_count",
    "linked_fixture_count",
    "unlinked_fixture_count",
    "missing_league_reference_count",
    "missing_home_team_reference_count",
    "missing_away_team_reference_count",
    "duplicate_league_ids",
    "duplicate_team_ids",
    "ready_for_future_staging_linkage",
    "blocking_reasons",
}


def _literal(*parts: str) -> str:
    return "".join(parts)


def _complete_fixture(
    fixture_id: int = 101,
    *,
    league_id: int = 39,
    home_team_id: int = 33,
    away_team_id: int = 34,
) -> dict[str, object]:
    return {
        "provider": "api-football",
        "provider_fixture_id": fixture_id,
        "provider_league_id": league_id,
        "provider_season": 2026,
        "fixture_date": "2026-07-07T18:00:00+00:00",
        "fixture_timezone": "UTC",
        "fixture_status_short": "NS",
        "fixture_status_long": "Not Started",
        "home_team_provider_id": home_team_id,
        "home_team_name": "Home FC",
        "away_team_provider_id": away_team_id,
        "away_team_name": "Away FC",
    }


def _league(league_id: int = 39, *, season: int = 2026) -> dict[str, object]:
    return {
        "provider": "api-football",
        "provider_league_id": league_id,
        "league_name": "Test League",
        "league_type": "League",
        "country_name": "Test Country",
        "country_code": "TC",
        "season": season,
    }


def _team(team_id: int) -> dict[str, object]:
    return {
        "provider": "api-football",
        "provider_team_id": team_id,
        "team_name": f"Test Team {team_id}",
        "team_code": "TST",
        "team_country": "Test Country",
    }


def _gate(
    fixtures: list[dict[str, object]],
    *,
    leagues: list[dict[str, object]] | None = None,
    teams: list[dict[str, object]] | None = None,
    source_mode: str = "phase_39_linkage_dry_run",
    payload_hashes: dict[str, str] | None = None,
) -> dict[str, object]:
    return build_fixture_league_team_staging_linkage_gate(
        fixtures,
        [_league()] if leagues is None else leagues,
        [_team(33), _team(34)] if teams is None else teams,
        source_mode=source_mode,
        payload_hashes=payload_hashes,
    )


def test_fixture_league_team_linkage_gate_module_and_function_exist() -> None:
    assert hasattr(gate_module, "build_fixture_league_team_staging_linkage_gate")
    assert callable(build_fixture_league_team_staging_linkage_gate)


def test_fixture_league_team_linkage_gate_accepts_clean_batch() -> None:
    result = _gate(
        [_complete_fixture(101), _complete_fixture(102)],
        payload_hashes={"fixtures": "abc123", "leagues": "def456"},
    )

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "fixture_league_team_staging_linkage_gate_only"
    assert result["target_table"] == "api_football_fixture_staging"
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["betting_created"] is False
    assert result["source_mode"] == "phase_39_linkage_dry_run"
    assert result["fixture_count"] == 2
    assert result["league_count"] == 1
    assert result["team_count"] == 2
    assert result["linked_fixture_count"] == 2
    assert result["unlinked_fixture_count"] == 0
    assert result["missing_league_reference_count"] == 0
    assert result["missing_home_team_reference_count"] == 0
    assert result["missing_away_team_reference_count"] == 0
    assert result["duplicate_league_ids"] == []
    assert result["duplicate_team_ids"] == []
    assert result["ready_for_future_staging_linkage"] is True
    assert result["blocking_reasons"] == []

    serialized_result = json.dumps(result, sort_keys=True)
    assert "fixtures" not in result
    assert "payload_hashes" not in result
    assert "raw_payload" not in serialized_result
    assert "Home FC" not in serialized_result
    assert "Away FC" not in serialized_result
    assert "Test Team" not in serialized_result
    assert "Test League" not in serialized_result


def test_fixture_league_team_linkage_gate_blocks_empty_source_mode() -> None:
    result = _gate([_complete_fixture()], source_mode="   ")

    assert result["source_mode"] == ""
    assert result["linked_fixture_count"] == 1
    assert result["unlinked_fixture_count"] == 0
    assert result["ready_for_future_staging_linkage"] is False
    assert "source_mode_missing" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_blocks_empty_fixture_batch() -> None:
    result = _gate([])

    assert result["fixture_count"] == 0
    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 0
    assert result["ready_for_future_staging_linkage"] is False
    assert "no_fixtures" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_blocks_wrong_fixture_provider() -> None:
    fixture = _complete_fixture()
    fixture["provider"] = "other-provider"

    result = _gate([fixture])

    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 1
    assert result["ready_for_future_staging_linkage"] is False
    assert "wrong_provider" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_counts_missing_league_reference() -> None:
    result = _gate([_complete_fixture(league_id=999)])

    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 1
    assert result["missing_league_reference_count"] == 1
    assert result["missing_home_team_reference_count"] == 0
    assert result["missing_away_team_reference_count"] == 0
    assert result["ready_for_future_staging_linkage"] is False
    assert "missing_league_reference" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_counts_missing_home_team_reference() -> None:
    result = _gate([_complete_fixture(home_team_id=999)])

    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 1
    assert result["missing_league_reference_count"] == 0
    assert result["missing_home_team_reference_count"] == 1
    assert result["missing_away_team_reference_count"] == 0
    assert result["ready_for_future_staging_linkage"] is False
    assert "missing_home_team_reference" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_counts_missing_away_team_reference() -> None:
    result = _gate([_complete_fixture(away_team_id=999)])

    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 1
    assert result["missing_league_reference_count"] == 0
    assert result["missing_home_team_reference_count"] == 0
    assert result["missing_away_team_reference_count"] == 1
    assert result["ready_for_future_staging_linkage"] is False
    assert "missing_away_team_reference" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_detects_duplicate_league_ids_by_id_only() -> None:
    result = _gate(
        [_complete_fixture()],
        leagues=[_league(39, season=2026), _league(39, season=2027)],
    )

    assert result["duplicate_league_ids"] == [39]
    assert result["missing_league_reference_count"] == 0
    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 1
    assert result["ready_for_future_staging_linkage"] is False
    assert "duplicate_league_ids" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_detects_duplicate_team_ids() -> None:
    result = _gate(
        [_complete_fixture()],
        teams=[_team(33), _team(33), _team(34)],
    )

    assert result["duplicate_team_ids"] == [33]
    assert result["missing_home_team_reference_count"] == 0
    assert result["missing_away_team_reference_count"] == 0
    assert result["linked_fixture_count"] == 0
    assert result["unlinked_fixture_count"] == 1
    assert result["ready_for_future_staging_linkage"] is False
    assert "duplicate_team_ids" in result["blocking_reasons"]


@pytest.mark.parametrize(
    ("collection_name", "forbidden_field"),
    [
        (collection_name, forbidden_field)
        for collection_name in ["fixture", "league", "team"]
        for forbidden_field in ["odds", "bookmaker", "stake", "prediction", "betting"]
    ],
)
def test_fixture_league_team_linkage_gate_blocks_forbidden_fields(
    collection_name: str,
    forbidden_field: str,
) -> None:
    fixture = _complete_fixture()
    league = _league()
    team = _team(33)
    if collection_name == "fixture":
        fixture[forbidden_field] = "blocked"
    elif collection_name == "league":
        league[forbidden_field] = "blocked"
    else:
        team[forbidden_field] = "blocked"

    result = _gate([fixture], leagues=[league], teams=[team, _team(34)])

    assert result["ready_for_future_staging_linkage"] is False
    assert "forbidden_fields" in result["blocking_reasons"]


def test_fixture_league_team_linkage_gate_does_not_open_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network must not be used")

    monkeypatch.setattr(socket, "create_connection", fail_network)

    result = _gate([_complete_fixture()])

    assert result["ready_for_future_staging_linkage"] is True


def test_fixture_league_team_linkage_gate_source_has_no_runtime_writes_or_network() -> None:
    module_source = inspect.getsource(gate_module).lower()

    forbidden_fragments = (
        _literal("in", "sert"),
        "upsert",
        "session.add",
        ".execute(",
        "sqlalchemy",
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
        _literal("author", "ization"),
        _literal("bear", "er"),
        _literal("raw", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source


def test_fixture_league_team_linkage_gate_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 39" in doc_text
    assert "dry-run/in-memory only" in doc_lower
    assert "no db write" in doc_lower
    assert "no real api call" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no prediction" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 40" in doc_lower
    assert "read-only internal api" in doc_lower


def test_fixture_league_team_linkage_gate_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "58_API_FOOTBALL_FIXTURE_LEAGUE_TEAM_STAGING_LINKAGE_GATE.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
