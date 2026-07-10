from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_CONFIDENCE_SCORING_MODE: Final = "kairos_confidence_scoring_engine"
KAIROS_BACKTESTING_FOUNDATION_MODE: Final = "kairos_backtesting_foundation_only"
DEFAULT_SCORING_VERSION: Final = "kairos_confidence_scoring_v1"
DEFAULT_SCORING_SOURCE_MODE: Final = "backtesting_foundation"
CONFIDENCE_SCORE_TYPE: Final = "technical_signal_quality"

_UNSAFE_SOURCE_KEYS: Final = frozenset({"raw_payload"})
_UNSAFE_CREDENTIAL_KEYS: Final = frozenset(
    {"api_key", "auth", "secret", "token"}
)
_UNSAFE_MARKET_KEYS: Final = frozenset({"odds", "bookmaker", "stake"})
_UNSAFE_DECISION_KEYS: Final = frozenset(
    {
        "prediction",
        "predictions",
        "official_prediction",
        "prediction_record",
        "model_output",
        "probability",
        "win_probability",
        "recommended_outcome",
        "suggested_bet",
        "final_pick",
        "bet_signal",
    }
)
_UNSAFE_FINANCIAL_KEYS: Final = frozenset(
    {"roi", "profit", "payout", "bankroll"}
)


def build_kairos_confidence_scoring_engine(
    backtest_report: Mapping[str, Any],
    *,
    scoring_version: str = DEFAULT_SCORING_VERSION,
    source_mode: str = DEFAULT_SCORING_SOURCE_MODE,
) -> dict[str, Any]:
    scoring_version_value = _safe_text(scoring_version)
    source_mode_value = _safe_text(source_mode)
    sample_quality = _sample_quality(backtest_report)
    evaluation_summary = backtest_report.get("evaluation_summary")
    score_components = _score_components(
        sample_quality=sample_quality,
        evaluation_summary=evaluation_summary,
    )
    present_keys = _nested_keys(backtest_report)
    blocking_reasons = _blocking_reasons(
        scoring_version_present=bool(scoring_version_value),
        source_mode_present=bool(source_mode_value),
        backtest_report=backtest_report,
        evaluation_summary=evaluation_summary,
        sample_quality=sample_quality,
        present_keys=present_keys,
    )
    raw_score = sum(score_components.values())
    confidence_score = 0 if blocking_reasons else _clamp_score(raw_score)
    confidence_score_created = not blocking_reasons

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_CONFIDENCE_SCORING_MODE,
        "scoring_version": scoring_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "probability_created": False,
        "confidence_score_created": confidence_score_created,
        "confidence_score_type": CONFIDENCE_SCORE_TYPE,
        "confidence_score": confidence_score,
        "confidence_band": _confidence_band(
            score=confidence_score,
            has_blocking_reasons=bool(blocking_reasons),
        ),
        "not_probability": True,
        "not_for_betting": True,
        "not_a_guarantee": True,
        "sample_quality": sample_quality,
        "score_components": score_components,
        "blocking_reasons": blocking_reasons,
    }


def _sample_quality(backtest_report: Mapping[str, Any]) -> dict[str, int]:
    return {
        "sandbox_count": _non_negative_int_like(
            backtest_report.get("sandbox_count")
        )
        or 0,
        "fixture_count": _non_negative_int_like(backtest_report.get("fixture_count"))
        or 0,
        "matched_fixture_count": _non_negative_int_like(
            backtest_report.get("matched_fixture_count")
        )
        or 0,
        "evaluable_count": _non_negative_int_like(
            backtest_report.get("evaluable_count")
        )
        or 0,
        "non_evaluable_count": _non_negative_int_like(
            backtest_report.get("non_evaluable_count")
        )
        or 0,
        "missing_result_count": _non_negative_int_like(
            backtest_report.get("missing_result_count")
        )
        or 0,
    }


def _score_components(
    *,
    sample_quality: Mapping[str, int],
    evaluation_summary: Any,
) -> dict[str, int]:
    sandbox_count = sample_quality["sandbox_count"]
    fixture_count = sample_quality["fixture_count"]
    matched_fixture_count = sample_quality["matched_fixture_count"]
    evaluable_count = sample_quality["evaluable_count"]
    non_evaluable_count = sample_quality["non_evaluable_count"]
    missing_result_count = sample_quality["missing_result_count"]
    completed_or_missing_count = evaluable_count + missing_result_count

    return {
        "sample_presence": 25
        if sandbox_count > 0 and fixture_count > 0 and evaluable_count > 0
        else 0,
        "match_coverage": _ratio_component(
            numerator=matched_fixture_count,
            denominator=fixture_count,
            max_points=25,
        ),
        "evaluable_coverage": _ratio_component(
            numerator=evaluable_count,
            denominator=evaluable_count + non_evaluable_count,
            max_points=25,
        ),
        "result_completeness": _ratio_component(
            numerator=evaluable_count,
            denominator=completed_or_missing_count,
            max_points=15,
        ),
        "descriptive_integrity": 10
        if _summary_flag(evaluation_summary, "descriptive_only") is True
        else 0,
    }


