from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_PREDICTION_PROTOCOL_GATE_MODE: Final = "kairos_prediction_protocol_gate_only"
BASELINE_ANALYTICS_MODE: Final = (
    "fixture_baseline_analytics_without_official_prediction"
)
DEFAULT_PROTOCOL_VERSION: Final = "kairos_prediction_protocol_v1"
DEFAULT_PROTOCOL_SOURCE_MODE: Final = "baseline_analytics"

_REQUIRED_BASELINE_KEYS: Final = frozenset(
    {
        "provider",
        "mode",
        "prediction_created",
        "official_prediction_created",
        "betting_created",
        "ml_model_used",
        "confidence_score_created",
        "candidate_count",
        "accepted_count",
        "rejected_count",
        "completed_fixture_count",
        "scheduled_fixture_count",
        "descriptive_signals",
        "blocking_reasons",
    }
)

_UNSAFE_SOURCE_KEYS: Final = frozenset({"raw_payload"})
_UNSAFE_CREDENTIAL_KEYS: Final = frozenset(
    {"api_key", "auth", "secret", "token"}
)
_UNSAFE_MARKET_KEYS: Final = frozenset({"odds", "bookmaker", "stake"})
_UNSAFE_DECISION_KEYS: Final = frozenset(
    {
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
)


def build_kairos_prediction_protocol_gate(
    baseline_analytics: Mapping[str, Any],
    *,
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
    source_mode: str = DEFAULT_PROTOCOL_SOURCE_MODE,
) -> dict[str, Any]:
    protocol_version_value = _safe_text(protocol_version)
    source_mode_value = _safe_text(source_mode)
    present_keys = _nested_keys(baseline_analytics)

    candidate_count = _non_negative_int_like(
        baseline_analytics.get("candidate_count")
    )
    accepted_count = _non_negative_int_like(baseline_analytics.get("accepted_count"))
    rejected_count = _non_negative_int_like(baseline_analytics.get("rejected_count"))
    completed_fixture_count = _non_negative_int_like(
        baseline_analytics.get("completed_fixture_count")
    )
    scheduled_fixture_count = _non_negative_int_like(
        baseline_analytics.get("scheduled_fixture_count")
    )
    descriptive_signals = baseline_analytics.get("descriptive_signals")
    sample_is_empty = _sample_is_empty(descriptive_signals)
    has_completed_sample = _sample_flag(
        descriptive_signals,
        "has_completed_sample",
        fallback=bool(completed_fixture_count),
    )
    has_scheduled_sample = _sample_flag(
        descriptive_signals,
        "has_scheduled_sample",
        fallback=bool(scheduled_fixture_count),
    )
    required_inputs_present = _REQUIRED_BASELINE_KEYS.issubset(baseline_analytics)
    baseline_sample_accepted = (
        candidate_count is not None
        and candidate_count > 0
        and accepted_count is not None
        and accepted_count > 0
        and sample_is_empty is False
    )
    descriptive_only_confirmed = _descriptive_only_confirmed(
        baseline_analytics=baseline_analytics,
        present_keys=present_keys,
    )
    blocking_reasons = _blocking_reasons(
        protocol_version_present=bool(protocol_version_value),
        source_mode_present=bool(source_mode_value),
        required_inputs_present=required_inputs_present,
        baseline_analytics=baseline_analytics,
        present_keys=present_keys,
        candidate_count=candidate_count,
        accepted_count=accepted_count,
        baseline_sample_accepted=baseline_sample_accepted,
        sample_is_empty=sample_is_empty,
        descriptive_only_confirmed=descriptive_only_confirmed,
    )

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_PREDICTION_PROTOCOL_GATE_MODE,
        "protocol_version": protocol_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "prediction_created": False,
        "official_prediction_created": False,
        "offline_prediction_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "allowed_for_future_offline_prediction_sandbox": not blocking_reasons,
        "required_inputs_present": required_inputs_present,
        "baseline_sample_accepted": baseline_sample_accepted,
        "descriptive_only_confirmed": descriptive_only_confirmed,
        "candidate_count": candidate_count or 0,
        "accepted_count": accepted_count or 0,
        "rejected_count": rejected_count or 0,
        "completed_fixture_count": completed_fixture_count or 0,
        "scheduled_fixture_count": scheduled_fixture_count or 0,
        "has_completed_sample": has_completed_sample,
        "has_scheduled_sample": has_scheduled_sample,
        "blocking_reasons": blocking_reasons,
    }


