from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import kairos_backtesting_foundation as backtest_module
from app.modules.providers.kairos_backtesting_foundation import (
    build_kairos_backtesting_foundation,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "65_BACKTESTING_FOUNDATION.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "active"
) / "046-phase-46-backtesting-foundation.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "completed"
) / "046-phase-46-backtesting-foundation.md"
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "backtest_version",
    "source_mode",
    "read_only",
    "db_writes",
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "confidence_score_created",
    "probability_created",
    "backtest_report_created",
    "sandbox_count",
    "fixture_count",
    "matched_fixture_count",
    "unmatched_sandbox_count",
    "evaluable_count",
    "non_evaluable_count",
    "completed_fixture_count",
    "missing_result_count",
    "outcome_distribution",
    "evaluation_summary",
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
    "roi",
    "profit",
    "payout",
    "bankroll",
}


def _sandbox(**overrides: object) -> dict[str, object]:
    sandbox: dict[str, object] = {
        "provider": "api-football",
        "mode": "kairos_first_offline_prediction_sandbox",
        "sandbox_version": "kairos_offline_sandbox_v1",
        "source_mode": "protocol_gate",
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
        "candidate_count": 3,
        "accepted_count": 3,
        "completed_fixture_count": 2,
        "scheduled_fixture_count": 1,
        "sandbox_hypothesis": {
            "hypothesis_type": "descriptive_offline_sandbox",
            "basis": "baseline_analytics_only",
            "sample_state": "completed_and_scheduled_sample",
            "non_official": True,
            "not_for_betting": True,
        },
        "sandbox_notes": [
            "experimental_offline_only",
            "descriptive_baseline_only",
            "non_official",
            "not_for_betting",
        ],
        "blocking_reasons": [],
    }
    sandbox.update(overrides)
    return sandbox


def _fixture(**overrides: object) -> dict[str, object]:
    fixture: dict[str, object] = {
        "provider": "api-football",
        "provider_fixture_id": 101,
        "fixture_status_short": "FT",
        "goals_home": None,
        "goals_away": None,
        "score_fulltime_home": 2,
        "score_fulltime_away": 1,
        "payload_hash": "abc123",
        "source_mode": "phase_46_test",
    }
    fixture.update(overrides)
    return fixture


def _fixtures() -> list[dict[str, object]]:
    return [
        _fixture(provider_fixture_id=101, score_fulltime_home=2, score_fulltime_away=1),
        _fixture(
            provider_fixture_id=102,
            fixture_status_short="AET",
            goals_home=1,
            goals_away=1,
            score_fulltime_home=None,
            score_fulltime_away=None,
        ),
        _fixture(
            provider_fixture_id=103,
            fixture_status_short="NS",
            score_fulltime_home=None,
            score_fulltime_away=None,
        ),
        _fixture(
            provider_fixture_id=104,
            fixture_status_short="FT",
            goals_home=None,
            goals_away=None,
            score_fulltime_home=None,
            score_fulltime_away=None,
        ),
    ]


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
    sandboxes: list[dict[str, object]] | None = None,
    fixtures: list[dict[str, object]] | None = None,
    expected_reason: str,
) -> dict[str, object]:
    result = build_kairos_backtesting_foundation(
        [_sandbox()] if sandboxes is None else sandboxes,
        _fixtures() if fixtures is None else fixtures,
    )

    assert result["backtest_report_created"] is False
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_backtesting_foundation_module_and_function_exist() -> None:
    assert hasattr(backtest_module, "build_kairos_backtesting_foundation")
    assert callable(build_kairos_backtesting_foundation)


def test_kairos_backtesting_foundation_creates_descriptive_report() -> None:
    result = build_kairos_backtesting_foundation([_sandbox()], _fixtures())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_backtesting_foundation_only"
    assert result["backtest_version"] == "kairos_backtesting_foundation_v1"
    assert result["source_mode"] == "offline_sandbox"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["confidence_score_created"] is False
    assert result["probability_created"] is False
    assert result["backtest_report_created"] is True
    assert result["sandbox_count"] == 1
    assert result["fixture_count"] == 4
    assert result["matched_fixture_count"] == 2
    assert result["unmatched_sandbox_count"] == 0
    assert result["evaluable_count"] == 2
    assert result["non_evaluable_count"] == 2
    assert result["completed_fixture_count"] == 3
    assert result["missing_result_count"] == 1
    assert result["outcome_distribution"] == {
        "home_win": 1,
        "draw": 1,
        "away_win": 0,
    }
    assert result["evaluation_summary"] == {
        "has_evaluable_sample": True,
        "sample_is_empty": False,
        "descriptive_only": True,
    }
    assert result["blocking_reasons"] == []


def test_kairos_backtesting_foundation_uses_custom_metadata() -> None:
    result = build_kairos_backtesting_foundation(
        [_sandbox()],
        _fixtures(),
        backtest_version=" kairos_backtesting_foundation_v2 ",
        source_mode=" phase_46_test ",
    )

    assert result["backtest_version"] == "kairos_backtesting_foundation_v2"
    assert result["source_mode"] == "phase_46_test"
    assert result["backtest_report_created"] is True


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"backtest_version": "   "}, "backtest_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_backtesting_foundation_blocks_missing_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_backtesting_foundation([_sandbox()], _fixtures(), **kwargs)

    assert result["backtest_report_created"] is False
    assert expected_reason in result["blocking_reasons"]


