from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_BACKTESTING_FOUNDATION_MODE: Final = "kairos_backtesting_foundation_only"
KAIROS_FIRST_OFFLINE_SANDBOX_MODE: Final = (
    "kairos_first_offline_prediction_sandbox"
)
DEFAULT_BACKTEST_VERSION: Final = "kairos_backtesting_foundation_v1"
DEFAULT_BACKTEST_SOURCE_MODE: Final = "offline_sandbox"

_COMPLETED_STATUS_SHORT_VALUES: Final = frozenset({"FT", "AET", "PEN"})
_UNSAFE_SOURCE_KEYS: Final = frozenset({"raw_payload"})
_UNSAFE_CREDENTIAL_KEYS: Final = frozenset(
    {"api_key", "auth", "secret", "token"}
)
_UNSAFE_MARKET_KEYS: Final = frozenset({"odds", "bookmaker", "stake"})
_UNSAFE_DECISION_KEYS: Final = frozenset(
    {
        "betting",
        "prediction",
        "predictions",
        "official_prediction",
        "prediction_record",
        "model_output",
        "confidence_score",
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


def build_kairos_backtesting_foundation(
    sandbox_outputs: Sequence[Mapping[str, Any]],
    completed_fixture_rows: Sequence[Mapping[str, Any]],
    *,
    backtest_version: str = DEFAULT_BACKTEST_VERSION,
    source_mode: str = DEFAULT_BACKTEST_SOURCE_MODE,
) -> dict[str, Any]:
    backtest_version_value = _safe_text(backtest_version)
    source_mode_value = _safe_text(source_mode)
    sandbox_count = len(sandbox_outputs)
    fixture_count = len(completed_fixture_rows)

    completed_fixture_count = 0
    missing_result_count = 0
    evaluable_fixture_count = 0
    outcome_distribution = {"home_win": 0, "draw": 0, "away_win": 0}

    for fixture_row in completed_fixture_rows:
        if not _is_completed_fixture(fixture_row):
            continue
        completed_fixture_count += 1
        result = _fixture_result(fixture_row)
        if result is None:
            missing_result_count += 1
            continue
        evaluable_fixture_count += 1
        outcome_distribution[result] += 1

    matched_fixture_count = evaluable_fixture_count if sandbox_count > 0 else 0
    unmatched_sandbox_count = (
        0 if sandbox_count > 0 and evaluable_fixture_count > 0 else sandbox_count
    )
    non_evaluable_count = fixture_count - evaluable_fixture_count
    evaluation_summary = {
        "has_evaluable_sample": sandbox_count > 0 and evaluable_fixture_count > 0,
        "sample_is_empty": sandbox_count == 0 or fixture_count == 0,
        "descriptive_only": True,
    }
    blocking_reasons = _blocking_reasons(
        backtest_version_present=bool(backtest_version_value),
        source_mode_present=bool(source_mode_value),
        sandbox_outputs=sandbox_outputs,
        completed_fixture_rows=completed_fixture_rows,
        sandbox_count=sandbox_count,
        fixture_count=fixture_count,
        evaluable_fixture_count=evaluable_fixture_count,
    )
    backtest_report_created = (
        not blocking_reasons and evaluation_summary["has_evaluable_sample"]
    )

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_BACKTESTING_FOUNDATION_MODE,
        "backtest_version": backtest_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "probability_created": False,
        "backtest_report_created": backtest_report_created,
        "sandbox_count": sandbox_count,
        "fixture_count": fixture_count,
        "matched_fixture_count": matched_fixture_count,
        "unmatched_sandbox_count": unmatched_sandbox_count,
        "evaluable_count": evaluable_fixture_count,
        "non_evaluable_count": non_evaluable_count,
        "completed_fixture_count": completed_fixture_count,
        "missing_result_count": missing_result_count,
        "outcome_distribution": outcome_distribution,
        "evaluation_summary": evaluation_summary,
        "blocking_reasons": blocking_reasons,
    }


def _blocking_reasons(
    *,
    backtest_version_present: bool,
    source_mode_present: bool,
    sandbox_outputs: Sequence[Mapping[str, Any]],
    completed_fixture_rows: Sequence[Mapping[str, Any]],
    sandbox_count: int,
    fixture_count: int,
    evaluable_fixture_count: int,
) -> list[str]:
    reasons: list[str] = []
    if not backtest_version_present:
        reasons.append("backtest_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    if sandbox_count == 0:
        reasons.append("sandbox_outputs_empty")
    if fixture_count == 0:
        reasons.append("completed_fixture_rows_empty")
    if sandbox_count > 0 and evaluable_fixture_count == 0:
        reasons.append("no_evaluable_completed_fixtures")

    for sandbox_output in sandbox_outputs:
        _append_sandbox_reasons(reasons, sandbox_output)
    for fixture_row in completed_fixture_rows:
        _append_fixture_reasons(reasons, fixture_row)
    return _dedupe_reasons(reasons)


def _append_sandbox_reasons(
    reasons: list[str],
    sandbox_output: Mapping[str, Any],
) -> None:
    if sandbox_output.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("sandbox_wrong_provider")
    if sandbox_output.get("mode") != KAIROS_FIRST_OFFLINE_SANDBOX_MODE:
        reasons.append("sandbox_wrong_mode")
    if sandbox_output.get("sandbox_hypothesis_created") is not True:
        reasons.append("sandbox_hypothesis_not_created")
    if sandbox_output.get("allowed_by_protocol_gate") is not True:
        reasons.append("sandbox_not_allowed_by_protocol_gate")
    if _count_is_empty(_non_negative_int_like(sandbox_output.get("candidate_count"))):
        reasons.append("sandbox_candidate_count_empty")
    if _count_is_empty(_non_negative_int_like(sandbox_output.get("accepted_count"))):
        reasons.append("sandbox_accepted_count_empty")
    _append_flag_reasons(reasons, source_name="sandbox", payload=sandbox_output)
    _append_unsafe_key_reasons(
        reasons,
        source_name="sandbox",
        present_keys=_nested_keys(sandbox_output),
    )
    if _has_blocking_reasons(sandbox_output.get("blocking_reasons")):
        reasons.append("sandbox_blocking_reasons_present")


def _append_fixture_reasons(
    reasons: list[str],
    fixture_row: Mapping[str, Any],
) -> None:
    if fixture_row.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("fixture_wrong_provider")
    _append_unsafe_key_reasons(
        reasons,
        source_name="fixture",
        present_keys=_nested_keys(fixture_row),
    )


def _append_flag_reasons(
    reasons: list[str],
    *,
    source_name: str,
    payload: Mapping[str, Any],
) -> None:
    if _is_true(payload.get("prediction_created")):
        reasons.append(f"{source_name}_created_prediction_flag")
    if _is_true(payload.get("official_prediction_created")):
        reasons.append(f"{source_name}_created_official_prediction_flag")
    if _is_true(payload.get("prediction_record_created")):
        reasons.append(f"{source_name}_created_prediction_record_flag")
    if _is_true(payload.get("betting_created")):
        reasons.append(f"{source_name}_created_betting_flag")
    if _is_true(payload.get("ml_model_used")):
        reasons.append(f"{source_name}_used_ml_model")
    if _is_true(payload.get("confidence_score_created")):
        reasons.append(f"{source_name}_created_confidence_flag")
    if _is_true(payload.get("probability_created")):
        reasons.append(f"{source_name}_created_probability_flag")


def _append_unsafe_key_reasons(
    reasons: list[str],
    *,
    source_name: str,
    present_keys: set[str],
) -> None:
    if _UNSAFE_SOURCE_KEYS & present_keys:
        reasons.append(f"{source_name}_unsafe_source_material_present")
    if _UNSAFE_CREDENTIAL_KEYS & present_keys:
        reasons.append(f"{source_name}_unsafe_credential_material_present")
    if _UNSAFE_MARKET_KEYS & present_keys:
        reasons.append(f"{source_name}_unsafe_market_material_present")
    if _UNSAFE_DECISION_KEYS & present_keys:
        reasons.append(f"{source_name}_unsafe_decision_material_present")
    if _UNSAFE_FINANCIAL_KEYS & present_keys:
        reasons.append(f"{source_name}_unsafe_financial_material_present")


def _is_completed_fixture(fixture_row: Mapping[str, Any]) -> bool:
    return _safe_text(fixture_row.get("fixture_status_short")).upper() in (
        _COMPLETED_STATUS_SHORT_VALUES
    )


def _fixture_result(fixture_row: Mapping[str, Any]) -> str | None:
    if _positive_int_like(fixture_row.get("provider_fixture_id")) is None:
        return None
    score_pair = _score_pair(
        fixture_row.get("score_fulltime_home"),
        fixture_row.get("score_fulltime_away"),
    )
    if score_pair is None:
        score_pair = _score_pair(
            fixture_row.get("goals_home"),
            fixture_row.get("goals_away"),
        )
    if score_pair is None:
        return None
    home_score, away_score = score_pair
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"


def _score_pair(home_value: Any, away_value: Any) -> tuple[int, int] | None:
    home_score = _non_negative_int_like(home_value)
    away_score = _non_negative_int_like(away_value)
    if home_score is None or away_score is None:
        return None
    return home_score, away_score


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


def _count_is_empty(value: int | None) -> bool:
    return value is None or value == 0


def _positive_int_like(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str):
        stripped_value = value.strip()
        if stripped_value.isdecimal():
            parsed_value = int(stripped_value)
            return parsed_value if parsed_value > 0 else None
    return None


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


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped_reasons: list[str] = []
    for reason in reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)
    return deduped_reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "DEFAULT_BACKTEST_SOURCE_MODE",
    "DEFAULT_BACKTEST_VERSION",
    "KAIROS_BACKTESTING_FOUNDATION_MODE",
    "KAIROS_FIRST_OFFLINE_SANDBOX_MODE",
    "build_kairos_backtesting_foundation",
]