def _blocking_reasons(
    *,
    scoring_version_present: bool,
    source_mode_present: bool,
    backtest_report: Mapping[str, Any],
    evaluation_summary: Any,
    sample_quality: Mapping[str, int],
    present_keys: set[str],
) -> list[str]:
    reasons: list[str] = []
    if not scoring_version_present:
        reasons.append("scoring_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    if backtest_report.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("wrong_provider")
    if backtest_report.get("mode") != KAIROS_BACKTESTING_FOUNDATION_MODE:
        reasons.append("wrong_backtest_mode")
    if backtest_report.get("backtest_report_created") is not True:
        reasons.append("backtest_report_not_created")
    if _summary_flag(evaluation_summary, "descriptive_only") is not True:
        reasons.append("backtest_not_descriptive")
    if _summary_flag(evaluation_summary, "sample_is_empty") is True:
        reasons.append("sample_is_empty")
    if _summary_flag(evaluation_summary, "has_evaluable_sample") is not True:
        reasons.append("evaluable_sample_missing")
    if sample_quality["sandbox_count"] == 0 or sample_quality["fixture_count"] == 0:
        reasons.append("sample_is_empty")
    if sample_quality["evaluable_count"] == 0:
        reasons.append("evaluable_count_empty")
    _append_flag_reasons(reasons, backtest_report)
    _append_unsafe_key_reasons(reasons, present_keys)
    if _has_blocking_reasons(backtest_report.get("blocking_reasons")):
        reasons.append("backtest_blocking_reasons_present")
    return _dedupe_reasons(reasons)


def _append_flag_reasons(
    reasons: list[str],
    backtest_report: Mapping[str, Any],
) -> None:
    if _is_true(backtest_report.get("official_prediction_created")):
        reasons.append("created_official_prediction_flag")
    if _is_true(backtest_report.get("prediction_record_created")):
        reasons.append("created_prediction_record_flag")
    if _is_true(backtest_report.get("betting_created")):
        reasons.append("created_betting_flag")
    if _is_true(backtest_report.get("ml_model_used")):
        reasons.append("used_ml_model")
    if _is_true(backtest_report.get("probability_created")):
        reasons.append("created_probability_flag")


def _append_unsafe_key_reasons(
    reasons: list[str],
    present_keys: set[str],
) -> None:
    if _UNSAFE_SOURCE_KEYS & present_keys:
        reasons.append("unsafe_source_material_present")
    if _UNSAFE_CREDENTIAL_KEYS & present_keys:
        reasons.append("unsafe_credential_material_present")
    if _UNSAFE_MARKET_KEYS & present_keys:
        reasons.append("unsafe_market_material_present")
    if _UNSAFE_DECISION_KEYS & present_keys:
        reasons.append("unsafe_decision_material_present")
    if _UNSAFE_FINANCIAL_KEYS & present_keys:
        reasons.append("unsafe_financial_material_present")


def _ratio_component(*, numerator: int, denominator: int, max_points: int) -> int:
    if denominator <= 0 or numerator <= 0:
        return 0
    bounded_numerator = min(numerator, denominator)
    return int((bounded_numerator * max_points) / denominator)


def _confidence_band(*, score: int, has_blocking_reasons: bool) -> str:
    if has_blocking_reasons or score == 0:
        return "blocked"
    if score <= 39:
        return "low"
    if score <= 69:
        return "medium"
    return "high"


def _summary_flag(value: Any, field_name: str) -> bool | None:
    if isinstance(value, Mapping):
        flag_value = value.get(field_name)
        if isinstance(flag_value, bool):
            return flag_value
    return None


def _nested_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        keys = {str(key) for key in value}
        for nested_value in value.values():
            for nested_key in _nested_keys(nested_value):
                keys.add(nested_key)
        return keys
    if isinstance(value, list | tuple):
        keys: set[str] = set()
        for item in value:
            for nested_key in _nested_keys(item):
                keys.add(nested_key)
        return keys
    return set()


def _has_blocking_reasons(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, list | tuple | set):
        return bool(value)
    return True


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _is_true(value: Any) -> bool:
    return value is True


def _non_negative_int_like(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        stripped_value = value.strip()
        if stripped_value.isdecimal():
            parsed_value = int(stripped_value)
            return parsed_value if parsed_value >= 0 else None
    return None


def _clamp_score(value: int) -> int:
    if value < 0:
        return 0
    if value > 100:
        return 100
    return value


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped_reasons: list[str] = []
    for reason in reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)
    return deduped_reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "CONFIDENCE_SCORE_TYPE",
    "DEFAULT_SCORING_SOURCE_MODE",
    "DEFAULT_SCORING_VERSION",
    "KAIROS_BACKTESTING_FOUNDATION_MODE",
    "KAIROS_CONFIDENCE_SCORING_MODE",
    "build_kairos_confidence_scoring_engine",
]
