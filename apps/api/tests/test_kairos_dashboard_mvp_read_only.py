from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import kairos_dashboard_mvp_read_only as dashboard_module
from app.modules.providers.kairos_dashboard_mvp_read_only import (
    build_kairos_dashboard_mvp_read_only,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "67_DASHBOARD_MVP_READ_ONLY.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "active"
) / "048-phase-48-dashboard-mvp-read-only.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "completed"
) / "048-phase-48-dashboard-mvp-read-only.md"
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "dashboard_version",
    "source_mode",
    "read_only",
    "db_writes",
    "api_football_call_created",
    "ingestion_created",
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "probability_created",
    "dashboard_ready",
    "cards",
    "summary",
    "blocking_reasons",
}
EXPECTED_CARD_KEYS = {
    "data_freshness",
    "feature_snapshots",
    "baseline_analytics",
    "protocol_gate",
    "offline_sandbox",
    "backtesting",
    "confidence_scoring",
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
    "probability",
    "recommended_outcome",
    "suggested_bet",
    "final_pick",
    "win_probability",
    "bet_signal",
    "roi",
    "profit",
    "payout",
    "bankroll",
}


def _dashboard_inputs() -> dict[str, dict[str, object]]:
    return {
        "data_freshness_audit": {
            "provider": "api-football",
            "mode": "fixture_data_freshness_provider_audit_trail",
            "read_only": True,
            "db_writes": False,
            "prediction_created": False,
            "betting_created": False,
            "ready_for_internal_read": True,
            "row_count": 12,
            "fresh_count": 10,
            "stale_count": 2,
            "blocking_reasons": [],
        },
        "feature_snapshot_contract": {
            "provider": "api-football",
            "mode": "fixture_feature_snapshot_contract_without_ml",
            "read_only": True,
            "db_writes": False,
            "prediction_created": False,
            "betting_created": False,
            "ml_model_used": False,
            "confidence_score_created": False,
            "candidate_count": 12,
            "accepted_count": 10,
            "rejected_count": 2,
            "blocking_reasons": [],
        },
        "baseline_analytics": {
            "provider": "api-football",
            "mode": "fixture_baseline_analytics_without_official_prediction",
            "read_only": True,
            "db_writes": False,
            "prediction_created": False,
            "official_prediction_created": False,
            "betting_created": False,
            "ml_model_used": False,
            "confidence_score_created": False,
            "candidate_count": 12,
            "accepted_count": 10,
            "completed_fixture_count": 8,
            "scheduled_fixture_count": 2,
            "blocking_reasons": [],
        },
        "protocol_gate": {
            "provider": "api-football",
            "mode": "kairos_prediction_protocol_gate_only",
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
            "blocking_reasons": [],
        },
        "offline_sandbox": {
            "provider": "api-football",
            "mode": "kairos_first_offline_prediction_sandbox",
            "read_only": True,
            "db_writes": False,
            "official_prediction_created": False,
            "prediction_record_created": False,
            "betting_created": False,
            "ml_model_used": False,
            "confidence_score_created": False,
            "probability_created": False,
            "sandbox_hypothesis_created": True,
            "allowed_by_protocol_gate": True,
            "candidate_count": 4,
            "accepted_count": 4,
            "blocking_reasons": [],
        },
        "backtesting_report": {
            "provider": "api-football",
            "mode": "kairos_backtesting_foundation_only",
            "read_only": True,
            "db_writes": False,
            "official_prediction_created": False,
            "prediction_record_created": False,
            "betting_created": False,
            "ml_model_used": False,
            "confidence_score_created": False,
            "probability_created": False,
            "backtest_report_created": True,
            "matched_fixture_count": 3,
            "evaluable_count": 3,
            "missing_result_count": 0,
            "blocking_reasons": [],
        },
        "confidence_scoring": {
            "provider": "api-football",
            "mode": "kairos_confidence_scoring_engine",
            "read_only": True,
            "db_writes": False,
            "official_prediction_created": False,
            "prediction_record_created": False,
            "betting_created": False,
            "ml_model_used": False,
            "probability_created": False,
            "confidence_score_created": True,
            "confidence_score_type": "technical_signal_quality",
            "confidence_score": 69,
            "confidence_band": "medium",
            "not_probability": True,
            "not_for_betting": True,
            "not_a_guarantee": True,
            "blocking_reasons": [],
        },
    }


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
    inputs: dict[str, dict[str, object]],
    expected_reason: str,
) -> dict[str, object]:
    result = build_kairos_dashboard_mvp_read_only(**inputs)

    assert result["dashboard_ready"] is False
    assert result["summary"]["overall_status"] == "blocked"
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_dashboard_mvp_module_and_function_exist() -> None:
    assert hasattr(dashboard_module, "build_kairos_dashboard_mvp_read_only")
    assert callable(build_kairos_dashboard_mvp_read_only)


