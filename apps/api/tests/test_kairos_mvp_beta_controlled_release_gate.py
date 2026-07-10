from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import (
    kairos_mvp_beta_controlled_release_gate as release_module,
)
from app.modules.providers.kairos_mvp_beta_controlled_release_gate import (
    build_kairos_mvp_beta_controlled_release_gate,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "70_MVP_BETA_CONTROLLED_RELEASE_GATE.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "active"
) / "051-phase-51-mvp-beta-controlled-release-gate.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "completed"
) / "051-phase-51-mvp-beta-controlled-release-gate.md"
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "release_version",
    "source_mode",
    "read_only",
    "db_writes",
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
    "controlled_beta_ready",
    "release_status",
    "staging_gate",
    "beta_policy_gate",
    "safety_gate",
    "access_control_gate",
    "operational_gate",
    "blocking_reasons",
}
FORBIDDEN_EXACT_OUTPUT_KEYS = {
    "raw_payload",
    "api_key",
    "auth",
    "secret",
    "token",
    "provider_url",
    "request_url",
    "deploy_url",
    "cloud_token",
    "cloud_secret",
    "production_url",
    "staging_url",
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
    "launched",
    "public_release",
}


def _staging_readiness(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider": "api-football",
        "mode": "kairos_staging_deployment_readiness",
        "readiness_version": "kairos_staging_deployment_readiness_v1",
        "source_mode": "read_only_pre_deployment_checks",
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
        "staging_ready": True,
        "readiness_status": "ready",
        "blocking_reasons": [],
    }
    payload.update(overrides)
    return payload


def _beta_policy(**overrides: object) -> dict[str, object]:
    policy: dict[str, object] = {
        "closed_beta_only": True,
        "public_launch_blocked": True,
        "max_beta_users_defined": True,
        "usage_limits_defined": True,
        "manual_approval_required": True,
    }
    policy.update(overrides)
    return policy


def _safety_notices(**overrides: object) -> dict[str, object]:
    notices: dict[str, object] = {
        "not_probability_notice_ready": True,
        "not_betting_advice_notice_ready": True,
        "no_guarantee_notice_ready": True,
        "responsible_use_notice_ready": True,
    }
    notices.update(overrides)
    return notices


def _access_control(**overrides: object) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "invite_only": True,
        "admin_review_required": True,
        "public_signup_disabled": True,
        "real_betting_disabled": True,
    }
    snapshot.update(overrides)
    return snapshot


def _operational_runbook(**overrides: object) -> dict[str, object]:
    runbook: dict[str, object] = {
        "release_notes_ready": True,
        "rollback_plan_ready": True,
        "support_contact_ready": True,
        "incident_response_ready": True,
    }
    runbook.update(overrides)
    return runbook


def _safe_kwargs() -> dict[str, dict[str, object]]:
    return {
        "staging_readiness": _staging_readiness(),
        "beta_policy": _beta_policy(),
        "safety_notices": _safety_notices(),
        "access_control_snapshot": _access_control(),
        "operational_runbook": _operational_runbook(),
    }


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
    expected_reason: str,
    **overrides: dict[str, object],
) -> dict[str, object]:
    kwargs = _safe_kwargs()
    kwargs.update(overrides)
    result = build_kairos_mvp_beta_controlled_release_gate(**kwargs)

    assert result["controlled_beta_ready"] is False
    assert result["release_status"] == "blocked"
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_mvp_beta_release_gate_module_and_function_exist() -> None:
    assert hasattr(release_module, "build_kairos_mvp_beta_controlled_release_gate")
    assert callable(build_kairos_mvp_beta_controlled_release_gate)


