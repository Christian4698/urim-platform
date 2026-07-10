from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import kairos_prediction_protocol_gate as gate_module
from app.modules.providers.kairos_prediction_protocol_gate import (
    build_kairos_prediction_protocol_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "63_KAIROS_PREDICTION_PROTOCOL_GATE.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "044-phase-44-kairos-prediction-protocol-gate.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "044-phase-44-kairos-prediction-protocol-gate.md"
)
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "protocol_version",
    "source_mode",
    "read_only",
    "db_writes",
    "prediction_created",
    "official_prediction_created",
    "offline_prediction_created",
    "betting_created",
    "ml_model_used",
    "confidence_score_created",
    "allowed_for_future_offline_prediction_sandbox",
    "required_inputs_present",
    "baseline_sample_accepted",
    "descriptive_only_confirmed",
    "candidate_count",
    "accepted_count",
    "rejected_count",
    "completed_fixture_count",
    "scheduled_fixture_count",
    "has_completed_sample",
    "has_scheduled_sample",
    "blocking_reasons",
}
FORBIDDEN_EXACT_OUTPUT_KEYS = {
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


def _baseline(**overrides: object) -> dict[str, object]:
    baseline: dict[str, object] = {
        "provider": "api-football",
        "mode": "fixture_baseline_analytics_without_official_prediction",
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "official_prediction_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "analytics_schema_version": "fixture_baseline_analytics_v1",
        "source_mode": "feature_snapshot_contract",
        "candidate_count": 3,
        "accepted_count": 3,
        "rejected_count": 0,
        "fixture_status_short_counts": {"FT": 2, "NS": 1},
        "league_counts": {"39": 3},
        "season_counts": {"2026": 3},
        "completed_fixture_count": 2,
        "live_fixture_count": 0,
        "scheduled_fixture_count": 1,
        "cancelled_or_postponed_count": 0,
        "goals_summary": {
            "fixtures_with_fulltime_scores": 2,
            "average_total_goals": 2.5,
            "home_goals_total": 3,
            "away_goals_total": 2,
        },
        "descriptive_signals": {
            "has_completed_sample": True,
            "has_live_sample": False,
            "has_scheduled_sample": True,
            "sample_is_empty": False,
        },
        "blocking_reasons": [],
    }
    baseline.update(overrides)
    return baseline


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


def _assert_blocked(
    baseline: dict[str, object],
    expected_reason: str,
) -> dict[str, object]:
    result = build_kairos_prediction_protocol_gate(baseline)

    assert result["allowed_for_future_offline_prediction_sandbox"] is False
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_prediction_protocol_gate_module_and_function_exist() -> None:
    assert hasattr(gate_module, "build_kairos_prediction_protocol_gate")
    assert callable(build_kairos_prediction_protocol_gate)


def test_kairos_prediction_protocol_gate_allows_valid_baseline() -> None:
    result = build_kairos_prediction_protocol_gate(_baseline())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_prediction_protocol_gate_only"
    assert result["protocol_version"] == "kairos_prediction_protocol_v1"
    assert result["source_mode"] == "baseline_analytics"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["prediction_created"] is False
    assert result["official_prediction_created"] is False
    assert result["offline_prediction_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["confidence_score_created"] is False
    assert result["allowed_for_future_offline_prediction_sandbox"] is True
    assert result["required_inputs_present"] is True
    assert result["baseline_sample_accepted"] is True
    assert result["descriptive_only_confirmed"] is True
    assert result["candidate_count"] == 3
    assert result["accepted_count"] == 3
    assert result["rejected_count"] == 0
    assert result["completed_fixture_count"] == 2
    assert result["scheduled_fixture_count"] == 1
    assert result["has_completed_sample"] is True
    assert result["has_scheduled_sample"] is True
    assert result["blocking_reasons"] == []


def test_kairos_prediction_protocol_gate_uses_custom_metadata() -> None:
    result = build_kairos_prediction_protocol_gate(
        _baseline(),
        protocol_version=" kairos_prediction_protocol_v2 ",
        source_mode=" phase_44_test ",
    )

    assert result["protocol_version"] == "kairos_prediction_protocol_v2"
    assert result["source_mode"] == "phase_44_test"
    assert result["allowed_for_future_offline_prediction_sandbox"] is True


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"protocol_version": "   "}, "protocol_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_prediction_protocol_gate_blocks_missing_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_prediction_protocol_gate(_baseline(), **kwargs)

    assert result["allowed_for_future_offline_prediction_sandbox"] is False
    assert expected_reason in result["blocking_reasons"]


def test_kairos_prediction_protocol_gate_blocks_wrong_provider() -> None:
    _assert_blocked(_baseline(provider="other-provider"), "wrong_provider")


def test_kairos_prediction_protocol_gate_blocks_wrong_baseline_mode() -> None:
    _assert_blocked(_baseline(mode="other_mode"), "wrong_baseline_mode")


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_reason"),
    [
        ("candidate_count", 0, "candidate_count_empty"),
        ("accepted_count", 0, "accepted_count_empty"),
    ],
)
def test_kairos_prediction_protocol_gate_blocks_empty_counts(
    field_name: str,
    field_value: object,
    expected_reason: str,
) -> None:
    result = _assert_blocked(
        _baseline(**{field_name: field_value}),
        expected_reason,
    )

    assert result["baseline_sample_accepted"] is False


