from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import (
    api_football_fixture_baseline_analytics_engine as analytics_module,
)
from app.modules.providers.api_football_fixture_baseline_analytics_engine import (
    build_fixture_baseline_analytics,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "62_BASELINE_ANALYTICS_ENGINE_WITHOUT_OFFICIAL_PREDICTION.md"
)
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "043-phase-43-baseline-analytics-engine-without-official-prediction.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "043-phase-43-baseline-analytics-engine-without-official-prediction.md"
)
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "read_only",
    "db_writes",
    "prediction_created",
    "official_prediction_created",
    "betting_created",
    "ml_model_used",
    "confidence_score_created",
    "analytics_schema_version",
    "source_mode",
    "candidate_count",
    "accepted_count",
    "rejected_count",
    "fixture_status_short_counts",
    "league_counts",
    "season_counts",
    "completed_fixture_count",
    "live_fixture_count",
    "scheduled_fixture_count",
    "cancelled_or_postponed_count",
    "goals_summary",
    "descriptive_signals",
    "blocking_reasons",
}
FORBIDDEN_OUTPUT_KEYS = {
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
    "final_pick",
    "win_probability",
    "bet_signal",
}


def _candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "provider": "api-football",
        "provider_fixture_id": 101,
        "provider_league_id": 39,
        "provider_season": 2026,
        "fixture_date": "2026-07-07T18:00:00+00:00",
        "fixture_timezone": "UTC",
        "fixture_status_short": "FT",
        "fixture_status_long": "Match Finished",
        "home_team_provider_id": 33,
        "away_team_provider_id": 34,
        "goals_home": 2,
        "goals_away": 1,
        "score_halftime_home": 1,
        "score_halftime_away": 0,
        "score_fulltime_home": 2,
        "score_fulltime_away": 1,
        "payload_hash": "abc123",
        "fetched_at": "2026-07-07T12:00:00+00:00",
        "source_mode": "staging_read_only",
        "feature_schema_version": "fixture_features_v1",
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
        "recommended_outcome": "blocked-recommendation",
        "suggested_bet": "blocked-suggested-bet",
        "final_pick": "blocked-final-pick",
        "win_probability": 0.8,
        "bet_signal": "blocked-bet-signal",
    }
    candidate.update(overrides)
    return candidate


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for nested_value in value.values():
            keys.update(_all_keys(nested_value))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_all_keys(item))
        return keys
    return set()


def test_fixture_baseline_analytics_module_and_function_exist() -> None:
    assert hasattr(analytics_module, "build_fixture_baseline_analytics")
    assert callable(build_fixture_baseline_analytics)


