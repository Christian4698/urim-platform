from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_FIRST_OFFLINE_SANDBOX_MODE: Final = (
    "kairos_first_offline_prediction_sandbox"
)
KAIROS_PROTOCOL_GATE_MODE: Final = "kairos_prediction_protocol_gate_only"
BASELINE_ANALYTICS_MODE: Final = (
    "fixture_baseline_analytics_without_official_prediction"
)
DEFAULT_SANDBOX_VERSION: Final = "kairos_offline_sandbox_v1"
DEFAULT_SANDBOX_SOURCE_MODE: Final = "protocol_gate"

_UNSAFE_SOURCE_KEYS: Final = frozenset({"raw_payload"})
_UNSAFE_CREDENTIAL_KEYS: Final = frozenset(
    {"api_key", "auth", "secret", "token"}
)
_UNSAFE_MARKET_KEYS: Final = frozenset({"odds", "bookmaker", "stake"})
_UNSAFE_DECISION_KEYS: Final = frozenset(
    {
        "prediction",
        "predictions",
        "prediction_record",
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


def build_kairos_offline_prediction_sandbox(
    protocol_gate: Mapping[str, Any],
    baseline_analytics: Mapping[str, Any],
    *,
    sandbox_version: str = DEFAULT_SANDBOX_VERSION,
    source_mode: str = DEFAULT_SANDBOX_SOURCE_MODE,
) -> dict[str, Any]:
    sandbox_version_value = _safe_text(sandbox_version)
    source_mode_value = _safe_text(source_mode)
    protocol_gate_keys = _nested_keys(protocol_gate)
    baseline_keys = _nested_keys(baseline_analytics)

    gate_candidate_count = _non_negative_int_like(protocol_gate.get("candidate_count"))
    gate_accepted_count = _non_negative_int_like(protocol_gate.get("accepted_count"))
    baseline_candidate_count = _non_negative_int_like(
        baseline_analytics.get("candidate_count")
    )
    baseline_accepted_count = _non_negative_int_like(
        baseline_analytics.get("accepted_count")
    )
    candidate_count = (
        baseline_candidate_count
        if baseline_candidate_count is not None
        else gate_candidate_count or 0
    )
    accepted_count = (
        baseline_accepted_count
        if baseline_accepted_count is not None
        else gate_accepted_count or 0
    )
    baseline_completed_fixture_count = _non_negative_int_like(
        baseline_analytics.get("completed_fixture_count")
    )
    gate_completed_fixture_count = _non_negative_int_like(
        protocol_gate.get("completed_fixture_count")
    )
    baseline_scheduled_fixture_count = _non_negative_int_like(
        baseline_analytics.get("scheduled_fixture_count")
    )
    gate_scheduled_fixture_count = _non_negative_int_like(
        protocol_gate.get("scheduled_fixture_count")
    )
    completed_fixture_count = (
        baseline_completed_fixture_count
        if baseline_completed_fixture_count is not None
        else gate_completed_fixture_count or 0
    )
    scheduled_fixture_count = (
        baseline_scheduled_fixture_count
        if baseline_scheduled_fixture_count is not None
        else gate_scheduled_fixture_count or 0
    )
    allowed_by_protocol_gate = (
        protocol_gate.get("allowed_for_future_offline_prediction_sandbox") is True
    )
    blocking_reasons = _blocking_reasons(
        sandbox_version_present=bool(sandbox_version_value),
        source_mode_present=bool(source_mode_value),
        protocol_gate=protocol_gate,
        baseline_analytics=baseline_analytics,
        protocol_gate_keys=protocol_gate_keys,
        baseline_keys=baseline_keys,
        allowed_by_protocol_gate=allowed_by_protocol_gate,
        gate_candidate_count=gate_candidate_count,
        gate_accepted_count=gate_accepted_count,
        baseline_candidate_count=baseline_candidate_count,
        baseline_accepted_count=baseline_accepted_count,
    )
    sandbox_hypothesis_created = not blocking_reasons

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_FIRST_OFFLINE_SANDBOX_MODE,
        "sandbox_version": sandbox_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "confidence_score_created": False,
        "probability_created": False,
        "sandbox_hypothesis_created": sandbox_hypothesis_created,
        "allowed_by_protocol_gate": allowed_by_protocol_gate,
        "candidate_count": candidate_count,
        "accepted_count": accepted_count,
        "completed_fixture_count": completed_fixture_count,
        "scheduled_fixture_count": scheduled_fixture_count,
        "sandbox_hypothesis": _sandbox_hypothesis(
            completed_fixture_count=completed_fixture_count,
            scheduled_fixture_count=scheduled_fixture_count,
        )
        if sandbox_hypothesis_created
        else None,
        "sandbox_notes": _sandbox_notes(),
        "blocking_reasons": blocking_reasons,
    }


def _blocking_reasons(
    *,
    sandbox_version_present: bool,
    source_mode_present: bool,
    protocol_gate: Mapping[str, Any],
    baseline_analytics: Mapping[str, Any],
    protocol_gate_keys: set[str],
    baseline_keys: set[str],
    allowed_by_protocol_gate: bool,
    gate_candidate_count: int | None,
    gate_accepted_count: int | None,
    baseline_candidate_count: int | None,
    baseline_accepted_count: int | None,
) -> list[str]:
    reasons: list[str] = []
    if not sandbox_version_present:
        reasons.append("sandbox_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    if protocol_gate.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("protocol_gate_wrong_provider")
    if baseline_analytics.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("baseline_wrong_provider")
    if protocol_gate.get("mode") != KAIROS_PROTOCOL_GATE_MODE:
        reasons.append("protocol_gate_wrong_mode")
    if baseline_analytics.get("mode") != BASELINE_ANALYTICS_MODE:
        reasons.append("baseline_wrong_mode")
    if not allowed_by_protocol_gate:
        reasons.append("protocol_gate_not_allowed")
    _append_flag_reasons(
        reasons,
        source_name="protocol_gate",
        payload=protocol_gate,
        include_offline_flag=True,
    )
    _append_flag_reasons(
        reasons,
        source_name="baseline",
        payload=baseline_analytics,
        include_offline_flag=False,
    )
    _append_unsafe_key_reasons(
        reasons,
        source_name="protocol_gate",
        present_keys=protocol_gate_keys,
    )
    _append_unsafe_key_reasons(
        reasons,
        source_name="baseline",
        present_keys=baseline_keys,
    )
    if _count_is_empty(gate_candidate_count) or _count_is_empty(
        baseline_candidate_count
    ):
        reasons.append("candidate_count_empty")
    if _count_is_empty(gate_accepted_count) or _count_is_empty(
        baseline_accepted_count
    ):
        reasons.append("accepted_count_empty")
    if _has_blocking_reasons(protocol_gate.get("blocking_reasons")):
        reasons.append("protocol_gate_blocking_reasons_present")
    if _has_blocking_reasons(baseline_analytics.get("blocking_reasons")):
        reasons.append("baseline_blocking_reasons_present")
    return _dedupe_reasons(reasons)


def _append_flag_reasons(
    reasons: list[str],
    *,
    source_name: str,
    payload: Mapping[str, Any],
    include_offline_flag: bool,
) -> None:
    if _is_true(payload.get("prediction_created")):
        reasons.append(f"{source_name}_created_prediction_flag")
    if _is_true(payload.get("official_prediction_created")):
        reasons.append(f"{source_name}_created_official_prediction_flag")
    if include_offline_flag and _is_true(payload.get("offline_prediction_created")):
        reasons.append(f"{source_name}_created_offline_prediction_flag")
    if _is_true(payload.get("betting_created")):
        reasons.append(f"{source_name}_created_betting_flag")
    if _is_true(payload.get("ml_model_used")):
        reasons.append(f"{source_name}_used_ml_model")
    if _is_true(payload.get("confidence_score_created")):
        reasons.append(f"{source_name}_created_confidence_flag")


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


def _sandbox_hypothesis(
    *,
    completed_fixture_count: int,
    scheduled_fixture_count: int,
) -> dict[str, Any]:
    return {
        "hypothesis_type": "descriptive_offline_sandbox",
        "basis": "baseline_analytics_only",
        "sample_state": _sample_state(
            completed_fixture_count=completed_fixture_count,
            scheduled_fixture_count=scheduled_fixture_count,
        ),
        "non_official": True,
        "not_for_betting": True,
    }


def _sample_state(
    *,
    completed_fixture_count: int,
    scheduled_fixture_count: int,
) -> str:
    if completed_fixture_count > 0 and scheduled_fixture_count > 0:
        return "completed_and_scheduled_sample"
    if completed_fixture_count > 0:
        return "completed_sample_only"
    if scheduled_fixture_count > 0:
        return "scheduled_sample_only"
    return "accepted_sample_without_fixture_family"


def _sandbox_notes() -> list[str]:
    return [
        "experimental_offline_only",
        "descriptive_baseline_only",
        "non_official",
        "not_for_betting",
    ]


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
    "DEFAULT_SANDBOX_SOURCE_MODE",
    "DEFAULT_SANDBOX_VERSION",
    "KAIROS_FIRST_OFFLINE_SANDBOX_MODE",
    "KAIROS_PROTOCOL_GATE_MODE",
    "build_kairos_offline_prediction_sandbox",
]
