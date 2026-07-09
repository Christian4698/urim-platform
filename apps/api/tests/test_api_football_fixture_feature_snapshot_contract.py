from __future__ import annotations

from datetime import datetime, timezone
import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import (
    api_football_fixture_feature_snapshot_contract as contract_module,
)
from app.modules.providers.api_football_fixture_feature_snapshot_contract import (
    ALLOWED_FEATURE_KEYS,
    build_fixture_feature_snapshot_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "61_FEATURE_SNAPSHOT_CONTRACT_WITHOUT_ML.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "042-phase-42-feature-snapshot-contract-without-ml.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "042-phase-42-feature-snapshot-contract-without-ml.md"
)
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "target_table",
    "read_only",
    "db_writes",
    "prediction_created",
    "betting_created",
    "ml_model_used",
    "confidence_score_created",
    "feature_schema_version",
    "source_mode",
    "candidate_count",
    "accepted_count",
    "rejected_count",
    "allowed_feature_keys",
    "snapshot_candidates",
    "blocking_reasons",
}
EXPECTED_ALLOWED_FEATURE_KEYS = [
    "provider",
    "provider_fixture_id",
    "provider_league_id",
    "provider_season",
    "fixture_date",
    "fixture_timezone",
    "fixture_status_short",
    "fixture_status_long",
    "home_team_provider_id",
    "away_team_provider_id",
    "goals_home",
    "goals_away",
    "score_halftime_home",
    "score_halftime_away",
    "score_fulltime_home",
    "score_fulltime_away",
    "payload_hash",
    "fetched_at",
    "source_mode",
    "feature_schema_version",
]
FORBIDDEN_SNAPSHOT_FIELDS = {
    "home_team_name",
    "away_team_name",
    "raw_payload",
    "api_key",
    "auth",
    "secret",
    "token",
    "odds",
    "bookmaker",
    "stake",
    "prediction",
    "predictions",
    "betting",
    "model_output",
    "confidence_score",
    "probability",
    "recommended_outcome",
    "suggested_bet",
}


def _literal(*parts: str) -> str:
    return "".join(parts)


def _complete_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
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
        "fetched_at": datetime(2026, 7, 7, 12, 0, tzinfo=timezone.utc),
        "source_mode": "phase_40_read_only_test",
        "raw_payload": {"blocked": True},
        "api_key": "blocked-api-key",
        "auth": "blocked-auth",
        "secret": "blocked-secret",
        "token": "blocked-token",
        "odds": {"home": 1.5},
        "bookmaker": "blocked-bookmaker",
        "stake": 100,
        "prediction": "blocked-prediction",
        "predictions": ["blocked-predictions"],
        "betting": "blocked-betting",
        "model_output": {"blocked": True},
        "confidence_score": 0.9,
        "probability": 0.7,
        "recommended_outcome": "blocked",
        "suggested_bet": "blocked",
    }
    row.update(overrides)
    return row


def test_fixture_feature_snapshot_contract_module_and_function_exist() -> None:
    assert hasattr(contract_module, "build_fixture_feature_snapshot_contract")
    assert callable(build_fixture_feature_snapshot_contract)


def test_fixture_feature_snapshot_contract_accepts_complete_row() -> None:
    result = build_fixture_feature_snapshot_contract([_complete_row()])

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "fixture_feature_snapshot_contract_without_ml"
    assert result["target_table"] == "feature_snapshots"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["confidence_score_created"] is False
    assert result["feature_schema_version"] == "fixture_features_v1"
    assert result["source_mode"] == "staging_read_only"
    assert result["candidate_count"] == 1
    assert result["accepted_count"] == 1
    assert result["rejected_count"] == 0
    assert result["allowed_feature_keys"] == EXPECTED_ALLOWED_FEATURE_KEYS
    assert result["blocking_reasons"] == []

    candidate = result["snapshot_candidates"][0]
    assert set(candidate) == set(ALLOWED_FEATURE_KEYS)
    assert candidate["provider"] == "api-football"
    assert candidate["provider_fixture_id"] == 101
    assert candidate["provider_league_id"] == 39
    assert candidate["fixture_date"] == "2026-07-07T18:00:00+00:00"
    assert candidate["fetched_at"] == "2026-07-07T12:00:00+00:00"
    assert candidate["source_mode"] == "staging_read_only"
    assert candidate["feature_schema_version"] == "fixture_features_v1"