def test_fixture_baseline_analytics_aggregates_accepted_candidates() -> None:
    result = build_fixture_baseline_analytics(
        [
            _candidate(provider_fixture_id=101, fixture_status_short="FT"),
            _candidate(
                provider_fixture_id=102,
                fixture_status_short="FT",
                score_fulltime_home=0,
                score_fulltime_away=0,
            ),
            _candidate(
                provider_fixture_id=103,
                provider_league_id=140,
                provider_season=2025,
                fixture_status_short="1H",
                score_fulltime_home=None,
                score_fulltime_away=None,
            ),
            _candidate(
                provider_fixture_id=104,
                provider_league_id=140,
                provider_season=2025,
                fixture_status_short="NS",
                score_fulltime_home=None,
                score_fulltime_away=None,
            ),
            _candidate(
                provider_fixture_id=105,
                provider_league_id=2,
                fixture_status_short="PST",
                score_fulltime_home=None,
                score_fulltime_away=None,
            ),
        ]
    )

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == (
        "fixture_baseline_analytics_without_official_prediction"
    )
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["official_prediction_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["confidence_score_created"] is False
    assert result["analytics_schema_version"] == "fixture_baseline_analytics_v1"
    assert result["source_mode"] == "feature_snapshot_contract"
    assert result["candidate_count"] == 5
    assert result["accepted_count"] == 5
    assert result["rejected_count"] == 0
    assert result["fixture_status_short_counts"] == {
        "1H": 1,
        "FT": 2,
        "NS": 1,
        "PST": 1,
    }
    assert result["league_counts"] == {"2": 1, "39": 2, "140": 2}
    assert result["season_counts"] == {"2025": 2, "2026": 3}
    assert result["completed_fixture_count"] == 2
    assert result["live_fixture_count"] == 1
    assert result["scheduled_fixture_count"] == 1
    assert result["cancelled_or_postponed_count"] == 1
    assert result["goals_summary"] == {
        "fixtures_with_fulltime_scores": 2,
        "average_total_goals": 1.5,
        "home_goals_total": 2,
        "away_goals_total": 1,
    }
    assert result["descriptive_signals"] == {
        "has_completed_sample": True,
        "has_live_sample": True,
        "has_scheduled_sample": True,
        "sample_is_empty": False,
    }
    assert result["blocking_reasons"] == []


def test_fixture_baseline_analytics_uses_custom_metadata() -> None:
    result = build_fixture_baseline_analytics(
        [_candidate()],
        analytics_schema_version=" fixture_baseline_analytics_v2 ",
        source_mode=" phase_43_test ",
    )

    assert result["analytics_schema_version"] == "fixture_baseline_analytics_v2"
    assert result["source_mode"] == "phase_43_test"
    assert result["accepted_count"] == 1
    assert result["blocking_reasons"] == []


def test_fixture_baseline_analytics_handles_empty_sample() -> None:
    result = build_fixture_baseline_analytics([])

    assert result["candidate_count"] == 0
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 0
    assert result["fixture_status_short_counts"] == {}
    assert result["league_counts"] == {}
    assert result["season_counts"] == {}
    assert result["completed_fixture_count"] == 0
    assert result["live_fixture_count"] == 0
    assert result["scheduled_fixture_count"] == 0
    assert result["cancelled_or_postponed_count"] == 0
    assert result["goals_summary"] == {
        "fixtures_with_fulltime_scores": 0,
        "average_total_goals": None,
        "home_goals_total": 0,
        "away_goals_total": 0,
    }
    assert result["descriptive_signals"] == {
        "has_completed_sample": False,
        "has_live_sample": False,
        "has_scheduled_sample": False,
        "sample_is_empty": True,
    }
    assert result["blocking_reasons"] == []


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        (
            {"analytics_schema_version": "   "},
            "analytics_schema_version_missing",
        ),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_fixture_baseline_analytics_blocks_missing_global_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_fixture_baseline_analytics([_candidate()], **kwargs)

    assert result["candidate_count"] == 1
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["descriptive_signals"]["sample_is_empty"] is True
    assert expected_reason in result["blocking_reasons"]


@pytest.mark.parametrize(
    ("field_name", "bad_value", "expected_reason"),
    [
        ("provider", "other-provider", "wrong_provider"),
        ("provider_fixture_id", None, "provider_fixture_id_missing"),
        ("provider_fixture_id", 0, "provider_fixture_id_missing"),
        ("provider_league_id", None, "provider_league_id_missing"),
        ("provider_league_id", True, "provider_league_id_missing"),
        ("fixture_status_short", None, "fixture_status_short_missing"),
        ("fixture_status_short", "   ", "fixture_status_short_missing"),
    ],
)
def test_fixture_baseline_analytics_rejects_invalid_candidates(
    field_name: str,
    bad_value: object,
    expected_reason: str,
) -> None:
    result = build_fixture_baseline_analytics(
        [_candidate(**{field_name: bad_value})]
    )

    assert result["candidate_count"] == 1
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert result["fixture_status_short_counts"] == {}
    assert result["descriptive_signals"]["sample_is_empty"] is True
    assert expected_reason in result["blocking_reasons"]


def test_fixture_baseline_analytics_counts_mixed_batch() -> None:
    result = build_fixture_baseline_analytics(
        [
            _candidate(provider_fixture_id=101, fixture_status_short=" ns "),
            _candidate(provider_fixture_id=None),
            _candidate(provider="other-provider"),
        ]
    )

    assert result["candidate_count"] == 3
    assert result["accepted_count"] == 1
    assert result["rejected_count"] == 2
    assert result["fixture_status_short_counts"] == {"NS": 1}
    assert result["scheduled_fixture_count"] == 1
    assert result["blocking_reasons"] == [
        "provider_fixture_id_missing",
        "wrong_provider",
    ]


def test_fixture_baseline_analytics_does_not_confuse_missing_scores_with_zero() -> None:
    result = build_fixture_baseline_analytics(
        [
            _candidate(
                provider_fixture_id=101,
                score_fulltime_home=0,
                score_fulltime_away=0,
            ),
            _candidate(
                provider_fixture_id=102,
                score_fulltime_home=None,
                score_fulltime_away=None,
            ),
        ]
    )

    assert result["goals_summary"] == {
        "fixtures_with_fulltime_scores": 1,
        "average_total_goals": 0.0,
        "home_goals_total": 0,
        "away_goals_total": 0,
    }


def test_fixture_baseline_analytics_output_does_not_echo_forbidden_material() -> None:
    result = build_fixture_baseline_analytics([_candidate()])
    serialized_result = json.dumps(result, sort_keys=True)
    output_keys = _all_keys(result)

    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(output_keys)
    assert "blocked" not in serialized_result
    assert "api_key" not in serialized_result
    assert "auth" not in serialized_result
    assert "secret" not in serialized_result
    assert "token" not in serialized_result
    assert "odds" not in serialized_result
    assert "bookmaker" not in serialized_result
    assert "stake" not in serialized_result
    assert "model_output" not in serialized_result
    assert "probability" not in serialized_result
    assert "recommended_outcome" not in serialized_result
    assert "suggested_bet" not in serialized_result
    assert "final_pick" not in serialized_result
    assert "win_probability" not in serialized_result
    assert "bet_signal" not in serialized_result


def test_fixture_baseline_analytics_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(analytics_module)
    module_source_lower = module_source.lower()
    module_source_upper = module_source.upper()

    assert "INSERT INTO" not in module_source_upper
    assert "UPDATE" not in module_source_upper
    assert "DELETE" not in module_source_upper
    forbidden_lower_fragments = (
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
    )
    for fragment in forbidden_lower_fragments:
        assert fragment not in module_source_lower


def test_fixture_baseline_analytics_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 43" in doc_text
    assert "baseline analytics only" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no ml" in doc_lower
    assert "no confidence scoring" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 44" in doc_lower
    assert "kairos prediction protocol gate" in doc_lower
    assert "not yet free prediction" in doc_lower


def test_fixture_baseline_analytics_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "62_BASELINE_ANALYTICS_ENGINE_WITHOUT_OFFICIAL_PREDICTION.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
