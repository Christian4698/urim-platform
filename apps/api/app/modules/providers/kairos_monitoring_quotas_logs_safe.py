from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_MONITORING_MODE: Final = "kairos_monitoring_quotas_logs_safe"
KAIROS_DASHBOARD_MVP_MODE: Final = "kairos_dashboard_mvp_read_only"
DEFAULT_MONITORING_VERSION: Final = "kairos_monitoring_quotas_logs_safe_v1"
DEFAULT_MONITORING_SOURCE_MODE: Final = "read_only_in_memory_snapshots"

_ALLOWED_PROVIDER_PLANS: Final = frozenset({"unknown", "free", "paid", "test"})
_ALLOWED_DASHBOARD_STATUSES: Final = frozenset(
    {"unknown", "blocked", "partial", "ready"}
)
_STAGING_ALLOWED_USAGE_BANDS: Final = frozenset({"safe", "watch"})
_DASHBOARD_BLOCKING_TRUE_FLAGS: Final = (
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
_UNSAFE_PROVIDER_LINK_KEYS: Final = frozenset({"provider_url", "request_url"})
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


def build_kairos_monitoring_quotas_logs_safe(
    *,
    dashboard_payload: Mapping[str, Any] | None = None,
    quota_snapshot: Mapping[str, Any] | None = None,
    log_events: Sequence[Mapping[str, Any]] | None = None,
    monitoring_version: str = DEFAULT_MONITORING_VERSION,
    source_mode: str = DEFAULT_MONITORING_SOURCE_MODE,
) -> dict[str, Any]:
    monitoring_version_value = _safe_text(monitoring_version)
    source_mode_value = _safe_text(source_mode)
    quota_status = _quota_status(quota_snapshot)
    logs_safety = _logs_safety(log_events)
    dashboard_status = _dashboard_status(dashboard_payload)
    blocking_reasons = _blocking_reasons(
        monitoring_version_present=bool(monitoring_version_value),
        source_mode_present=bool(source_mode_value),
        dashboard_payload=dashboard_payload,
        quota_snapshot=quota_snapshot,
        log_events=log_events,
        quota_usage_band=quota_status["usage_band"],
        logs_safety=logs_safety,
    )
    monitoring_ready = not blocking_reasons
    ready_for_staging_checks = (
        monitoring_ready
        and dashboard_status["dashboard_ready"] is True
        and logs_safety["contains_secret"] is False
        and logs_safety["contains_raw_payload"] is False
        and quota_status["usage_band"] in _STAGING_ALLOWED_USAGE_BANDS
    )

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_MONITORING_MODE,
        "monitoring_version": monitoring_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "api_football_call_created": False,
        "quota_consumed": False,
        "persistent_logs_created": False,
        "job_created": False,
        "endpoint_created": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "probability_created": False,
        "monitoring_ready": monitoring_ready,
        "quota_status": quota_status,
        "logs_safety": logs_safety,
        "dashboard_status": dashboard_status,
        "staging_readiness": {
            "ready_for_staging_checks": ready_for_staging_checks,
            "requires_manual_review": not ready_for_staging_checks,
        },
        "blocking_reasons": blocking_reasons,
    }


