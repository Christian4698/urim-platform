from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import api_football_fixture_staging_ingestion_gate as gate_module
from app.modules.providers.api_football_fixture_staging_ingestion_gate import (
    build_fixture_staging_ingestion_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "55_FIXTURE_STAGING_INGESTION_GATE.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "036-phase-36-fixture-staging-ingestion-gate.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "036-phase-36-fixture-staging-ingestion-gate.md"
)


def _literal(*parts: str) -> str:
    return "".join(parts)


def _complete_fixture(fixture_id: int = 101) -> dict[str, object]:
    return {
        "provider": "api-football",
        "provider_fixture_id": fixture_id,
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
        "goals_home": None,
        "goals_away": None,
        "score_halftime_home": None,
        "score_halftime_away": None,
        "score_fulltime_home": None,
        "score_fulltime_away": None,
    }


def _gate(
    fixtures: list[dict[str, object]],
    *,
    payload_hash: str = "abc123",
    payload_top_level_keys: list[str] | None = None,
    source_mode: str = "phase_32_compact_smoke",
) -> dict[str, object]:
    keys = ["response"] if payload_top_level_keys is None else payload_top_level_keys
    return build_fixture_staging_ingestion_gate(
        fixtures,
        payload_hash=payload_hash,
        payload_top_level_keys=keys,
        source_mode=source_mode,
    )


def test_fixture_staging_ingestion_gate_accepts_clean_batch() -> None:
    result = _gate([_complete_fixture(101), _complete_fixture(102)])

    assert result["provider"] == "api-football"
    assert result["target_table"] == "api_football_fixture_staging"
    assert result["mode"] == "fixture_staging_ingestion_gate_only"
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["betting_created"] is False
    assert result["payload_hash_present"] is True
    assert result["payload_top_level_keys_present"] is True
    assert result["candidate_count"] == 2
    assert result["accepted_count"] == 2
    assert result["rejected_count"] == 0
    assert result["duplicate_provider_fixture_ids"] == []
    assert result["missing_required_fields"] == {}
    assert result["ready_for_future_staging_ingestion"] is True
    assert result["blocking_reasons"] == []

    serialized_result = json.dumps(result, sort_keys=True)
    assert "Home FC" not in serialized_result
    assert "Away FC" not in serialized_result


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"source_mode": "   "}, "source_mode_missing"),
        ({"payload_hash": "   "}, "payload_hash_missing"),
        ({"payload_top_level_keys": []}, "payload_top_level_keys_missing"),
    ],
)
def test_fixture_staging_ingestion_gate_blocks_missing_global_evidence(
    kwargs: dict[str, object],
    expected_reason: str,
) -> None:
    result = _gate([_complete_fixture()], **kwargs)

    assert result["ready_for_future_staging_ingestion"] is False
    assert expected_reason in result["blocking_reasons"]


def test_fixture_staging_ingestion_gate_blocks_empty_batch() -> None:
    result = _gate([])

    assert result["candidate_count"] == 0
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 0
    assert result["ready_for_future_staging_ingestion"] is False
    assert "no_candidates" in result["blocking_reasons"]


def test_fixture_staging_ingestion_gate_rejects_wrong_provider() -> None:
    fixture = _complete_fixture()
    fixture["provider"] = "other-provider"

    result = _gate([fixture])

    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["ready_for_future_staging_ingestion"] is False
    assert "wrong_provider" in result["blocking_reasons"]


def test_fixture_staging_ingestion_gate_rejects_missing_provider_fixture_id() -> None:
    fixture = _complete_fixture()
    fixture.pop("provider_fixture_id")

    result = _gate([fixture])

    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["missing_required_fields"] == {
        "candidate:0": ["provider_fixture_id"]
    }
    assert "missing_required_fields" in result["blocking_reasons"]


def test_fixture_staging_ingestion_gate_lists_missing_required_fields() -> None:
    fixture = _complete_fixture(303)
    fixture["fixture_timezone"] = " "
    fixture["home_team_provider_id"] = None
    fixture["away_team_name"] = ""

    result = _gate([fixture])

    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["missing_required_fields"] == {
        "provider_fixture_id:303": [
            "fixture_timezone",
            "home_team_provider_id",
            "away_team_name",
        ]
    }


def test_fixture_staging_ingestion_gate_detects_duplicate_provider_fixture_ids() -> None:
    result = _gate(
        [
            _complete_fixture(101),
            _complete_fixture(101),
            _complete_fixture(102),
        ]
    )

    assert result["duplicate_provider_fixture_ids"] == [101]
    assert result["accepted_count"] == 1
    assert result["rejected_count"] == 2
    assert result["ready_for_future_staging_ingestion"] is False
    assert "duplicate_provider_fixture_ids" in result["blocking_reasons"]


@pytest.mark.parametrize(
    "forbidden_field",
    ["odds", "bookmaker", "stake", "prediction", "betting"],
)
def test_fixture_staging_ingestion_gate_rejects_forbidden_fixture_fields(
    forbidden_field: str,
) -> None:
    fixture = _complete_fixture()
    fixture[forbidden_field] = "blocked"

    result = _gate([fixture])

    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["ready_for_future_staging_ingestion"] is False
    assert "forbidden_fixture_fields" in result["blocking_reasons"]


def test_fixture_staging_ingestion_gate_source_has_no_runtime_writes_or_network() -> None:
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
        "urlopen",
        "socket",
        _literal("api", "_key"),
        _literal("x", "-apisports-key"),
        _literal("v3", ".football", ".api-sports", ".io"),
        _literal("raw", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source


def test_fixture_staging_ingestion_gate_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 36" in doc_text
    assert "no db write in phase 36" in doc_lower
    assert "no real api call" in doc_lower
    assert "no prediction" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "public-safe" in doc_lower
    assert "phase 37/38" in doc_lower
    assert "leagues/teams read-only" in doc_lower


def test_fixture_staging_ingestion_gate_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "55_FIXTURE_STAGING_INGESTION_GATE.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
