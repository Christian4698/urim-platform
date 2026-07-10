from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import kairos_confidence_scoring_engine as scoring_module
from app.modules.providers.kairos_confidence_scoring_engine import (
    build_kairos_confidence_scoring_engine,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "66_CONFIDENCE_SCORING_ENGINE.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "active"
) / "047-phase-47-confidence-scoring-engine.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "completed"
) / "047-phase-47-confidence-scoring-engine.md"
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "scoring_version",
    "source_mode",
    "read_only",
    "db_writes",
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "probability_created",
    "confidence_score_created",
    "confidence_score_type",
    "confidence_score",
    "confidence_band",
    "not_probability",
    "not_for_betting",
    "not_a_guarantee",
    "sample_quality",
    "score_components",
    "blocking_reasons",
}
EXPECTED_SAMPLE_QUALITY_KEYS = {
    "sandbox_count",
    "fixture_count",
    "matched_fixture_count",
    "evaluable_count",
    "non_evaluable_count",
    "missing_result_count",
}
EXPECTED_SCORE_COMPONENT_KEYS = {
    "sample_presence",
    "match_coverage",
    "evaluable_coverage",
    "result_completeness",
    "descriptive_integrity",
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


def _backtest_report(**overrides: object) -> dict[str, object]:
    report: dict[str, object] = {
        "provider": "api-football",
        "mode": "kairos_backtesting_foundation_only",
        "backtest_version": "kairos_backtesting_foundation_v1",
        "source_mode": "offline_sandbox",
        "read_only": True,
        "db_writes": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "probability_created": False,
        "backtest_report_created": True,
        "sandbox_count": 1,
        "fixture_count": 4,
        "matched_fixture_count": 2,
        "unmatched_sandbox_count": 0,
        "evaluable_count": 2,
        "non_evaluable_count": 2,
        "completed_fixture_count": 3,
        "missing_result_count": 1,
        "outcome_distribution": {
            "home_win": 1,
            "draw": 1,
            "away_win": 0,
        },
        "evaluation_summary": {
            "has_evaluable_sample": True,
            "sample_is_empty": False,
            "descriptive_only": True,
        },
        "blocking_reasons": [],
    }
    report.update(overrides)
    return report


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
    backtest_report: dict[str, object],
    expected_reason: str,
) -> dict[str, object]:
    result = build_kairos_confidence_scoring_engine(backtest_report)

    assert result["confidence_score_created"] is False
    assert result["confidence_score"] == 0
    assert result["confidence_band"] == "blocked"
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_confidence_scoring_engine_module_and_function_exist() -> None:
    assert hasattr(scoring_module, "build_kairos_confidence_scoring_engine")
    assert callable(build_kairos_confidence_scoring_engine)


def test_kairos_confidence_scoring_engine_scores_valid_backtest() -> None:
    result = build_kairos_confidence_scoring_engine(_backtest_report())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_confidence_scoring_engine"
    assert result["scoring_version"] == "kairos_confidence_scoring_v1"
    assert result["source_mode"] == "backtesting_foundation"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["probability_created"] is False
    assert result["confidence_score_created"] is True
    assert result["confidence_score_type"] == "technical_signal_quality"
    assert 0 <= result["confidence_score"] <= 100
    assert result["confidence_score"] == 69
    assert result["confidence_band"] == "medium"
    assert result["confidence_band"] in {"blocked", "low", "medium", "high"}
    assert result["not_probability"] is True
    assert result["not_for_betting"] is True
    assert result["not_a_guarantee"] is True
    assert result["sample_quality"] == {
        "sandbox_count": 1,
        "fixture_count": 4,
        "matched_fixture_count": 2,
        "evaluable_count": 2,
        "non_evaluable_count": 2,
        "missing_result_count": 1,
    }
    assert set(result["sample_quality"]) == EXPECTED_SAMPLE_QUALITY_KEYS
    assert result["score_components"] == {
        "sample_presence": 25,
        "match_coverage": 12,
        "evaluable_coverage": 12,
        "result_completeness": 10,
        "descriptive_integrity": 10,
    }
    assert set(result["score_components"]) == EXPECTED_SCORE_COMPONENT_KEYS
    assert result["blocking_reasons"] == []