def test_fixture_feature_snapshot_contract_uses_custom_metadata() -> None:
    result = build_fixture_feature_snapshot_contract(
        [_complete_row()],
        feature_schema_version=" fixture_features_v2 ",
        source_mode=" phase_42_contract_test ",
    )

    assert result["feature_schema_version"] == "fixture_features_v2"
    assert result["source_mode"] == "phase_42_contract_test"
    assert result["snapshot_candidates"][0]["feature_schema_version"] == (
        "fixture_features_v2"
    )
    assert result["snapshot_candidates"][0]["source_mode"] == "phase_42_contract_test"


def test_fixture_feature_snapshot_contract_blocks_empty_rows() -> None:
    result = build_fixture_feature_snapshot_contract([])

    assert result["candidate_count"] == 0
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 0
    assert result["snapshot_candidates"] == []
    assert result["blocking_reasons"] == ["no_rows"]


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"feature_schema_version": "   "}, "feature_schema_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_fixture_feature_snapshot_contract_blocks_missing_global_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_fixture_feature_snapshot_contract([_complete_row()], **kwargs)

    assert result["candidate_count"] == 1
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["snapshot_candidates"] == []
    assert expected_reason in result["blocking_reasons"]


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected_reason"),
    [
        ("provider", "other-provider", "wrong_provider"),
        ("provider_fixture_id", None, "provider_fixture_id_missing"),
        ("provider_fixture_id", 0, "provider_fixture_id_missing"),
        ("provider_league_id", None, "provider_league_id_missing"),
        ("provider_league_id", True, "provider_league_id_missing"),
        ("fixture_date", None, "fixture_date_missing"),
        ("fixture_date", "   ", "fixture_date_missing"),
        ("payload_hash", None, "payload_hash_missing"),
        ("payload_hash", "", "payload_hash_missing"),
    ],
)
def test_fixture_feature_snapshot_contract_rejects_invalid_rows(
    field_name: str,
    bad_value: object,
    expected_reason: str,
) -> None:
    result = build_fixture_feature_snapshot_contract(
        [_complete_row(**{field_name: bad_value})]
    )

    assert result["candidate_count"] == 1
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["snapshot_candidates"] == []
    assert expected_reason in result["blocking_reasons"]


def test_fixture_feature_snapshot_contract_counts_mixed_batch() -> None:
    result = build_fixture_feature_snapshot_contract(
        [
            _complete_row(provider_fixture_id=101),
            _complete_row(provider_fixture_id=None),
            _complete_row(provider="other-provider"),
        ]
    )

    assert result["candidate_count"] == 3
    assert result["accepted_count"] == 1
    assert result["rejected_count"] == 2
    assert len(result["snapshot_candidates"]) == 1
    assert result["blocking_reasons"] == [
        "provider_fixture_id_missing",
        "wrong_provider",
    ]


def test_fixture_feature_snapshot_contract_candidates_exclude_forbidden_fields() -> None:
    result = build_fixture_feature_snapshot_contract([_complete_row()])
    candidate = result["snapshot_candidates"][0]
    serialized_candidate = json.dumps(candidate, sort_keys=True)

    assert FORBIDDEN_SNAPSHOT_FIELDS.isdisjoint(candidate)
    assert "Home FC" not in serialized_candidate
    assert "Away FC" not in serialized_candidate
    assert "blocked" not in serialized_candidate
    for forbidden_field in FORBIDDEN_SNAPSHOT_FIELDS:
        assert forbidden_field not in serialized_candidate


def test_fixture_feature_snapshot_contract_allowed_feature_keys_are_strict() -> None:
    result = build_fixture_feature_snapshot_contract([_complete_row()])

    assert result["allowed_feature_keys"] == EXPECTED_ALLOWED_FEATURE_KEYS
    assert set(result["allowed_feature_keys"]).isdisjoint(FORBIDDEN_SNAPSHOT_FIELDS)


def test_fixture_feature_snapshot_contract_source_has_no_writes_provider_calls_or_secret_material() -> None:
    module_source = inspect.getsource(contract_module).lower()

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
        _literal("bear", "er"),
        _literal("tok", "en"),
        _literal("sec", "ret"),
        _literal("raw", "_payload"),
    )
    for fragment in forbidden_fragments:
        assert fragment not in module_source


def test_fixture_feature_snapshot_contract_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 42" in doc_text
    assert "feature snapshot contract only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no prediction" in doc_lower
    assert "no ml" in doc_lower
    assert "no confidence scoring" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 43" in doc_lower
    assert "baseline analytics engine" in doc_lower
    assert "without official prediction" in doc_lower


def test_fixture_feature_snapshot_contract_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "61_FEATURE_SNAPSHOT_CONTRACT_WITHOUT_ML.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