def _blocking_reasons(
    *,
    monitoring_version_present: bool,
    source_mode_present: bool,
    dashboard_payload: Mapping[str, Any] | None,
    quota_snapshot: Mapping[str, Any] | None,
    log_events: Sequence[Mapping[str, Any]] | None,
    quota_usage_band: str,
    logs_safety: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not monitoring_version_present:
        reasons.append("monitoring_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    reasons.extend(_dashboard_reasons(dashboard_payload))
    reasons.extend(_quota_reasons(quota_snapshot, quota_usage_band))
    reasons.extend(_log_event_reasons(log_events))
    if logs_safety["redaction_required"] is True:
        reasons.append("log_events_redaction_required")
    return _dedupe_reasons(reasons)


def _dashboard_reasons(dashboard_payload: Any) -> list[str]:
    if dashboard_payload is None:
        return ["dashboard_payload_missing"]
    if not isinstance(dashboard_payload, Mapping):
        return ["dashboard_payload_not_mapping"]

    reasons: list[str] = []
    if dashboard_payload.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("dashboard_payload_wrong_provider")
    if _safe_text(dashboard_payload.get("mode")) != KAIROS_DASHBOARD_MVP_MODE:
        reasons.append("dashboard_payload_wrong_mode")
    if dashboard_payload.get("dashboard_ready") is not True:
        reasons.append("dashboard_payload_not_ready")
    if _has_blocking_reasons(dashboard_payload.get("blocking_reasons")):
        reasons.append("dashboard_payload_blocking_reasons_present")
    for flag_name in _DASHBOARD_BLOCKING_TRUE_FLAGS:
        if _is_true(dashboard_payload.get(flag_name)):
            reasons.append(_dashboard_flag_reason(flag_name))
    _append_unsafe_category_reasons(
        reasons,
        source_name="dashboard_payload",
        categories=_unsafe_categories(dashboard_payload),
    )
    return _dedupe_reasons(reasons)


def _quota_reasons(quota_snapshot: Any, usage_band: str) -> list[str]:
    if quota_snapshot is None:
        return ["quota_snapshot_missing"]
    if not isinstance(quota_snapshot, Mapping):
        return ["quota_snapshot_not_mapping"]

    reasons: list[str] = []
    if quota_snapshot.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("quota_snapshot_wrong_provider")
    if usage_band == "unknown":
        reasons.append("quota_usage_unknown")
    if usage_band == "critical":
        reasons.append("quota_usage_critical")
    if usage_band == "blocked":
        reasons.append("quota_usage_blocked")
    _append_unsafe_category_reasons(
        reasons,
        source_name="quota_snapshot",
        categories=_unsafe_categories(quota_snapshot),
    )
    return _dedupe_reasons(reasons)


def _log_event_reasons(log_events: Any) -> list[str]:
    if log_events is None:
        return []
    if not _is_log_sequence(log_events):
        return ["log_events_not_sequence"]

    reasons: list[str] = []
    for event in log_events:
        if not isinstance(event, Mapping):
            reasons.append("log_event_not_mapping")
            continue
        _append_unsafe_category_reasons(
            reasons,
            source_name="log_events",
            categories=_unsafe_categories(event),
        )
    return _dedupe_reasons(reasons)


def _dashboard_flag_reason(flag_name: str) -> str:
    if flag_name == "official_prediction_created":
        return "dashboard_payload_created_official_prediction_flag"
    if flag_name == "prediction_record_created":
        return "dashboard_payload_created_prediction_record_flag"
    if flag_name == "betting_created":
        return "dashboard_payload_created_betting_flag"
    if flag_name == "ml_model_used":
        return "dashboard_payload_used_ml_model"
    return "dashboard_payload_created_probability_flag"


def _append_unsafe_category_reasons(
    reasons: list[str],
    *,
    source_name: str,
    categories: set[str],
) -> None:
    if "source" in categories:
        reasons.append(f"{source_name}_unsafe_source_material_present")
    if "credential" in categories:
        reasons.append(f"{source_name}_unsafe_credential_material_present")
    if "provider_link" in categories:
        reasons.append(f"{source_name}_unsafe_provider_link_material_present")
    if "market" in categories:
        reasons.append(f"{source_name}_unsafe_market_material_present")
    if "decision" in categories:
        reasons.append(f"{source_name}_unsafe_decision_material_present")
    if "financial" in categories:
        reasons.append(f"{source_name}_unsafe_financial_material_present")


def _quota_status(quota_snapshot: Any) -> dict[str, Any]:
    if not isinstance(quota_snapshot, Mapping):
        return {
            "snapshot_present": False,
            "provider_plan": "unknown",
            "daily_limit": None,
            "daily_used": None,
            "daily_remaining": None,
            "usage_band": "unknown",
        }

    daily_limit = _non_negative_int_like(quota_snapshot.get("daily_limit"))
    daily_used = _non_negative_int_like(quota_snapshot.get("daily_used"))
    daily_remaining = None
    if daily_limit is not None and daily_used is not None:
        daily_remaining = max(daily_limit - daily_used, 0)

    return {
        "snapshot_present": True,
        "provider_plan": _provider_plan(quota_snapshot.get("provider_plan")),
        "daily_limit": daily_limit,
        "daily_used": daily_used,
        "daily_remaining": daily_remaining,
        "usage_band": _usage_band(daily_limit, daily_used),
    }


def _logs_safety(log_events: Any) -> dict[str, Any]:
    if log_events is None:
        return {
            "events_count": 0,
            "safe_events_count": 0,
            "blocked_events_count": 0,
            "redaction_required": False,
            "contains_secret": False,
            "contains_raw_payload": False,
        }
    if not _is_log_sequence(log_events):
        return {
            "events_count": 0,
            "safe_events_count": 0,
            "blocked_events_count": 0,
            "redaction_required": True,
            "contains_secret": False,
            "contains_raw_payload": False,
        }

    events_count = len(log_events)
    blocked_events_count = 0
    contains_secret = False
    contains_raw_payload = False
    redaction_required = False
    for event in log_events:
        if not isinstance(event, Mapping):
            blocked_events_count += 1
            redaction_required = True
            continue
        categories = _unsafe_categories(event)
        if categories:
            blocked_events_count += 1
            redaction_required = True
        if "credential" in categories:
            contains_secret = True
        if "source" in categories:
            contains_raw_payload = True

    return {
        "events_count": events_count,
        "safe_events_count": events_count - blocked_events_count,
        "blocked_events_count": blocked_events_count,
        "redaction_required": redaction_required,
        "contains_secret": contains_secret,
        "contains_raw_payload": contains_raw_payload,
    }


def _dashboard_status(dashboard_payload: Any) -> dict[str, Any]:
    if not isinstance(dashboard_payload, Mapping):
        return {
            "dashboard_payload_present": False,
            "dashboard_ready": False,
            "overall_status": "unknown",
        }

    return {
        "dashboard_payload_present": True,
        "dashboard_ready": dashboard_payload.get("dashboard_ready") is True,
        "overall_status": _dashboard_overall_status(dashboard_payload),
    }


def _dashboard_overall_status(dashboard_payload: Mapping[str, Any]) -> str:
    summary = dashboard_payload.get("summary")
    if not isinstance(summary, Mapping):
        return "unknown"
    status = _safe_text(summary.get("overall_status"))
    return status if status in _ALLOWED_DASHBOARD_STATUSES else "unknown"


def _usage_band(daily_limit: int | None, daily_used: int | None) -> str:
    if daily_limit is None or daily_used is None or daily_limit <= 0:
        return "unknown"
    if daily_used >= daily_limit:
        return "blocked"

    usage_percent = (daily_used * 100) / daily_limit
    if usage_percent <= 60:
        return "safe"
    if usage_percent <= 85:
        return "watch"
    return "critical"


def _provider_plan(value: Any) -> str:
    plan = _safe_text(value).lower()
    return plan if plan in _ALLOWED_PROVIDER_PLANS else "unknown"


def _unsafe_categories(value: Any) -> set[str]:
    keys = _nested_keys(value)
    text_terms = _nested_text_terms(value)
    terms = keys | text_terms
    categories: set[str] = set()
    if _UNSAFE_SOURCE_KEYS & terms:
        categories.add("source")
    if _UNSAFE_CREDENTIAL_KEYS & terms:
        categories.add("credential")
    if _UNSAFE_PROVIDER_LINK_KEYS & terms:
        categories.add("provider_link")
    if _UNSAFE_MARKET_KEYS & terms:
        categories.add("market")
    if _UNSAFE_DECISION_KEYS & terms:
        categories.add("decision")
    if _UNSAFE_FINANCIAL_KEYS & terms:
        categories.add("financial")
    return categories


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


def _nested_text_terms(value: Any) -> set[str]:
    if isinstance(value, str):
        lowered_value = value.lower()
        return {
            term
            for term in _all_unsafe_terms()
            if term in lowered_value
        }
    if isinstance(value, Mapping):
        terms: set[str] = set()
        for nested_value in value.values():
            for nested_term in _nested_text_terms(nested_value):
                terms.add(nested_term)
        return terms
    if isinstance(value, list | tuple | set):
        terms: set[str] = set()
        for item in value:
            for nested_term in _nested_text_terms(item):
                terms.add(nested_term)
        return terms
    return set()


def _all_unsafe_terms() -> frozenset[str]:
    return (
        _UNSAFE_SOURCE_KEYS
        | _UNSAFE_CREDENTIAL_KEYS
        | _UNSAFE_PROVIDER_LINK_KEYS
        | _UNSAFE_MARKET_KEYS
        | _UNSAFE_DECISION_KEYS
        | _UNSAFE_FINANCIAL_KEYS
    )


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


def _is_log_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


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
    "DEFAULT_MONITORING_SOURCE_MODE",
    "DEFAULT_MONITORING_VERSION",
    "KAIROS_DASHBOARD_MVP_MODE",
    "KAIROS_MONITORING_MODE",
    "build_kairos_monitoring_quotas_logs_safe",
]