def test_kairos_confidence_scoring_engine_uses_custom_metadata() -> None:
    result = build_kairos_confidence_scoring_engine(
        _backtest_report(),
        scoring_version=" kairos_confidence_scoring_v2 ",
        source_mode=" phase_47_test ",
    )

    assert result["scoring_version"] == "kairos_confidence_scoring_v2"
    assert result["source_mode"] == "phase_47_test"
    assert result["confidence_score_created"] is True


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"scoring_version": "   "}, "scoring_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_confidence_scoring_engine_blocks_missing_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_confidence_scoring_engine(_backtest_report(), **kwargs)

    assert result["confidence_score_created"] is False
    assert result["confidence_score"] == 0
    assert result["confidence_band"] == "blocked"
    assert expected_reason in result["blocking_reasons"]


def test_kairos_confidence_scoring_engine_blocks_wrong_provider() -> None:
    _assert_blocked(_backtest_report(provider="other-provider"), "wrong_provider")


def test_kairos_confidence_scoring_engine_blocks_uncreated_backtest_report() -> None:
    _assert_blocked(
        _backtest_report(backtest_report_created=False),
        "backtest_report_not_created",
    )


def test_kairos_confidence_scoring_engine_blocks_empty_sample() -> None:
    report = _backtest_report(
        sandbox_count=0,
        fixture_count=0,
        matched_fixture_count=0,
        evaluable_count=0,
        non_evaluable_count=0,
        missing_result_count=0,
        evaluation_summary={
            "has_evaluable_sample": False,
            "sample_is_empty": True,
            "descriptive_only": True,
        },
    )
    result = _assert_blocked(report, "sample_is_empty")

    assert result["sample_quality"]["sandbox_count"] == 0
    assert result["sample_quality"]["fixture_count"] == 0


def test_kairos_confidence_scoring_engine_blocks_zero_evaluable_count() -> None:
    report = _backtest_report(
        evaluable_count=0,
        matched_fixture_count=0,
        evaluation_summary={
            "has_evaluable_sample": False,
            "sample_is_empty": False,
            "descriptive_only": True,
        },
    )

    _assert_blocked(report, "evaluable_count_empty")


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
def test_kairos_confidence_scoring_engine_blocks_unsafe_flags(
    flag_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(_backtest_report(**{flag_name: True}), expected_reason)


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
def test_kairos_confidence_scoring_engine_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    _assert_blocked(
        _backtest_report(extra={"nested": {forbidden_key: "blocked"}}),
        "unsafe_decision_material_present",
    )


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
        ("roi", "unsafe_financial_material_present"),
        ("profit", "unsafe_financial_material_present"),
        ("payout", "unsafe_financial_material_present"),
        ("bankroll", "unsafe_financial_material_present"),
    ],
)
def test_kairos_confidence_scoring_engine_blocks_unsafe_material(
    forbidden_key: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        _backtest_report(extra={"nested": {forbidden_key: "blocked"}}),
        expected_reason,
    )


def test_kairos_confidence_scoring_engine_blocks_non_descriptive_backtest() -> None:
    _assert_blocked(
        _backtest_report(
            evaluation_summary={
                "has_evaluable_sample": True,
                "sample_is_empty": False,
                "descriptive_only": False,
            },
        ),
        "backtest_not_descriptive",
    )


def test_kairos_confidence_scoring_engine_blocks_upstream_reasons() -> None:
    _assert_blocked(
        _backtest_report(blocking_reasons=["sandbox_wrong_provider"]),
        "backtest_blocking_reasons_present",
    )


def test_kairos_confidence_scoring_engine_output_does_not_echo_forbidden_material() -> None:
    result = build_kairos_confidence_scoring_engine(
        _backtest_report(
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
                "roi": 0.1,
                "profit": 12,
                "payout": 20,
                "bankroll": 100,
            }
        )
    )
    serialized_result = json.dumps(result, sort_keys=True)
    output_keys = _all_keys(result)

    assert FORBIDDEN_EXACT_OUTPUT_KEYS.isdisjoint(output_keys)
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
    assert "roi" not in serialized_result
    assert "profit" not in serialized_result
    assert "payout" not in serialized_result
    assert "bankroll" not in serialized_result


def test_kairos_confidence_scoring_engine_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_confidence_scoring_engine(_backtest_report())
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


def test_kairos_confidence_scoring_engine_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(scoring_module)
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


def test_kairos_confidence_scoring_engine_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 47" in doc_text
    assert "confidence scoring technique only" in doc_lower
    assert "not probability" in doc_lower
    assert "not for betting" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no prediction record" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no ml" in doc_lower
    assert "no probability" in doc_lower
    assert "no betting/odds/stake" in doc_lower
    assert "no roi/profit/bankroll" in doc_lower
    assert "phase 48" in doc_lower
    assert "dashboard mvp read-only" in doc_lower


def test_kairos_confidence_scoring_engine_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "66_CONFIDENCE_SCORING_ENGINE.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
