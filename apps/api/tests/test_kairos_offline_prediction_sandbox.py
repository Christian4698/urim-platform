from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import kairos_offline_prediction_sandbox as sandbox_module
from app.modules.providers.kairos_offline_prediction_sandbox import (
    build_kairos_offline_prediction_sandbox,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "64_FIRST_OFFLINE_PREDICTION_SANDBOX.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "active"
    / "045-phase-45-first-offline-prediction-sandbox.md"
)
COMPLETED_PLAN_PATH = (
    REPO_ROOT
    / "docs"
    / "exec-plans"
    / "completed"
    / "045-phase-45-first-offline-prediction-sandbox.md"
)
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "sandbox_version",
    "source_mode",
    "read_only",
    "db_writes",
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "confidence_score_created",
    "probability_created",
    "sandbox_hypothesis_created",
    "allowed_by_protocol_gate",
    "candidate_count",
    "accepted_count",
    "completed_fixture_count",
    "scheduled_fixture_count",
    "sandbox_hypothesis",
    "sandbox_notes",
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
    "prediction_record",
    "confidence_score",
    "probability",
    "recommended_outcome",
    "suggested_bet",
    "final_pick",
    "win_probability",
    "bet_signal",
}


def _protocol_gate(**overrides: object) -> dict[str, object]:
    protocol_gate: dict[str, object] = {
        "provider": "api-football",
        "mode": "kairos_prediction_protocol_gate_only",
        "protocol_version": "kairos_prediction_protocol_v1",
        "source_mode": "baseline_analytics",
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "official_prediction_created": False,
        "offline_prediction_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "allowed_for_future_offline_prediction_sandbox": True,
        "required_inputs_present": True,
        "baseline_sample_accepted": True,
        "descriptive_only_confirmed": True,
        "candidate_count": 3,
        "accepted_count": 3,
        "rejected_count": 0,
        "completed_fixture_count": 2,
        "scheduled_fixture_count": 1,
        "has_completed_sample": True,
        "has_scheduled_sample": True,
        "blocking_reasons": [],
    }
    protocol_gate.update(overrides)
    return protocol_gate


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
    *,
    protocol_gate: dict[str, object] | None = None,
    baseline: dict[str, object] | None = None,
    expected_reason: str,
) -> dict[str, object]:
    result = build_kairos_offline_prediction_sandbox(
        _protocol_gate() if protocol_gate is None else protocol_gate,
        _baseline() if baseline is None else baseline,
    )

    assert result["sandbox_hypothesis_created"] is False
    assert result["sandbox_hypothesis"] is None
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_offline_prediction_sandbox_module_and_function_exist() -> None:
    assert hasattr(sandbox_module, "build_kairos_offline_prediction_sandbox")
    assert callable(build_kairos_offline_prediction_sandbox)


def test_kairos_offline_prediction_sandbox_creates_descriptive_hypothesis() -> None:
    result = build_kairos_offline_prediction_sandbox(_protocol_gate(), _baseline())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_first_offline_prediction_sandbox"
    assert result["sandbox_version"] == "kairos_offline_sandbox_v1"
    assert result["source_mode"] == "protocol_gate"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["confidence_score_created"] is False
    assert result["probability_created"] is False
    assert result["sandbox_hypothesis_created"] is True
    assert result["allowed_by_protocol_gate"] is True
    assert result["candidate_count"] == 3
    assert result["accepted_count"] == 3
    assert result["completed_fixture_count"] == 2
    assert result["scheduled_fixture_count"] == 1
    assert result["sandbox_hypothesis"] == {
        "hypothesis_type": "descriptive_offline_sandbox",
        "basis": "baseline_analytics_only",
        "sample_state": "completed_and_scheduled_sample",
        "non_official": True,
        "not_for_betting": True,
    }
    assert result["sandbox_notes"] == [
        "experimental_offline_only",
        "descriptive_baseline_only",
        "non_official",
        "not_for_betting",
    ]
    assert result["blocking_reasons"] == []


def test_kairos_offline_prediction_sandbox_uses_custom_metadata() -> None:
    result = build_kairos_offline_prediction_sandbox(
        _protocol_gate(),
        _baseline(),
        sandbox_version=" kairos_offline_sandbox_v2 ",
        source_mode=" phase_45_test ",
    )

    assert result["sandbox_version"] == "kairos_offline_sandbox_v2"
    assert result["source_mode"] == "phase_45_test"
    assert result["sandbox_hypothesis_created"] is True


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"sandbox_version": "   "}, "sandbox_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_offline_prediction_sandbox_blocks_missing_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_offline_prediction_sandbox(
        _protocol_gate(),
        _baseline(),
        **kwargs,
    )

    assert result["sandbox_hypothesis_created"] is False
    assert expected_reason in result["blocking_reasons"]


def test_kairos_offline_prediction_sandbox_blocks_gate_not_allowed() -> None:
    result = _assert_blocked(
        protocol_gate=_protocol_gate(
            allowed_for_future_offline_prediction_sandbox=False
        ),
        expected_reason="protocol_gate_not_allowed",
    )

    assert result["allowed_by_protocol_gate"] is False