def test_kairos_dashboard_mvp_builds_complete_safe_payload() -> None:
    result = build_kairos_dashboard_mvp_read_only(**_dashboard_inputs())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_dashboard_mvp_read_only"
    assert result["dashboard_version"] == "kairos_dashboard_mvp_v1"
    assert result["source_mode"] == "read_only_aggregate"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["api_football_call_created"] is False
    assert result["ingestion_created"] is False
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["probability_created"] is False
    assert result["dashboard_ready"] is True
    assert set(result["cards"]) == EXPECTED_CARD_KEYS
    assert result["cards"]["data_freshness"]["status"] == "ready"
    assert result["cards"]["feature_snapshots"]["status"] == "ready"
    assert result["cards"]["baseline_analytics"]["status"] == "ready"
    assert result["cards"]["protocol_gate"]["status"] == "ready"
    assert result["cards"]["offline_sandbox"]["status"] == "ready"
    assert result["cards"]["backtesting"]["status"] == "ready"
    assert result["cards"]["confidence_scoring"]["status"] == "ready"
    assert result["cards"]["confidence_scoring"]["confidence_score"] == 69
    assert result["summary"] == {
        "overall_status": "ready",
        "confidence_band": "medium",
        "confidence_score_type": "technical_signal_quality",
        "not_probability": True,
        "not_for_betting": True,
        "not_a_guarantee": True,
    }
    assert result["summary"]["confidence_band"] in {
        "blocked",
        "low",
        "medium",
        "high",
        "unknown",
    }
    assert result["blocking_reasons"] == []


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"dashboard_version": "   "}, "dashboard_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_dashboard_mvp_blocks_missing_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_dashboard_mvp_read_only(
        **_dashboard_inputs(),
        **kwargs,
    )

    assert result["dashboard_ready"] is False
    assert result["summary"]["overall_status"] == "blocked"
    assert expected_reason in result["blocking_reasons"]


def test_kairos_dashboard_mvp_missing_input_returns_partial() -> None:
    inputs = _dashboard_inputs()
    inputs.pop("confidence_scoring")

    result = build_kairos_dashboard_mvp_read_only(**inputs)

    assert result["dashboard_ready"] is False
    assert result["summary"]["overall_status"] == "partial"
    assert result["cards"]["confidence_scoring"] == {
        "present": False,
        "status": "missing",
    }
    assert "missing_confidence_scoring" in result["blocking_reasons"]


def test_kairos_dashboard_mvp_blocks_wrong_provider() -> None:
    inputs = _dashboard_inputs()
    inputs["baseline_analytics"]["provider"] = "other-provider"

    _assert_blocked(inputs, "baseline_analytics_wrong_provider")


@pytest.mark.parametrize(
    ("flag_name", "expected_reason"),
    [
        ("official_prediction_created", "created_official_prediction_flag"),
        ("prediction_record_created", "created_prediction_record_flag"),
        ("betting_created", "created_betting_flag"),
        ("ml_model_used", "used_ml_model"),
        ("probability_created", "created_probability_flag"),
    ],
)
def test_kairos_dashboard_mvp_blocks_unsafe_created_flags(
    flag_name: str,
    expected_reason: str,
) -> None:
    inputs = _dashboard_inputs()
    inputs["confidence_scoring"][flag_name] = True

    _assert_blocked(inputs, f"confidence_scoring_{expected_reason}")


@pytest.mark.parametrize(
    "forbidden_key",
    ["odds", "bookmaker", "stake"],
)
def test_kairos_dashboard_mvp_blocks_market_material(
    forbidden_key: str,
) -> None:
    inputs = _dashboard_inputs()
    inputs["baseline_analytics"]["extra"] = {
        "nested": {forbidden_key: "blocked"}
    }

    result = _assert_blocked(
        inputs,
        "baseline_analytics_unsafe_market_material_present",
    )

    assert forbidden_key not in json.dumps(result, sort_keys=True)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "probability",
        "win_probability",
        "final_pick",
        "suggested_bet",
        "bet_signal",
    ],
)
def test_kairos_dashboard_mvp_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    inputs = _dashboard_inputs()
    inputs["offline_sandbox"]["extra"] = {"nested": {forbidden_key: "blocked"}}

    result = _assert_blocked(
        inputs,
        "offline_sandbox_unsafe_decision_material_present",
    )
    output_keys = _all_keys(result)

    assert forbidden_key not in output_keys