def _blocking_reasons(
    *,
    protocol_version_present: bool,
    source_mode_present: bool,
    required_inputs_present: bool,
    baseline_analytics: Mapping[str, Any],
    present_keys: set[str],
    candidate_count: int | None,
    accepted_count: int | None,
    baseline_sample_accepted: bool,
    sample_is_empty: bool | None,
    descriptive_only_confirmed: bool,
) -> list[str]:
    reasons: list[str] = []
    if not protocol_version_present:
        reasons.append("protocol_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    if not required_inputs_present:
        reasons.append("required_inputs_missing")
    if baseline_analytics.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("wrong_provider")
    if baseline_analytics.get("mode") != BASELINE_ANALYTICS_MODE:
        reasons.append("wrong_baseline_mode")
    if _is_true(baseline_analytics.get("prediction_created")):
        reasons.append("input_created_prediction_flag")
    if _is_true(baseline_analytics.get("official_prediction_created")):
        reasons.append("input_created_official_prediction_flag")
    if _is_true(baseline_analytics.get("offline_prediction_created")):
        reasons.append("input_created_offline_prediction_flag")
    if _is_true(baseline_analytics.get("betting_created")):
        reasons.append("input_created_betting_flag")
    if _is_true(baseline_analytics.get("ml_model_used")):
        reasons.append("input_used_ml_model")
    if _is_true(baseline_analytics.get("confidence_score_created")):
        reasons.append("input_created_confidence_flag")
    if _UNSAFE_SOURCE_KEYS & present_keys:
        reasons.append("unsafe_source_material_present")
    if _UNSAFE_CREDENTIAL_KEYS & present_keys:
        reasons.append("unsafe_credential_material_present")
    if _UNSAFE_MARKET_KEYS & present_keys:
        reasons.append("unsafe_market_material_present")
    if _UNSAFE_DECISION_KEYS & present_keys:
        reasons.append("unsafe_decision_material_present")
    if candidate_count is None or candidate_count == 0:
        reasons.append("candidate_count_empty")
    if accepted_count is None or accepted_count == 0:
        reasons.append("accepted_count_empty")
    if sample_is_empty is True or not baseline_sample_accepted:
        reasons.append("sample_is_empty")
    if _has_baseline_blocking_reasons(baseline_analytics.get("blocking_reasons")):
        reasons.append("baseline_blocking_reasons_present")
    if not descriptive_only_confirmed:
        reasons.append("descriptive_only_not_confirmed")
    return _dedupe_reasons(reasons)


def _descriptive_only_confirmed(
    *,
    baseline_analytics: Mapping[str, Any],
    present_keys: set[str],
) -> bool:
    unsafe_keys = (
        _UNSAFE_SOURCE_KEYS
        | _UNSAFE_CREDENTIAL_KEYS
        | _UNSAFE_MARKET_KEYS
        | _UNSAFE_DECISION_KEYS
    )
    if unsafe_keys & present_keys:
        return False
    return not any(
        _is_true(baseline_analytics.get(flag_name))
        for flag_name in (
            "prediction_created",
            "official_prediction_created",
            "offline_prediction_created",
            "betting_created",
            "ml_model_used",
            "confidence_score_created",
        )
    )


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


def _sample_is_empty(value: Any) -> bool | None:
    if isinstance(value, Mapping):
        sample_is_empty = value.get("sample_is_empty")
        if isinstance(sample_is_empty, bool):
            return sample_is_empty
    return None


def _sample_flag(value: Any, field_name: str, *, fallback: bool) -> bool:
    if isinstance(value, Mapping):
        flag_value = value.get(field_name)
        if isinstance(flag_value, bool):
            return flag_value
    return fallback


def _has_baseline_blocking_reasons(value: Any) -> bool:
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


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped_reasons: list[str] = []
    for reason in reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)
    return deduped_reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "BASELINE_ANALYTICS_MODE",
    "DEFAULT_PROTOCOL_SOURCE_MODE",
    "DEFAULT_PROTOCOL_VERSION",
    "KAIROS_PREDICTION_PROTOCOL_GATE_MODE",
    "build_kairos_prediction_protocol_gate",
]