def test_kairos_backtesting_foundation_blocks_empty_inputs() -> None:
    empty_sandbox_result = build_kairos_backtesting_foundation([], _fixtures())

    assert empty_sandbox_result["backtest_report_created"] is False
    assert empty_sandbox_result["evaluation_summary"]["sample_is_empty"] is True
    assert "sandbox_outputs_empty" in empty_sandbox_result["blocking_reasons"]

    empty_fixture_result = build_kairos_backtesting_foundation([_sandbox()], [])

    assert empty_fixture_result["backtest_report_created"] is False
    assert empty_fixture_result["evaluation_summary"]["sample_is_empty"] is True
    assert "completed_fixture_rows_empty" in empty_fixture_result["blocking_reasons"]


@pytest.mark.parametrize(
    ("sandboxes", "fixtures", "expected_reason"),
    [
        ([_sandbox(provider="other-provider")], _fixtures(), "sandbox_wrong_provider"),
        ([_sandbox()], [_fixture(provider="other-provider")], "fixture_wrong_provider"),
    ],
)
def test_kairos_backtesting_foundation_blocks_wrong_provider(
    sandboxes: list[dict[str, object]],
    fixtures: list[dict[str, object]],
    expected_reason: str,
) -> None:
    _assert_blocked(
        sandboxes=sandboxes,
        fixtures=fixtures,
        expected_reason=expected_reason,
    )


@pytest.mark.parametrize(
    "flag_name",
    [
        "official_prediction_created",
        "prediction_record_created",
        "betting_created",
        "ml_model_used",
        "confidence_score_created",
        "probability_created",
    ],
)
def test_kairos_backtesting_foundation_blocks_sandbox_flags(flag_name: str) -> None:
    _assert_blocked(
        sandboxes=[_sandbox(**{flag_name: True})],
        expected_reason=f"sandbox_{_expected_flag_reason(flag_name)}",
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
def test_kairos_backtesting_foundation_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    _assert_blocked(
        sandboxes=[_sandbox(extra={"nested": {forbidden_key: "blocked"}})],
        expected_reason="sandbox_unsafe_decision_material_present",
    )


@pytest.mark.parametrize(
    ("forbidden_key", "expected_reason"),
    [
        ("odds", "sandbox_unsafe_market_material_present"),
        ("bookmaker", "sandbox_unsafe_market_material_present"),
        ("stake", "sandbox_unsafe_market_material_present"),
        ("raw_payload", "fixture_unsafe_source_material_present"),
        ("api_key", "fixture_unsafe_credential_material_present"),
        ("auth", "fixture_unsafe_credential_material_present"),
        ("secret", "fixture_unsafe_credential_material_present"),
        ("token", "fixture_unsafe_credential_material_present"),
        ("roi", "sandbox_unsafe_financial_material_present"),
        ("profit", "sandbox_unsafe_financial_material_present"),
        ("payout", "sandbox_unsafe_financial_material_present"),
        ("bankroll", "sandbox_unsafe_financial_material_present"),
    ],
)
def test_kairos_backtesting_foundation_blocks_unsafe_material(
    forbidden_key: str,
    expected_reason: str,
) -> None:
    if forbidden_key in {"raw_payload", "api_key", "auth", "secret", "token"}:
        _assert_blocked(
            fixtures=[_fixture(extra={"nested": {forbidden_key: "blocked"}})],
            expected_reason=expected_reason,
        )
        return

    _assert_blocked(
        sandboxes=[_sandbox(extra={"nested": {forbidden_key: "blocked"}})],
        expected_reason=expected_reason,
    )


def test_kairos_backtesting_foundation_blocks_when_no_fixture_result_is_evaluable() -> None:
    result = _assert_blocked(
        fixtures=[
            _fixture(
                provider_fixture_id=101,
                score_fulltime_home=None,
                score_fulltime_away=None,
                goals_home=None,
                goals_away=None,
            )
        ],
        expected_reason="no_evaluable_completed_fixtures",
    )

    assert result["evaluable_count"] == 0
    assert result["missing_result_count"] == 1


def test_kairos_backtesting_foundation_output_does_not_echo_forbidden_material() -> None:
    result = build_kairos_backtesting_foundation(
        [_sandbox(extra={"nested": {"profit": "blocked"}})],
        [_fixture(extra={"nested": {"raw_payload": {"blocked": True}}})],
    )
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
    assert "roi" not in serialized_result
    assert "profit" not in serialized_result
    assert "payout" not in serialized_result
    assert "bankroll" not in serialized_result


def test_kairos_backtesting_foundation_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_backtesting_foundation([_sandbox()], _fixtures())
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


def test_kairos_backtesting_foundation_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(backtest_module)
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


def test_kairos_backtesting_foundation_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 46" in doc_text
    assert "backtesting foundation only" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no prediction record" in doc_lower
    assert "no real api call" in doc_lower
    assert "no db write" in doc_lower
    assert "no ingestion runtime" in doc_lower
    assert "no ml" in doc_lower
    assert "no confidence scoring" in doc_lower
    assert "no probability" in doc_lower
    assert "no betting/odds/stake" in doc_lower
    assert "no roi/profit/bankroll" in doc_lower
    assert "phase 47" in doc_lower
    assert "confidence scoring engine" in doc_lower
    assert "separate from betting" in doc_lower


def test_kairos_backtesting_foundation_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "65_BACKTESTING_FOUNDATION.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()


def _expected_flag_reason(flag_name: str) -> str:
    if flag_name == "official_prediction_created":
        return "created_official_prediction_flag"
    if flag_name == "prediction_record_created":
        return "created_prediction_record_flag"
    if flag_name == "betting_created":
        return "created_betting_flag"
    if flag_name == "ml_model_used":
        return "used_ml_model"
    if flag_name == "confidence_score_created":
        return "created_confidence_flag"
    if flag_name == "probability_created":
        return "created_probability_flag"
    raise AssertionError(f"Unexpected flag: {flag_name}")