@pytest.mark.parametrize(
    "forbidden_key",
    ["roi", "profit", "payout", "bankroll"],
)
def test_kairos_dashboard_mvp_blocks_financial_material(
    forbidden_key: str,
) -> None:
    inputs = _dashboard_inputs()
    inputs["backtesting_report"]["extra"] = {
        "nested": {forbidden_key: "blocked"}
    }

    result = _assert_blocked(
        inputs,
        "backtesting_unsafe_financial_material_present",
    )

    assert forbidden_key not in json.dumps(result, sort_keys=True)


def test_kairos_dashboard_mvp_blocks_upstream_reasons() -> None:
    inputs = _dashboard_inputs()
    inputs["protocol_gate"]["blocking_reasons"] = ["baseline_sample_missing"]

    _assert_blocked(inputs, "protocol_gate_blocking_reasons_present")


def test_kairos_dashboard_mvp_output_does_not_echo_forbidden_material() -> None:
    inputs = _dashboard_inputs()
    inputs["data_freshness_audit"]["extra"] = {
        "raw_payload": {"blocked": True},
        "api_key": "blocked-api-key",
        "auth": "blocked-auth",
        "secret": "blocked-secret",
        "token": "blocked-token",
    }
    inputs["offline_sandbox"]["extra"] = {
        "odds": {"home": 1.5},
        "bookmaker": "blocked-bookmaker",
        "stake": 100,
        "probability": 0.7,
        "recommended_outcome": "blocked-recommendation",
        "suggested_bet": "blocked-suggested-bet",
        "final_pick": "blocked-final-pick",
        "win_probability": 0.8,
        "bet_signal": "blocked-bet-signal",
        "roi": 0.1,
        "profit": 12,
        "payout": 20,
        "bankroll": 100,
    }

    result = build_kairos_dashboard_mvp_read_only(**inputs)
    serialized_result = json.dumps(result, sort_keys=True)
    output_keys = _all_keys(result)

    assert FORBIDDEN_EXACT_OUTPUT_KEYS.isdisjoint(output_keys)
    assert "blocked-api-key" not in serialized_result
    assert "blocked-auth" not in serialized_result
    assert "blocked-secret" not in serialized_result
    assert "blocked-token" not in serialized_result
    assert "raw_payload" not in serialized_result
    assert "api_key" not in serialized_result
    assert "auth" not in serialized_result
    assert "secret" not in serialized_result
    assert "token" not in serialized_result
    assert "odds" not in serialized_result
    assert "bookmaker" not in serialized_result
    assert "stake" not in serialized_result
    assert "prediction record" not in serialized_result
    assert "recommended_outcome" not in serialized_result
    assert "suggested_bet" not in serialized_result
    assert "final_pick" not in serialized_result
    assert "win_probability" not in serialized_result
    assert "bet_signal" not in serialized_result
    assert "roi" not in serialized_result
    assert "profit" not in serialized_result
    assert "payout" not in serialized_result
    assert "bankroll" not in serialized_result


def test_kairos_dashboard_mvp_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_dashboard_mvp_read_only(**_dashboard_inputs())
    serialized_result = json.dumps(result, sort_keys=True).lower()

    forbidden_runtime_phrases = (
        "safe bet",
        "sure bet",
        "guaranteed",
        "stake",
        "odds pick",
    )
    for phrase in forbidden_runtime_phrases:
        assert phrase not in serialized_result


def test_kairos_dashboard_mvp_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(dashboard_module)
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


def test_kairos_dashboard_mvp_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 48" in doc_text
    assert "dashboard read-only only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no prediction record" in doc_lower
    assert "no ml" in doc_lower
    assert "confidence score is technical only" in doc_lower
    assert "no probability" in doc_lower
    assert "no betting/odds/stake" in doc_lower
    assert "no roi/profit/bankroll" in doc_lower
    assert "phase 49" in doc_lower
    assert "monitoring, quotas and safe logs" in doc_lower


def test_kairos_dashboard_mvp_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "67_DASHBOARD_MVP_READ_ONLY.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