@pytest.mark.parametrize(
    ("gate_provider", "baseline_provider", "expected_reason"),
    [
        ("other-provider", "api-football", "protocol_gate_wrong_provider"),
        ("api-football", "other-provider", "baseline_wrong_provider"),
    ],
)
def test_kairos_offline_prediction_sandbox_blocks_wrong_provider(
    gate_provider: str,
    baseline_provider: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        protocol_gate=_protocol_gate(provider=gate_provider),
        baseline=_baseline(provider=baseline_provider),
        expected_reason=expected_reason,
    )


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_reason"),
    [
        ("candidate_count", 0, "candidate_count_empty"),
        ("accepted_count", 0, "accepted_count_empty"),
    ],
)
def test_kairos_offline_prediction_sandbox_blocks_empty_baseline_counts(
    field_name: str,
    field_value: object,
    expected_reason: str,
) -> None:
    result = _assert_blocked(
        baseline=_baseline(**{field_name: field_value}),
        expected_reason=expected_reason,
    )

    assert result[field_name] == 0


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
def test_kairos_offline_prediction_sandbox_blocks_baseline_flags(
    flag_name: str,
) -> None:
    _assert_blocked(
        baseline=_baseline(**{flag_name: True}),
        expected_reason=f"baseline_{_expected_flag_reason(flag_name)}",
    )


@pytest.mark.parametrize(
    "flag_name",
    [
        "prediction_created",
        "official_prediction_created",
        "offline_prediction_created",
        "betting_created",
        "ml_model_used",
        "confidence_score_created",
    ],
)
def test_kairos_offline_prediction_sandbox_blocks_protocol_gate_flags(
    flag_name: str,
) -> None:
    _assert_blocked(
        protocol_gate=_protocol_gate(**{flag_name: True}),
        expected_reason=f"protocol_gate_{_expected_flag_reason(flag_name)}",
    )


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
        "confidence_score",
    ],
)
def test_kairos_offline_prediction_sandbox_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    baseline = _baseline(extra={"nested": {forbidden_key: "blocked"}})

    _assert_blocked(
        baseline=baseline,
        expected_reason="baseline_unsafe_decision_material_present",
    )


@pytest.mark.parametrize(
    ("forbidden_key", "expected_reason"),
    [
        ("odds", "baseline_unsafe_market_material_present"),
        ("bookmaker", "baseline_unsafe_market_material_present"),
        ("stake", "baseline_unsafe_market_material_present"),
        ("raw_payload", "baseline_unsafe_source_material_present"),
        ("api_key", "baseline_unsafe_credential_material_present"),
        ("auth", "baseline_unsafe_credential_material_present"),
        ("secret", "baseline_unsafe_credential_material_present"),
        ("token", "baseline_unsafe_credential_material_present"),
    ],
)
def test_kairos_offline_prediction_sandbox_blocks_unsafe_material(
    forbidden_key: str,
    expected_reason: str,
) -> None:
    baseline = _baseline(extra={"nested": {forbidden_key: "blocked"}})

    _assert_blocked(baseline=baseline, expected_reason=expected_reason)


def test_kairos_offline_prediction_sandbox_blocks_upstream_reasons() -> None:
    _assert_blocked(
        protocol_gate=_protocol_gate(blocking_reasons=["sample_is_empty"]),
        expected_reason="protocol_gate_blocking_reasons_present",
    )
    _assert_blocked(
        baseline=_baseline(blocking_reasons=["wrong_provider"]),
        expected_reason="baseline_blocking_reasons_present",
    )


def test_kairos_offline_prediction_sandbox_output_does_not_echo_forbidden_material() -> None:
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
    result = build_kairos_offline_prediction_sandbox(_protocol_gate(), baseline)
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
    assert "recommended_outcome" not in serialized_result
    assert "suggested_bet" not in serialized_result
    assert "final_pick" not in serialized_result
    assert "win_probability" not in serialized_result
    assert "bet_signal" not in serialized_result


def test_kairos_offline_prediction_sandbox_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_offline_prediction_sandbox(_protocol_gate(), _baseline())
    serialized_result = json.dumps(result, sort_keys=True).lower()

    forbidden_runtime_phrases = (
        "safe bet",
        "sure",
        "guaranteed",
        "stake",
        "odds pick",
    )
    for phrase in forbidden_runtime_phrases:
        assert phrase not in serialized_result


def test_kairos_offline_prediction_sandbox_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(sandbox_module)
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


def test_kairos_offline_prediction_sandbox_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 45" in doc_text
    assert "offline sandbox only" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no prediction record" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no ml" in doc_lower
    assert "no confidence scoring" in doc_lower
    assert "no probability" in doc_lower
    assert "no betting/odds/stake" in doc_lower
    assert "phase 46" in doc_lower
    assert "backtesting foundation" in doc_lower


def test_kairos_offline_prediction_sandbox_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "64_FIRST_OFFLINE_PREDICTION_SANDBOX.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()


def _expected_flag_reason(flag_name: str) -> str:
    if flag_name == "prediction_created":
        return "created_prediction_flag"
    if flag_name == "official_prediction_created":
        return "created_official_prediction_flag"
    if flag_name == "offline_prediction_created":
        return "created_offline_prediction_flag"
    if flag_name == "betting_created":
        return "created_betting_flag"
    if flag_name == "ml_model_used":
        return "used_ml_model"
    if flag_name == "confidence_score_created":
        return "created_confidence_flag"
    raise AssertionError(f"Unexpected flag: {flag_name}")