def test_kairos_mvp_beta_release_gate_builds_complete_safe_payload() -> None:
    result = build_kairos_mvp_beta_controlled_release_gate(**_safe_kwargs())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_mvp_beta_controlled_release_gate"
    assert result["release_version"] == "kairos_mvp_beta_controlled_release_v1"
    assert result["source_mode"] == "read_only_beta_release_checks"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["api_football_call_created"] is False
    assert result["quota_consumed"] is False
    assert result["env_read"] is False
    assert result["cloud_call_created"] is False
    assert result["deployment_created"] is False
    assert result["persistent_logs_created"] is False
    assert result["job_created"] is False
    assert result["endpoint_created"] is False
    assert result["frontend_created"] is False
    assert result["user_created"] is False
    assert result["email_sent"] is False
    assert result["invitation_sent"] is False
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["probability_created"] is False
    assert result["controlled_beta_ready"] is True
    assert result["release_status"] == "ready_for_manual_approval"
    assert result["staging_gate"] == {
        "present": True,
        "staging_ready": True,
        "readiness_status": "ready",
    }
    assert result["beta_policy_gate"] == {
        "present": True,
        "closed_beta_only": True,
        "public_launch_blocked": True,
        "max_beta_users_defined": True,
        "usage_limits_defined": True,
        "manual_approval_required": True,
    }
    assert result["safety_gate"] == {
        "present": True,
        "not_probability_notice_ready": True,
        "not_betting_advice_notice_ready": True,
        "no_guarantee_notice_ready": True,
        "responsible_use_notice_ready": True,
    }
    assert result["access_control_gate"] == {
        "present": True,
        "invite_only": True,
        "admin_review_required": True,
        "public_signup_disabled": True,
        "real_betting_disabled": True,
    }
    assert result["operational_gate"] == {
        "present": True,
        "release_notes_ready": True,
        "rollback_plan_ready": True,
        "support_contact_ready": True,
        "incident_response_ready": True,
    }
    assert result["blocking_reasons"] == []
    assert "launched" not in result
    assert "public_release" not in result


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"release_version": "   "}, "release_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_empty_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_mvp_beta_controlled_release_gate(
        **_safe_kwargs(),
        **kwargs,
    )

    assert result["controlled_beta_ready"] is False
    assert result["release_status"] == "blocked"
    assert expected_reason in result["blocking_reasons"]


@pytest.mark.parametrize(
    ("missing_key", "expected_reason"),
    [
        ("staging_readiness", "missing_staging_readiness"),
        ("beta_policy", "missing_beta_policy"),
        ("safety_notices", "missing_safety_notices"),
        ("access_control_snapshot", "missing_access_control_snapshot"),
        ("operational_runbook", "missing_operational_runbook"),
    ],
)
def test_kairos_mvp_beta_release_gate_missing_snapshots_return_partial(
    missing_key: str,
    expected_reason: str,
) -> None:
    kwargs = _safe_kwargs()
    kwargs[missing_key] = None

    result = build_kairos_mvp_beta_controlled_release_gate(**kwargs)

    assert result["controlled_beta_ready"] is False
    assert result["release_status"] == "partial"
    assert expected_reason in result["blocking_reasons"]


def test_kairos_mvp_beta_release_gate_blocks_wrong_provider() -> None:
    _assert_blocked(
        "staging_readiness_wrong_provider",
        staging_readiness=_staging_readiness(provider="other-provider"),
    )


