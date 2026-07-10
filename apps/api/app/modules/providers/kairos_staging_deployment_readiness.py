from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_STAGING_READINESS_MODE: Final = "kairos_staging_deployment_readiness"
KAIROS_MONITORING_MODE: Final = "kairos_monitoring_quotas_logs_safe"
DEFAULT_READINESS_VERSION: Final = "kairos_staging_deployment_readiness_v1"
DEFAULT_READINESS_SOURCE_MODE: Final = "read_only_pre_deployment_checks"

_ALLOWED_USAGE_BANDS: Final = frozenset({"safe", "watch"})
_ALL_USAGE_BANDS: Final = frozenset(
    {"unknown", "safe", "watch", "critical", "blocked"}
)
_MONITORING_TRUE_FLAGS: Final = (
    "api_football_call_created",
    "quota_consumed",
    "env_read",
    "cloud_call_created",
    "deployment_created",
    "persistent_logs_created",
    "job_created",
    "endpoint_created",
    "frontend_created",
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
_UNSAFE_RUNTIME_TARGET_KEYS: Final = frozenset(
    {"deploy_url", "cloud_token", "cloud_secret", "production_url", "staging_url"}
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


def build_kairos_staging_deployment_readiness(
    *,
    monitoring_payload: Mapping[str, Any] | None = None,
    quality_gates: Mapping[str, Any] | None = None,
    staging_config_snapshot: Mapping[str, Any] | None = None,
    release_checklist: Mapping[str, Any] | None = None,
    readiness_version: str = DEFAULT_READINESS_VERSION,
    source_mode: str = DEFAULT_READINESS_SOURCE_MODE,
) -> dict[str, Any]:
    readiness_version_value = _safe_text(readiness_version)
    source_mode_value = _safe_text(source_mode)
    monitoring_gate = _monitoring_gate(monitoring_payload)
    quality_gate = _quality_gate(quality_gates)
    staging_config_gate = _staging_config_gate(staging_config_snapshot)
    release_gate = _release_gate(release_checklist)
    inputs = {
        "monitoring_payload": monitoring_payload,
        "quality_gates": quality_gates,
        "staging_config_snapshot": staging_config_snapshot,
        "release_checklist": release_checklist,
    }
    blocking_reasons = _blocking_reasons(
        readiness_version_present=bool(readiness_version_value),
        source_mode_present=bool(source_mode_value),
        inputs=inputs,
        monitoring_gate=monitoring_gate,
        quality_gate=quality_gate,
        staging_config_gate=staging_config_gate,
        release_gate=release_gate,
    )
    readiness_status = _readiness_status(blocking_reasons)
    staging_ready = readiness_status == "ready"

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_STAGING_READINESS_MODE,
        "readiness_version": readiness_version_value,
        "source_mode": source_mode_value,
        "read_only": True,
        "db_writes": False,
        "api_football_call_created": False,
        "quota_consumed": False,
        "env_read": False,
        "cloud_call_created": False,
        "deployment_created": False,
        "persistent_logs_created": False,
        "job_created": False,
        "endpoint_created": False,
        "frontend_created": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "probability_created": False,
        "staging_ready": staging_ready,
        "readiness_status": readiness_status,
        "monitoring_gate": monitoring_gate,
        "quality_gate": quality_gate,
        "staging_config_gate": staging_config_gate,
        "release_gate": release_gate,
        "blocking_reasons": blocking_reasons,
    }


def _monitoring_gate(monitoring_payload: Any) -> dict[str, Any]:
    if not isinstance(monitoring_payload, Mapping):
        return {
            "present": False,
            "monitoring_ready": False,
            "ready_for_staging_checks": False,
            "usage_band": "unknown",
        }

    staging_readiness = monitoring_payload.get("staging_readiness")
    quota_status = monitoring_payload.get("quota_status")
    usage_band = "unknown"
    if isinstance(quota_status, Mapping):
        parsed_usage_band = _safe_text(quota_status.get("usage_band"))
        if parsed_usage_band in _ALL_USAGE_BANDS:
            usage_band = parsed_usage_band

    return {
        "present": True,
        "monitoring_ready": monitoring_payload.get("monitoring_ready") is True,
        "ready_for_staging_checks": _mapping_flag(
            staging_readiness,
            "ready_for_staging_checks",
        ),
        "usage_band": usage_band,
    }


def _quality_gate(quality_gates: Any) -> dict[str, bool]:
    if not isinstance(quality_gates, Mapping):
        return {
            "present": False,
            "ruff_passed": False,
            "pytest_passed": False,
            "diff_check_passed": False,
            "git_status_clean_expected": False,
        }

    return {
        "present": True,
        "ruff_passed": quality_gates.get("ruff_passed") is True,
        "pytest_passed": quality_gates.get("pytest_passed") is True,
        "diff_check_passed": quality_gates.get("diff_check_passed") is True,
        "git_status_clean_expected": (
            quality_gates.get("git_status_clean_expected") is True
        ),
    }


def _staging_config_gate(staging_config_snapshot: Any) -> dict[str, bool]:
    if not isinstance(staging_config_snapshot, Mapping):
        return {
            "present": False,
            "staging_config_declared": False,
            "secrets_configured_outside_repo": False,
            "no_secrets_in_payload": False,
            "manual_review_required": True,
        }

    return {
        "present": True,
        "staging_config_declared": (
            staging_config_snapshot.get("staging_config_declared") is True
        ),
        "secrets_configured_outside_repo": (
            staging_config_snapshot.get("secrets_configured_outside_repo")
            is True
        ),
        "no_secrets_in_payload": (
            staging_config_snapshot.get("no_secrets_in_payload") is True
        ),
        "manual_review_required": (
            staging_config_snapshot.get("manual_review_required") is True
        ),
    }


def _release_gate(release_checklist: Any) -> dict[str, Any]:
    if not isinstance(release_checklist, Mapping):
        return {
            "present": False,
            "release_notes_ready": False,
            "rollback_plan_ready": False,
            "manual_approval_required": True,
            "blockers_count": 0,
        }

    return {
        "present": True,
        "release_notes_ready": (
            release_checklist.get("release_notes_ready") is True
        ),
        "rollback_plan_ready": (
            release_checklist.get("rollback_plan_ready") is True
        ),
        "manual_approval_required": (
            release_checklist.get("manual_approval_required") is True
        ),
        "blockers_count": _safe_count(release_checklist.get("blockers_count")),
    }


def _blocking_reasons(
    *,
    readiness_version_present: bool,
    source_mode_present: bool,
    inputs: Mapping[str, Any],
    monitoring_gate: Mapping[str, Any],
    quality_gate: Mapping[str, bool],
    staging_config_gate: Mapping[str, bool],
    release_gate: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not readiness_version_present:
        reasons.append("readiness_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")

    reasons.extend(_input_presence_reasons(inputs))
    reasons.extend(_input_safety_reasons(inputs))
    reasons.extend(_monitoring_reasons(inputs.get("monitoring_payload")))
    reasons.extend(_gate_reasons(monitoring_gate, quality_gate, staging_config_gate, release_gate))
    return _dedupe_reasons(reasons)


def _input_presence_reasons(inputs: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for input_name, value in inputs.items():
        if value is None:
            reasons.append(f"missing_{input_name}")
        elif not isinstance(value, Mapping):
            reasons.append(f"{input_name}_not_mapping")
    return reasons


def _input_safety_reasons(inputs: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for input_name, value in inputs.items():
        if not isinstance(value, Mapping):
            continue
        _append_unsafe_category_reasons(
            reasons,
            source_name=input_name,
            categories=_unsafe_categories(value),
        )
    return _dedupe_reasons(reasons)


def _monitoring_reasons(monitoring_payload: Any) -> list[str]:
    if not isinstance(monitoring_payload, Mapping):
        return []

    reasons: list[str] = []
    if monitoring_payload.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("monitoring_payload_wrong_provider")
    if _safe_text(monitoring_payload.get("mode")) != KAIROS_MONITORING_MODE:
        reasons.append("monitoring_payload_wrong_mode")
    for flag_name in _MONITORING_TRUE_FLAGS:
        if _is_true(monitoring_payload.get(flag_name)):
            reasons.append(_monitoring_flag_reason(flag_name))
    if _has_blocking_reasons(monitoring_payload.get("blocking_reasons")):
        reasons.append("monitoring_payload_blocking_reasons_present")
    return _dedupe_reasons(reasons)


def _gate_reasons(
    monitoring_gate: Mapping[str, Any],
    quality_gate: Mapping[str, bool],
    staging_config_gate: Mapping[str, bool],
    release_gate: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if monitoring_gate["present"] is True:
        if monitoring_gate["monitoring_ready"] is not True:
            reasons.append("monitoring_not_ready")
        if monitoring_gate["ready_for_staging_checks"] is not True:
            reasons.append("monitoring_staging_checks_not_ready")
        usage_band = monitoring_gate["usage_band"]
        if usage_band not in _ALLOWED_USAGE_BANDS:
            reasons.append(f"usage_band_{usage_band}")

    if quality_gate["present"] is True:
        if quality_gate["ruff_passed"] is not True:
            reasons.append("quality_gate_ruff_failed")
        if quality_gate["pytest_passed"] is not True:
            reasons.append("quality_gate_pytest_failed")
        if quality_gate["diff_check_passed"] is not True:
            reasons.append("quality_gate_diff_check_failed")

    if staging_config_gate["present"] is True:
        if staging_config_gate["staging_config_declared"] is not True:
            reasons.append("staging_config_not_declared")
        if staging_config_gate["secrets_configured_outside_repo"] is not True:
            reasons.append("staging_config_secret_boundary_missing")
        if staging_config_gate["no_secrets_in_payload"] is not True:
            reasons.append("staging_config_payload_secret_guard_missing")

    if release_gate["present"] is True:
        if release_gate["release_notes_ready"] is not True:
            reasons.append("release_notes_not_ready")
        if release_gate["rollback_plan_ready"] is not True:
            reasons.append("rollback_plan_not_ready")
        if release_gate["blockers_count"] > 0:
            reasons.append("release_blockers_present")
    return reasons


def _monitoring_flag_reason(flag_name: str) -> str:
    if flag_name == "api_football_call_created":
        return "monitoring_created_api_football_call_flag"
    if flag_name == "quota_consumed":
        return "monitoring_consumed_quota_flag"
    if flag_name == "env_read":
        return "monitoring_read_env_flag"
    if flag_name == "cloud_call_created":
        return "monitoring_created_cloud_call_flag"
    if flag_name == "deployment_created":
        return "monitoring_created_deployment_flag"
    if flag_name == "persistent_logs_created":
        return "monitoring_created_persistent_logs_flag"
    if flag_name == "job_created":
        return "monitoring_created_job_flag"
    if flag_name == "endpoint_created":
        return "monitoring_created_endpoint_flag"
    if flag_name == "frontend_created":
        return "monitoring_created_frontend_flag"
    if flag_name == "official_prediction_created":
        return "monitoring_created_official_prediction_flag"
    if flag_name == "prediction_record_created":
        return "monitoring_created_prediction_record_flag"
    if flag_name == "betting_created":
        return "monitoring_created_betting_flag"
    if flag_name == "ml_model_used":
        return "monitoring_used_ml_model"
    return "monitoring_created_probability_flag"


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
    if "runtime_target" in categories:
        reasons.append(f"{source_name}_unsafe_runtime_target_material_present")
    if "market" in categories:
        reasons.append(f"{source_name}_unsafe_market_material_present")
    if "decision" in categories:
        reasons.append(f"{source_name}_unsafe_decision_material_present")
    if "financial" in categories:
        reasons.append(f"{source_name}_unsafe_financial_material_present")


def _unsafe_categories(value: Any) -> set[str]:
    terms = _nested_keys(value) | _nested_text_terms(value)
    categories: set[str] = set()
    if _UNSAFE_SOURCE_KEYS & terms:
        categories.add("source")
    if _UNSAFE_CREDENTIAL_KEYS & terms:
        categories.add("credential")
    if _UNSAFE_PROVIDER_LINK_KEYS & terms:
        categories.add("provider_link")
    if _UNSAFE_RUNTIME_TARGET_KEYS & terms:
        categories.add("runtime_target")
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
        | _UNSAFE_RUNTIME_TARGET_KEYS
        | _UNSAFE_MARKET_KEYS
        | _UNSAFE_DECISION_KEYS
        | _UNSAFE_FINANCIAL_KEYS
    )


def _readiness_status(blocking_reasons: list[str]) -> str:
    if not blocking_reasons:
        return "ready"
    if all(reason.startswith("missing_") for reason in blocking_reasons):
        return "partial"
    return "blocked"


def _mapping_flag(value: Any, field_name: str) -> bool:
    if not isinstance(value, Mapping):
        return False
    return value.get(field_name) is True


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


def _safe_count(value: Any) -> int:
    parsed_value = _non_negative_int_like(value)
    return parsed_value if parsed_value is not None else 0


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
    "DEFAULT_READINESS_SOURCE_MODE",
    "DEFAULT_READINESS_VERSION",
    "KAIROS_MONITORING_MODE",
    "KAIROS_STAGING_READINESS_MODE",
    "build_kairos_staging_deployment_readiness",
]