def test_kairos_prediction_protocol_gate_blocks_empty_descriptive_sample() -> None:
    baseline = _baseline(
        descriptive_signals={
            "has_completed_sample": False,
            "has_live_sample": False,
            "has_scheduled_sample": False,
            "sample_is_empty": True,
        },
    )
    result = _assert_blocked(baseline, "sample_is_empty")

    assert result["baseline_sample_accepted"] is False


@pytest.mark.parametrize(
    "flag_name",
    [
        "prediction_created",
        "official_prediction_created",
        "betting_created",
        "ml_model_used",
        "confidence_score_created",
    ],
)
def test_kairos_prediction_protocol_gate_blocks_created_or_used_flags(
    flag_name: str,
) -> None:
    result = build_kairos_prediction_protocol_gate(_baseline(**{flag_name: True}))

    assert result["allowed_for_future_offline_prediction_sandbox"] is False
    assert result["descriptive_only_confirmed"] is False


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "probability",
        "win_probability",
        "final_pick",
        "suggested_bet",
        "bet_signal",
        "recommended_outcome",
        "model_output",
    ],
)
def test_kairos_prediction_protocol_gate_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    baseline = _baseline(extra={"nested": {forbidden_key: "blocked"}})
    result = _assert_blocked(baseline, "unsafe_decision_material_present")

    assert result["descriptive_only_confirmed"] is False


@pytest.mark.parametrize(
    ("forbidden_key", "expected_reason"),
    [
        ("odds", "unsafe_market_material_present"),
        ("bookmaker", "unsafe_market_material_present"),
        ("stake", "unsafe_market_material_present"),
        ("raw_payload", "unsafe_source_material_present"),
        ("api_key", "unsafe_credential_material_present"),
        ("auth", "unsafe_credential_material_present"),
        ("secret", "unsafe_credential_material_present"),
        ("token", "unsafe_credential_material_present"),
    ],
)
def test_kairos_prediction_protocol_gate_blocks_unsafe_material(
    forbidden_key: str,
    expected_reason: str,
) -> None:
    baseline = _baseline(extra={"nested": {forbidden_key: "blocked"}})

    _assert_blocked(baseline, expected_reason)


def test_kairos_prediction_protocol_gate_blocks_baseline_blocking_reasons() -> None:
    _assert_blocked(
        _baseline(blocking_reasons=["wrong_provider"]),
        "baseline_blocking_reasons_present",
    )


def test_kairos_prediction_protocol_gate_marks_required_inputs_missing() -> None:
    baseline = _baseline()
    baseline.pop("descriptive_signals")

    result = _assert_blocked(baseline, "required_inputs_missing")

    assert result["required_inputs_present"] is False


def test_kairos_prediction_protocol_gate_output_does_not_echo_forbidden_material() -> None:
    baseline = _baseline(
        extra={
            "raw_payload": {"blocked": True},
            "api_key": "blocked-api-key",
            "auth": "blocked-auth",
            "secret": "blocked-secret",
            "token": "blocked-token",
            "odds": {"home": 1.5},
            "bookmaker": "blocked-bookmaker",
            "stake": 100,
            "probability": 0.7,
            "recommended_outcome": "blocked-recommendation",
            "suggested_bet": "blocked-suggested-bet",
            "final_pick": "blocked-final-pick",
            "win_probability": 0.8,
            "bet_signal": "blocked-bet-signal",
        }
    )
    result = build_kairos_prediction_protocol_gate(baseline)
    serialized_result = json.dumps(result, sort_keys=True)
    output_keys = _all_keys(result)

    assert FORBIDDEN_EXACT_OUTPUT_KEYS.isdisjoint(output_keys)
    assert "blocked" not in serialized_result
    assert "raw_payload" not in serialized_result
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


def test_kairos_prediction_protocol_gate_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(gate_module)
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


def test_kairos_prediction_protocol_gate_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 44" in doc_text
    assert "protocol gate only" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no offline prediction created" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no ml" in doc_lower
    assert "no confidence scoring" in doc_lower
    assert "no betting/odds" in doc_lower
    assert "phase 45" in doc_lower
    assert "first offline prediction sandbox" in doc_lower
    assert "controlled" in doc_lower


def test_kairos_prediction_protocol_gate_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "63_KAIROS_PREDICTION_PROTOCOL_GATE.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