@pytest.mark.parametrize(
    ("staging_overrides", "expected_reason"),
    [
        ({"mode": "wrong_mode"}, "staging_readiness_wrong_mode"),
        ({"staging_ready": False}, "staging_not_ready"),
        ({"readiness_status": "blocked"}, "staging_readiness_status_not_ready"),
        ({"blocking_reasons": ["release_blockers_present"]}, "staging_readiness_blocking_reasons_present"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_bad_staging_status(
    staging_overrides: dict[str, object],
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        staging_readiness=_staging_readiness(**staging_overrides),
    )


@pytest.mark.parametrize(
    ("forbidden_key", "expected_reason"),
    [
        ("api_key", "beta_policy_unsafe_credential_material_present"),
        ("auth", "beta_policy_unsafe_credential_material_present"),
        ("secret", "beta_policy_unsafe_credential_material_present"),
        ("token", "beta_policy_unsafe_credential_material_present"),
        ("raw_payload", "staging_readiness_unsafe_source_material_present"),
        ("provider_url", "staging_readiness_unsafe_provider_link_material_present"),
        ("request_url", "staging_readiness_unsafe_provider_link_material_present"),
        ("deploy_url", "operational_runbook_unsafe_runtime_target_material_present"),
        ("cloud_token", "operational_runbook_unsafe_runtime_target_material_present"),
        ("cloud_secret", "operational_runbook_unsafe_runtime_target_material_present"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_secret_source_and_runtime_material(
    forbidden_key: str,
    expected_reason: str,
) -> None:
    if forbidden_key in {"api_key", "auth", "secret", "token"}:
        result = _assert_blocked(
            expected_reason,
            beta_policy=_beta_policy(extra={forbidden_key: "blocked"}),
        )
    elif forbidden_key == "raw_payload":
        result = _assert_blocked(
            expected_reason,
            staging_readiness=_staging_readiness(extra={forbidden_key: "blocked"}),
        )
    elif forbidden_key in {"provider_url", "request_url"}:
        result = _assert_blocked(
            expected_reason,
            staging_readiness=_staging_readiness(extra={forbidden_key: "blocked"}),
        )
    else:
        result = _assert_blocked(
            expected_reason,
            operational_runbook=_operational_runbook(extra={forbidden_key: "blocked"}),
        )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    ("flag_name", "expected_reason"),
    [
        ("api_football_call_created", "staging_readiness_created_api_football_call_flag"),
        ("quota_consumed", "staging_readiness_consumed_quota_flag"),
        ("env_read", "staging_readiness_read_env_flag"),
        ("cloud_call_created", "staging_readiness_created_cloud_call_flag"),
        ("deployment_created", "staging_readiness_created_deployment_flag"),
        ("persistent_logs_created", "staging_readiness_created_persistent_logs_flag"),
        ("job_created", "staging_readiness_created_job_flag"),
        ("endpoint_created", "staging_readiness_created_endpoint_flag"),
        ("frontend_created", "staging_readiness_created_frontend_flag"),
        ("official_prediction_created", "staging_readiness_created_official_prediction_flag"),
        ("prediction_record_created", "staging_readiness_created_prediction_record_flag"),
        ("betting_created", "staging_readiness_created_betting_flag"),
        ("ml_model_used", "staging_readiness_used_ml_model"),
        ("probability_created", "staging_readiness_created_probability_flag"),
        ("user_created", "staging_readiness_created_user_flag"),
        ("email_sent", "staging_readiness_sent_email_flag"),
        ("invitation_sent", "staging_readiness_sent_invitation_flag"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_side_effect_flags(
    flag_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        staging_readiness=_staging_readiness(**{flag_name: True}),
    )


@pytest.mark.parametrize(
    "forbidden_key",
    ["odds", "bookmaker", "stake"],
)
def test_kairos_mvp_beta_release_gate_blocks_market_material(
    forbidden_key: str,
) -> None:
    result = _assert_blocked(
        "access_control_snapshot_unsafe_market_material_present",
        access_control_snapshot=_access_control(extra={forbidden_key: "blocked"}),
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    "forbidden_key",
    [
        "probability",
        "win_probability",
        "final_pick",
        "suggested_bet",
        "bet_signal",
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    result = _assert_blocked(
        "safety_notices_unsafe_decision_material_present",
        safety_notices=_safety_notices(extra={forbidden_key: "blocked"}),
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    "forbidden_key",
    ["roi", "profit", "payout", "bankroll"],
)
def test_kairos_mvp_beta_release_gate_blocks_financial_material(
    forbidden_key: str,
) -> None:
    result = _assert_blocked(
        "operational_runbook_unsafe_financial_material_present",
        operational_runbook=_operational_runbook(extra={forbidden_key: "blocked"}),
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("closed_beta_only", "closed_beta_only_missing"),
        ("public_launch_blocked", "public_launch_not_blocked"),
        ("max_beta_users_defined", "max_beta_users_not_defined"),
        ("usage_limits_defined", "usage_limits_not_defined"),
        ("manual_approval_required", "manual_approval_not_required"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_bad_beta_policy(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        beta_policy=_beta_policy(**{field_name: False}),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("not_probability_notice_ready", "not_probability_notice_not_ready"),
        (
            "not_betting_advice_notice_ready",
            "not_betting_advice_notice_not_ready",
        ),
        ("no_guarantee_notice_ready", "no_guarantee_notice_not_ready"),
        ("responsible_use_notice_ready", "responsible_use_notice_not_ready"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_missing_safety_notice(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        safety_notices=_safety_notices(**{field_name: False}),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("invite_only", "invite_only_not_declared"),
        ("admin_review_required", "admin_review_not_required"),
        ("public_signup_disabled", "public_signup_not_disabled"),
        ("real_betting_disabled", "real_betting_not_disabled"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_bad_access_control(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        access_control_snapshot=_access_control(**{field_name: False}),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("release_notes_ready", "release_notes_not_ready"),
        ("rollback_plan_ready", "rollback_plan_not_ready"),
        ("support_contact_ready", "support_contact_not_ready"),
        ("incident_response_ready", "incident_response_not_ready"),
    ],
)
def test_kairos_mvp_beta_release_gate_blocks_bad_operational_runbook(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        operational_runbook=_operational_runbook(**{field_name: False}),
    )


def test_kairos_mvp_beta_release_gate_output_does_not_echo_forbidden_material() -> None:
    result = build_kairos_mvp_beta_controlled_release_gate(
        staging_readiness=_staging_readiness(
            extra={
                "raw_payload": {"blocked": True},
                "provider_url": "https://blocked.example/provider",
                "request_url": "https://blocked.example/request",
            }
        ),
        beta_policy=_beta_policy(
            extra={
                "api_key": "blocked-api-key",
                "auth": "blocked-auth",
                "secret": "blocked-secret",
                "token": "blocked-token",
            }
        ),
        safety_notices=_safety_notices(
            extra={
                "probability": 0.7,
                "recommended_outcome": "blocked-recommendation",
                "suggested_bet": "blocked-suggested-bet",
                "final_pick": "blocked-final-pick",
                "win_probability": 0.8,
                "bet_signal": "blocked-bet-signal",
            }
        ),
        access_control_snapshot=_access_control(
            extra={
                "odds": {"home": 1.5},
                "bookmaker": "blocked-bookmaker",
                "stake": 100,
            }
        ),
        operational_runbook=_operational_runbook(
            extra={
                "deploy_url": "https://blocked.example/deploy",
                "cloud_token": "blocked-cloud-token",
                "cloud_secret": "blocked-cloud-secret",
                "production_url": "https://blocked.example/prod",
                "staging_url": "https://blocked.example/staging",
                "roi": 0.1,
                "profit": 12,
                "payout": 20,
                "bankroll": 100,
            }
        ),
    )
    serialized_result = json.dumps(result, sort_keys=True)
    output_keys = _all_keys(result)

    assert FORBIDDEN_EXACT_OUTPUT_KEYS.isdisjoint(output_keys)
    assert "blocked-api-key" not in serialized_result
    assert "blocked-auth" not in serialized_result
    assert "blocked-secret" not in serialized_result
    assert "blocked-token" not in serialized_result
    assert "https://blocked.example" not in serialized_result
    assert "blocked-bookmaker" not in serialized_result
    assert "blocked-cloud-token" not in serialized_result
    assert "blocked-cloud-secret" not in serialized_result
    assert "blocked-recommendation" not in serialized_result
    assert "blocked-suggested-bet" not in serialized_result
    assert "blocked-final-pick" not in serialized_result
    assert "blocked-bet-signal" not in serialized_result
    assert "\"raw_payload\"" not in serialized_result
    assert "\"api_key\"" not in serialized_result
    assert "\"auth\"" not in serialized_result
    assert "\"secret\"" not in serialized_result
    assert "\"token\"" not in serialized_result
    assert "\"provider_url\"" not in serialized_result
    assert "\"request_url\"" not in serialized_result
    assert "\"deploy_url\"" not in serialized_result
    assert "\"cloud_token\"" not in serialized_result
    assert "\"cloud_secret\"" not in serialized_result
    assert "\"odds\"" not in serialized_result
    assert "\"bookmaker\"" not in serialized_result
    assert "\"stake\"" not in serialized_result
    assert "\"prediction record\"" not in serialized_result
    assert "\"recommended_outcome\"" not in serialized_result
    assert "\"suggested_bet\"" not in serialized_result
    assert "\"final_pick\"" not in serialized_result
    assert "\"win_probability\"" not in serialized_result
    assert "\"bet_signal\"" not in serialized_result
    assert "\"roi\"" not in serialized_result
    assert "\"profit\"" not in serialized_result
    assert "\"payout\"" not in serialized_result
    assert "\"bankroll\"" not in serialized_result


def test_kairos_mvp_beta_release_gate_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_mvp_beta_controlled_release_gate(**_safe_kwargs())
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


def test_kairos_mvp_beta_release_gate_source_has_no_side_effect_calls() -> None:
    module_source = inspect.getsource(release_module)
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
        "os.environ",
        "dotenv",
        ".env",
        "boto3",
        "paramiko",
        "subprocess",
        "open(",
        "write(",
        "send_email",
        "invite_user",
        "create_user",
    )
    for fragment in forbidden_lower_fragments:
        assert fragment not in module_source_lower


def test_kairos_mvp_beta_release_gate_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 51" in doc_text
    assert "mvp beta controlled release gate only" in doc_lower
    assert "no real beta launch" in doc_lower
    assert "no user creation" in doc_lower
    assert "no invitation/email sent" in doc_lower
    assert "no real deployment" in doc_lower
    assert "no cloud call" in doc_lower
    assert "no real api call" in doc_lower
    assert "no quota consumption" in doc_lower
    assert "no env read" in doc_lower
    assert "no db write" in doc_lower
    assert "no persistent logs" in doc_lower
    assert "no job automatic" in doc_lower
    assert "no public endpoint" in doc_lower
    assert "no frontend" in doc_lower
    assert "no official prediction" in doc_lower
    assert "no prediction record" in doc_lower
    assert "no ml" in doc_lower
    assert "no probability" in doc_lower
    assert "no betting/odds/stake" in doc_lower
    assert "no roi/profit/bankroll" in doc_lower
    assert "ready_for_manual_approval" in doc_lower
    assert "not launched" in doc_lower


def test_kairos_mvp_beta_release_gate_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "70_MVP_BETA_CONTROLLED_RELEASE_GATE.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
