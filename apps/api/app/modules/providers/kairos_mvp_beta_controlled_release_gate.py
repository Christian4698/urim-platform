from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
KAIROS_BETA_RELEASE_GATE_MODE: Final = "kairos_mvp_beta_controlled_release_gate"
KAIROS_STAGING_READINESS_MODE: Final = "kairos_staging_deployment_readiness"
DEFAULT_RELEASE_VERSION: Final = "kairos_mvp_beta_controlled_release_v1"
DEFAULT_RELEASE_SOURCE_MODE: Final = "read_only_beta_release_checks"

_TRUE_SIDE_EFFECT_FLAGS: Final = (
    "api_football_call_created",
    "quota_consumed",
    "env_read",
    "cloud_call_created",
    "deployment_created",
    "persistent_logs_created",
    "job_created",
    "endpoint_created",
    "frontend_created",
    "user_created",
    "email_sent",
    "invitation_sent",
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
_STAGING_STATUSES: Final = frozenset({"unknown", "blocked", "partial", "ready"})


def build_kairos_mvp_beta_controlled_release_gate(
    *,
    staging_readiness: Mapping[str, Any] | None = None,
    beta_policy: Mapping[str, Any] | None = None,
    safety_notices: Mapping[str, Any] | None = None,
    access_control_snapshot: Mapping[str, Any] | None = None,
    operational_runbook: Mapping[str, Any] | None = None,
    release_version: str = DEFAULT_RELEASE_VERSION,
    source_mode: str = DEFAULT_RELEASE_SOURCE_MODE,
) -> dict[str, Any]:
    release_version_value = _safe_text(release_version)
    source_mode_value = _safe_text(source_mode)
    staging_gate = _staging_gate(staging_readiness)
    beta_policy_gate = _beta_policy_gate(beta_policy)
    safety_gate = _safety_gate(safety_notices)
    access_control_gate = _access_control_gate(access_control_snapshot)
    operational_gate = _operational_gate(operational_runbook)
    inputs = {
        "staging_readiness": staging_readiness,
        "beta_policy": beta_policy,
        "safety_notices": safety_notices,
        "access_control_snapshot": access_control_snapshot,
        "operational_runbook": operational_runbook,
    }
    blocking_reasons = _blocking_reasons(
        release_version_present=bool(release_version_value),
        source_mode_present=bool(source_mode_value),
        inputs=inputs,
        staging_gate=staging_gate,
        beta_policy_gate=beta_policy_gate,
        safety_gate=safety_gate,
        access_control_gate=access_control_gate,
        operational_gate=operational_gate,
    )
    release_status = _release_status(blocking_reasons)
    controlled_beta_ready = release_status == "ready_for_manual_approval"

    return {
        "provider": API_FOOTBALL_PROVIDER,
        "mode": KAIROS_BETA_RELEASE_GATE_MODE,
        "release_version": release_version_value,
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
        "user_created": False,
        "email_sent": False,
        "invitation_sent": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "probability_created": False,
        "controlled_beta_ready": controlled_beta_ready,
        "release_status": release_status,
        "staging_gate": staging_gate,
        "beta_policy_gate": beta_policy_gate,
        "safety_gate": safety_gate,
        "access_control_gate": access_control_gate,
        "operational_gate": operational_gate,
        "blocking_reasons": blocking_reasons,
    }


def _staging_gate(staging_readiness: Any) -> dict[str, Any]:
    if not isinstance(staging_readiness, Mapping):
        return {
            "present": False,
            "staging_ready": False,
            "readiness_status": "unknown",
        }

    readiness_status = _safe_text(staging_readiness.get("readiness_status"))
    if readiness_status not in _STAGING_STATUSES:
        readiness_status = "unknown"

    return {
        "present": True,
        "staging_ready": staging_readiness.get("staging_ready") is True,
        "readiness_status": readiness_status,
    }


def _beta_policy_gate(beta_policy: Any) -> dict[str, bool]:
    if not isinstance(beta_policy, Mapping):
        return {
            "present": False,
            "closed_beta_only": False,
            "public_launch_blocked": False,
            "max_beta_users_defined": False,
            "usage_limits_defined": False,
            "manual_approval_required": False,
        }

    return {
        "present": True,
        "closed_beta_only": beta_policy.get("closed_beta_only") is True,
        "public_launch_blocked": beta_policy.get("public_launch_blocked") is True,
        "max_beta_users_defined": (
            beta_policy.get("max_beta_users_defined") is True
        ),
        "usage_limits_defined": beta_policy.get("usage_limits_defined") is True,
        "manual_approval_required": (
            beta_policy.get("manual_approval_required") is True
        ),
    }


def _safety_gate(safety_notices: Any) -> dict[str, bool]:
    if not isinstance(safety_notices, Mapping):
        return {
            "present": False,
            "not_probability_notice_ready": False,
            "not_betting_advice_notice_ready": False,
            "no_guarantee_notice_ready": False,
            "responsible_use_notice_ready": False,
        }

    return {
        "present": True,
        "not_probability_notice_ready": (
            safety_notices.get("not_probability_notice_ready") is True
        ),
        "not_betting_advice_notice_ready": (
            safety_notices.get("not_betting_advice_notice_ready") is True
        ),
        "no_guarantee_notice_ready": (
            safety_notices.get("no_guarantee_notice_ready") is True
        ),
        "responsible_use_notice_ready": (
            safety_notices.get("responsible_use_notice_ready") is True
        ),
    }


def _access_control_gate(access_control_snapshot: Any) -> dict[str, bool]:
    if not isinstance(access_control_snapshot, Mapping):
        return {
            "present": False,
            "invite_only": False,
            "admin_review_required": False,
            "public_signup_disabled": False,
            "real_betting_disabled": False,
        }

    return {
        "present": True,
        "invite_only": access_control_snapshot.get("invite_only") is True,
        "admin_review_required": (
            access_control_snapshot.get("admin_review_required") is True
        ),
        "public_signup_disabled": (
            access_control_snapshot.get("public_signup_disabled") is True
        ),
        "real_betting_disabled": (
            access_control_snapshot.get("real_betting_disabled") is True
        ),
    }


def _operational_gate(operational_runbook: Any) -> dict[str, bool]:
    if not isinstance(operational_runbook, Mapping):
        return {
            "present": False,
            "release_notes_ready": False,
            "rollback_plan_ready": False,
            "support_contact_ready": False,
            "incident_response_ready": False,
        }

    return {
        "present": True,
        "release_notes_ready": (
            operational_runbook.get("release_notes_ready") is True
        ),
        "rollback_plan_ready": (
            operational_runbook.get("rollback_plan_ready") is True
        ),
        "support_contact_ready": (
            operational_runbook.get("support_contact_ready") is True
        ),
        "incident_response_ready": (
            operational_runbook.get("incident_response_ready") is True
        ),
    }


def _blocking_reasons(
    *,
    release_version_present: bool,
    source_mode_present: bool,
    inputs: Mapping[str, Any],
    staging_gate: Mapping[str, Any],
    beta_policy_gate: Mapping[str, bool],
    safety_gate: Mapping[str, bool],
    access_control_gate: Mapping[str, bool],
    operational_gate: Mapping[str, bool],
) -> list[str]:
    reasons: list[str] = []
    if not release_version_present:
        reasons.append("release_version_missing")
    if not source_mode_present:
        reasons.append("source_mode_missing")
    reasons.extend(_input_presence_reasons(inputs))
    reasons.extend(_input_safety_reasons(inputs))
    reasons.extend(_side_effect_reasons(inputs))
    reasons.extend(_staging_reasons(inputs.get("staging_readiness"), staging_gate))
    reasons.extend(_gate_reasons(
        beta_policy_gate,
        safety_gate,
        access_control_gate,
        operational_gate,
    ))
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


def _side_effect_reasons(inputs: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for input_name, value in inputs.items():
        if not isinstance(value, Mapping):
            continue
        true_flags = _nested_true_flags(value)
        for flag_name in _TRUE_SIDE_EFFECT_FLAGS:
            if flag_name in true_flags:
                reasons.append(_side_effect_reason(input_name, flag_name))
    return _dedupe_reasons(reasons)


def _staging_reasons(
    staging_readiness: Any,
    staging_gate: Mapping[str, Any],
) -> list[str]:
    if not isinstance(staging_readiness, Mapping):
        return []

    reasons: list[str] = []
    if staging_readiness.get("provider") != API_FOOTBALL_PROVIDER:
        reasons.append("staging_readiness_wrong_provider")
    if _safe_text(staging_readiness.get("mode")) != KAIROS_STAGING_READINESS_MODE:
        reasons.append("staging_readiness_wrong_mode")
    if staging_gate["staging_ready"] is not True:
        reasons.append("staging_not_ready")
    if staging_gate["readiness_status"] != "ready":
        reasons.append("staging_readiness_status_not_ready")
    if _has_blocking_reasons(staging_readiness.get("blocking_reasons")):
        reasons.append("staging_readiness_blocking_reasons_present")
    return _dedupe_reasons(reasons)


def _gate_reasons(
    beta_policy_gate: Mapping[str, bool],
    safety_gate: Mapping[str, bool],
    access_control_gate: Mapping[str, bool],
    operational_gate: Mapping[str, bool],
) -> list[str]:
    reasons: list[str] = []
    if beta_policy_gate["present"] is True:
        _append_false_gate_reasons(
            reasons,
            beta_policy_gate,
            {
                "closed_beta_only": "closed_beta_only_missing",
                "public_launch_blocked": "public_launch_not_blocked",
                "max_beta_users_defined": "max_beta_users_not_defined",
                "usage_limits_defined": "usage_limits_not_defined",
                "manual_approval_required": "manual_approval_not_required",
            },
        )
    if safety_gate["present"] is True:
        _append_false_gate_reasons(
            reasons,
            safety_gate,
            {
                "not_probability_notice_ready": "not_probability_notice_not_ready",
                "not_betting_advice_notice_ready": (
                    "not_betting_advice_notice_not_ready"
                ),
                "no_guarantee_notice_ready": "no_guarantee_notice_not_ready",
                "responsible_use_notice_ready": "responsible_use_notice_not_ready",
            },
        )
    if access_control_gate["present"] is True:
        _append_false_gate_reasons(
            reasons,
            access_control_gate,
            {
                "invite_only": "invite_only_not_declared",
                "admin_review_required": "admin_review_not_required",
                "public_signup_disabled": "public_signup_not_disabled",
                "real_betting_disabled": "real_betting_not_disabled",
            },
        )
    if operational_gate["present"] is True:
        _append_false_gate_reasons(
            reasons,
            operational_gate,
            {
                "release_notes_ready": "release_notes_not_ready",
                "rollback_plan_ready": "rollback_plan_not_ready",
                "support_contact_ready": "support_contact_not_ready",
                "incident_response_ready": "incident_response_not_ready",
            },
        )
    return reasons


def _append_false_gate_reasons(
    reasons: list[str],
    gate: Mapping[str, bool],
    reason_by_field: Mapping[str, str],
) -> None:
    for field_name, reason in reason_by_field.items():
        if gate[field_name] is not True:
            reasons.append(reason)


def _side_effect_reason(input_name: str, flag_name: str) -> str:
    if flag_name == "api_football_call_created":
        return f"{input_name}_created_api_football_call_flag"
    if flag_name == "quota_consumed":
        return f"{input_name}_consumed_quota_flag"
    if flag_name == "env_read":
        return f"{input_name}_read_env_flag"
    if flag_name == "cloud_call_created":
        return f"{input_name}_created_cloud_call_flag"
    if flag_name == "deployment_created":
        return f"{input_name}_created_deployment_flag"
    if flag_name == "persistent_logs_created":
        return f"{input_name}_created_persistent_logs_flag"
    if flag_name == "job_created":
        return f"{input_name}_created_job_flag"
    if flag_name == "endpoint_created":
        return f"{input_name}_created_endpoint_flag"
    if flag_name == "frontend_created":
        return f"{input_name}_created_frontend_flag"
    if flag_name == "user_created":
        return f"{input_name}_created_user_flag"
    if flag_name == "email_sent":
        return f"{input_name}_sent_email_flag"
    if flag_name == "invitation_sent":
        return f"{input_name}_sent_invitation_flag"
    if flag_name == "official_prediction_created":
        return f"{input_name}_created_official_prediction_flag"
    if flag_name == "prediction_record_created":
        return f"{input_name}_created_prediction_record_flag"
    if flag_name == "betting_created":
        return f"{input_name}_created_betting_flag"
    if flag_name == "ml_model_used":
        return f"{input_name}_used_ml_model"
    return f"{input_name}_created_probability_flag"


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


def _nested_true_flags(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        flags = {
            str(key).strip().lower()
            for key, nested_value in value.items()
            if nested_value is True
        }
        for nested_value in value.values():
            for nested_flag in _nested_true_flags(nested_value):
                flags.add(nested_flag)
        return flags
    if isinstance(value, list | tuple | set):
        flags: set[str] = set()
        for item in value:
            for nested_flag in _nested_true_flags(item):
                flags.add(nested_flag)
        return flags
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


def _release_status(blocking_reasons: list[str]) -> str:
    if not blocking_reasons:
        return "ready_for_manual_approval"
    if all(reason.startswith("missing_") for reason in blocking_reasons):
        return "partial"
    return "blocked"


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


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped_reasons: list[str] = []
    for reason in reasons:
        if reason not in deduped_reasons:
            deduped_reasons.append(reason)
    return deduped_reasons


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "DEFAULT_RELEASE_SOURCE_MODE",
    "DEFAULT_RELEASE_VERSION",
    "KAIROS_BETA_RELEASE_GATE_MODE",
    "KAIROS_STAGING_READINESS_MODE",
    "build_kairos_mvp_beta_controlled_release_gate",
]
