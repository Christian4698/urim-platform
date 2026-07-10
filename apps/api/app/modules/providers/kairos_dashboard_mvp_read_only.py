from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_DASHBOARD_MVP_MODE: Final = "kairos_dashboard_mvp_read_only"
DEFAULT_DASHBOARD_VERSION: Final = "kairos_dashboard_mvp_v1"
DEFAULT_DASHBOARD_SOURCE_MODE: Final = "read_only_aggregate"
CONFIDENCE_SCORE_TYPE: Final = "technical_signal_quality"

_CARD_MODES: Final = {
    "data_freshness": "fixture_data_freshness_provider_audit_trail",
    "feature_snapshots": "fixture_feature_snapshot_contract_without_ml",
    "baseline_analytics": "fixture_baseline_analytics_without_official_prediction",
    "protocol_gate": "kairos_prediction_protocol_gate_only",
    "offline_sandbox": "kairos_first_offline_prediction_sandbox",
    "backtesting": "kairos_backtesting_foundation_only",
    "confidence_scoring": "kairos_confidence_scoring_engine",
}
_BLOCKING_TRUE_FLAGS: Final = (
    "prediction_created",
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "probability_created",
)
_UNSAFE_SOURCE_KEYS: Final = frozenset({"raw_payload"})
_UNSAFE_CREDENTIAL_KEYS: Final = frozenset(
    {"api_key", "auth", "secret", "token"}
)
_UNSAFE_MARKET_KEYS: Final = frozenset({"odds", "bookmaker", "stake"})
_UNSAFE_DECISION_KEYS: Final = frozenset(
    {
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
_CONFIDENCE_BANDS: Final = frozenset(
    {"blocked", "low", "medium", "high", "unknown"}
)


def build_kairos_dashboard_mvp_read_only(
    *,
    data_freshness_audit: Mapping[str, Any] | None = None,
    feature_snapshot_contract: Mapping[str, Any] | None = None,
    baseline_analytics: Mapping[str, Any] | None = None,
    protocol_gate: Mapping[str, Any] | None = None,
    offline_sandbox: Mapping[str, Any] | None = None,
    backtesting_report: Mapping[str, Any] | None = None,
    confidence_scoring: Mapping[str, Any] | None = None,
    dashboard_version: str = DEFAULT_DASHBOARD_VERSION,
    source_mode: str = DEFAULT_DASHBOARD_SOURCE_MODE,
) -> dict[str, Any]:
    dashboard_version_value = _safe_text(dashboard_version)
    source_mode_value = _safe_text(source_mode)
    sources = {
        "data_freshness": data_freshness_audit,
        "feature_snapshots": feature_snapshot_contract,
        "baseline_analytics": baseline_analytics,
        "protocol_gate": protocol_gate,
        "offline_sandbox": offline_sandbox,
        "backtesting": backtesting_report,
        "confidence_scoring": confidence_scoring,
    }
    blocking_reasons = _blocking_reasons(
        dashboard_version_present=bool(dashboard_version_value),
        source_mode_present=bool(source_mode_value),
        sources=sources,
    )
    overall_status = _overall_status(blocking_reasons)

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_DASHBOARD_MVP_MODE,
        "dashboard_version": dashboard_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "api_football_call_created": False,
        "ingestion_created": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "probability_created": False,
        "dashboard_ready": overall_status == "ready",
        "cards": {
            "data_freshness": _data_freshness_card(data_freshness_audit),
            "feature_snapshots": _feature_snapshots_card(
                feature_snapshot_contract
            ),
            "baseline_analytics": _baseline_analytics_card(baseline_analytics),
            "protocol_gate": _protocol_gate_card(protocol_gate),
            "offline_sandbox": _offline_sandbox_card(offline_sandbox),
            "backtesting": _backtesting_card(backtesting_report),
            "confidence_scoring": _confidence_scoring_card(confidence_scoring),
        },
        "summary": {
            "overall_status": overall_status,
            "confidence_band": _summary_confidence_band(confidence_scoring),
            "confidence_score_type": _summary_confidence_score_type(
                confidence_scoring
            ),
            "not_probability": True,
            "not_for_betting": True,
            "not_a_guarantee": True,
        },
        "blocking_reasons": blocking_reasons,
    }


def _blocking_reasons(
    *,
    dashboard_version_present: bool,
    source_mode_present: bool,
    sources: Mapping[str, Mapping[str, Any] | None],
) -> list[str]:
    reasons: list[str] = []
    if not dashboard_version_present:
        reasons.append("dashboard_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    for card_name, source in sources.items():
        if source is None:
            reasons.append(f"missing_{card_name}")
            continue
        reasons.extend(_source_blocking_reasons(card_name, source))
    return _dedupe_reasons(reasons)


def _source_blocking_reasons(card_name: str, source: Any) -> list[str]:
    reasons: list[str] = []
    if not isinstance(source, Mapping):
        return [f"{card_name}_not_mapping"]

    if source.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append(f"{card_name}_wrong_provider")
    if _safe_text(source.get("mode")) != _CARD_MODES[card_name]:
        reasons.append(f"{card_name}_wrong_mode")
    for flag_name in _BLOCKING_TRUE_FLAGS:
        if _is_true(source.get(flag_name)):
            reasons.append(_flag_reason(card_name, flag_name))
    _append_unsafe_key_reasons(reasons, card_name, _nested_keys(source))
    _append_card_readiness_reasons(reasons, card_name, source)
    if _has_blocking_reasons(source.get("blocking_reasons")):
        reasons.append(f"{card_name}_blocking_reasons_present")
    return _dedupe_reasons(reasons)


def _append_card_readiness_reasons(
    reasons: list[str],
    card_name: str,
    source: Mapping[str, Any],
) -> None:
    if card_name == "data_freshness":
        if source.get("ready_for_internal_read") is not True:
            reasons.append("data_freshness_not_ready")
        return
    if card_name == "feature_snapshots":
        if _non_negative_int_like(source.get("accepted_count")) in (None, 0):
            reasons.append("feature_snapshots_empty")
        return
    if card_name == "baseline_analytics":
        if _non_negative_int_like(source.get("accepted_count")) in (None, 0):
            reasons.append("baseline_analytics_empty")
        return
    if card_name == "protocol_gate":
        if source.get("allowed_for_future_offline_prediction_sandbox") is not True:
            reasons.append("protocol_gate_not_allowing_sandbox")
        if source.get("required_inputs_present") is not True:
            reasons.append("protocol_gate_inputs_missing")
        return
    if card_name == "offline_sandbox":
        if source.get("sandbox_hypothesis_created") is not True:
            reasons.append("offline_sandbox_hypothesis_missing")
        if source.get("allowed_by_protocol_gate") is not True:
            reasons.append("offline_sandbox_not_allowed")
        return
    if card_name == "backtesting":
        if source.get("backtest_report_created") is not True:
            reasons.append("backtesting_report_missing")
        return
    if card_name == "confidence_scoring":
        if source.get("confidence_score_created") is not True:
            reasons.append("confidence_scoring_score_missing")
        if source.get("confidence_score_type") != CONFIDENCE_SCORE_TYPE:
            reasons.append("confidence_scoring_wrong_score_type")
        if source.get("not_probability") is not True:
            reasons.append("confidence_scoring_probability_guard_missing")
        if source.get("not_for_betting") is not True:
            reasons.append("confidence_scoring_betting_guard_missing")
        if source.get("not_a_guarantee") is not True:
            reasons.append("confidence_scoring_guarantee_guard_missing")


def _flag_reason(card_name: str, flag_name: str) -> str:
    if flag_name == "prediction_created":
        return f"{card_name}_created_prediction_flag"
    if flag_name == "official_prediction_created":
        return f"{card_name}_created_official_prediction_flag"
    if flag_name == "prediction_record_created":
        return f"{card_name}_created_prediction_record_flag"
    if flag_name == "betting_created":
        return f"{card_name}_created_betting_flag"
    if flag_name == "ml_model_used":
        return f"{card_name}_used_ml_model"
    return f"{card_name}_created_probability_flag"


def _append_unsafe_key_reasons(
    reasons: list[str],
    card_name: str,
    present_keys: set[str],
) -> None:
    if _UNSAFE_SOURCE_KEYS & present_keys:
        reasons.append(f"{card_name}_unsafe_source_material_present")
    if _UNSAFE_CREDENTIAL_KEYS & present_keys:
        reasons.append(f"{card_name}_unsafe_credential_material_present")
    if _UNSAFE_MARKET_KEYS & present_keys:
        reasons.append(f"{card_name}_unsafe_market_material_present")
    if _UNSAFE_DECISION_KEYS & present_keys:
        reasons.append(f"{card_name}_unsafe_decision_material_present")
    if _UNSAFE_FINANCIAL_KEYS & present_keys:
        reasons.append(f"{card_name}_unsafe_financial_material_present")


def _data_freshness_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("data_freshness", source)
    if not isinstance(source, Mapping):
        return card
    card["ready_for_internal_read"] = source.get("ready_for_internal_read") is True
    card["row_count"] = _safe_count(source.get("row_count"))
    card["fresh_count"] = _safe_count(source.get("fresh_count"))
    card["stale_count"] = _safe_count(source.get("stale_count"))
    return card


def _feature_snapshots_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("feature_snapshots", source)
    if not isinstance(source, Mapping):
        return card
    card["candidate_count"] = _safe_count(source.get("candidate_count"))
    card["accepted_count"] = _safe_count(source.get("accepted_count"))
    card["rejected_count"] = _safe_count(source.get("rejected_count"))
    return card


def _baseline_analytics_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("baseline_analytics", source)
    if not isinstance(source, Mapping):
        return card
    card["candidate_count"] = _safe_count(source.get("candidate_count"))
    card["accepted_count"] = _safe_count(source.get("accepted_count"))
    card["completed_fixture_count"] = _safe_count(
        source.get("completed_fixture_count")
    )
    card["scheduled_fixture_count"] = _safe_count(
        source.get("scheduled_fixture_count")
    )
    return card


def _protocol_gate_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("protocol_gate", source)
    if not isinstance(source, Mapping):
        return card
    card["allowed_for_future_offline_prediction_sandbox"] = (
        source.get("allowed_for_future_offline_prediction_sandbox") is True
    )
    card["required_inputs_present"] = source.get("required_inputs_present") is True
    card["baseline_sample_accepted"] = source.get("baseline_sample_accepted") is True
    return card


def _offline_sandbox_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("offline_sandbox", source)
    if not isinstance(source, Mapping):
        return card
    card["sandbox_hypothesis_created"] = (
        source.get("sandbox_hypothesis_created") is True
    )
    card["allowed_by_protocol_gate"] = source.get("allowed_by_protocol_gate") is True
    card["candidate_count"] = _safe_count(source.get("candidate_count"))
    card["accepted_count"] = _safe_count(source.get("accepted_count"))
    return card


def _backtesting_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("backtesting", source)
    if not isinstance(source, Mapping):
        return card
    card["backtest_report_created"] = (
        source.get("backtest_report_created") is True
    )
    card["matched_fixture_count"] = _safe_count(
        source.get("matched_fixture_count")
    )
    card["evaluable_count"] = _safe_count(source.get("evaluable_count"))
    card["missing_result_count"] = _safe_count(
        source.get("missing_result_count")
    )
    return card


def _confidence_scoring_card(source: Mapping[str, Any] | None) -> dict[str, Any]:
    card = _base_card("confidence_scoring", source)
    if not isinstance(source, Mapping):
        return card
    card["confidence_score_created"] = (
        source.get("confidence_score_created") is True
    )
    card["confidence_score_type"] = _summary_confidence_score_type(source)
    card["confidence_score"] = _safe_score(source.get("confidence_score"))
    card["confidence_band"] = _summary_confidence_band(source)
    card["not_probability"] = source.get("not_probability") is True
    card["not_for_betting"] = source.get("not_for_betting") is True
    card["not_a_guarantee"] = source.get("not_a_guarantee") is True
    return card


def _base_card(card_name: str, source: Any) -> dict[str, Any]:
    if source is None:
        return {"present": False, "status": "missing"}
    if not isinstance(source, Mapping):
        return {
            "present": True,
            "provider": "unknown",
            "mode": "unknown",
            "status": "blocked",
            "read_only": False,
            "db_writes": False,
            "blocking_reason_count": 0,
        }

    return {
        "present": True,
        "provider": _safe_text(source.get("provider")) or "unknown",
        "mode": _safe_text(source.get("mode")) or "unknown",
        "status": "blocked"
        if _source_blocking_reasons(card_name, source)
        else "ready",
        "read_only": source.get("read_only") is True,
        "db_writes": source.get("db_writes") is True,
        "blocking_reason_count": _blocking_reason_count(
            source.get("blocking_reasons")
        ),
    }


def _summary_confidence_band(source: Any) -> str:
    if not isinstance(source, Mapping):
        return "unknown"
    band = _safe_text(source.get("confidence_band"))
    return band if band in _CONFIDENCE_BANDS else "unknown"


def _summary_confidence_score_type(source: Any) -> str:
    if not isinstance(source, Mapping):
        return "unknown"
    if source.get("confidence_score_type") == CONFIDENCE_SCORE_TYPE:
        return CONFIDENCE_SCORE_TYPE
    return "unknown"


def _overall_status(blocking_reasons: list[str]) -> str:
    if not blocking_reasons:
        return "ready"
    if any(not reason.startswith("missing_") for reason in blocking_reasons):
        return "blocked"
    return "partial"


def _nested_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        keys = {str(key).strip().lower() for key in value}
        for nested_value in value.values():
            for nested_key in _nested_keys(nested_value):
                keys.add(nested_key)
        return keys
    if isinstance(value, list | tuple | set):
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


def _blocking_reason_count(value: Any) -> int:
    if not _has_blocking_reasons(value):
        return 0
    if isinstance(value, str):
        return 1
    if isinstance(value, Mapping | list | tuple | set):
        return len(value)
    return 1


def _safe_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _is_true(value: Any) -> bool:
    return value is True


def _safe_count(value: Any) -> int:
    parsed_value = _non_negative_int_like(value)
    return parsed_value if parsed_value is not None else 0


def _safe_score(value: Any) -> int | None:
    parsed_value = _non_negative_int_like(value)
    if parsed_value is None:
        return None
    if parsed_value > 100:
        return 100
    return parsed_value


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
    "CONFIDENCE_SCORE_TYPE",
    "DEFAULT_DASHBOARD_SOURCE_MODE",
    "DEFAULT_DASHBOARD_VERSION",
    "KAIROS_DASHBOARD_MVP_MODE",
    "build_kairos_dashboard_mvp_read_only",
]
