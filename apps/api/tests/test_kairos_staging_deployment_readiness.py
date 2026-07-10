from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import (
    kairos_staging_deployment_readiness as readiness_module,
)
from app.modules.providers.kairos_staging_deployment_readiness import (
    build_kairos_staging_deployment_readiness,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "69_STAGING_DEPLOYMENT_READINESS.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "active"
) / "050-phase-50-staging-deployment-readiness.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "completed"
) / "050-phase-50-staging-deployment-readiness.md"
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "readiness_version",
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
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "probability_created",
    "staging_ready",
    "readiness_status",
    "monitoring_gate",
    "quality_gate",
    "staging_config_gate",
    "release_gate",
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
}


def _monitoring_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider": "api-football",
        "mode": "kairos_monitoring_quotas_logs_safe",
        "monitoring_version": "kairos_monitoring_quotas_logs_safe_v1",
        "source_mode": "read_only_in_memory_snapshots",
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
        "monitoring_ready": True,
        "quota_status": {"usage_band": "safe"},
        "logs_safety": {
            "redaction_required": False,
            "contains_secret": False,
            "contains_raw_payload": False,
        },
        "dashboard_status": {
            "dashboard_payload_present": True,
            "dashboard_ready": True,
            "overall_status": "ready",
        },
        "staging_readiness": {
            "ready_for_staging_checks": True,
            "requires_manual_review": False,
        },
        "blocking_reasons": [],
    }
    payload.update(overrides)
    return payload


def _quality_gates(**overrides: object) -> dict[str, object]:
    gates: dict[str, object] = {
        "ruff_passed": True,
        "pytest_passed": True,
        "diff_check_passed": True,
        "git_status_clean_expected": False,
    }
    gates.update(overrides)
    return gates


def _staging_config(**overrides: object) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "staging_config_declared": True,
        "secrets_configured_outside_repo": True,
        "no_secrets_in_payload": True,
        "manual_review_required": False,
    }
    snapshot.update(overrides)
    return snapshot


def _release_checklist(**overrides: object) -> dict[str, object]:
    checklist: dict[str, object] = {
        "release_notes_ready": True,
        "rollback_plan_ready": True,
        "manual_approval_required": True,
        "blockers_count": 0,
    }
    checklist.update(overrides)
    return checklist


def _safe_kwargs() -> dict[str, dict[str, object]]:
    return {
        "monitoring_payload": _monitoring_payload(),
        "quality_gates": _quality_gates(),
        "staging_config_snapshot": _staging_config(),
        "release_checklist": _release_checklist(),
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
    result = build_kairos_staging_deployment_readiness(**kwargs)

    assert result["staging_ready"] is False
    assert result["readiness_status"] == "blocked"
    assert expected_reason in result["blocking_reasons"]
    return result


def test_kairos_staging_readiness_module_and_function_exist() -> None:
    assert hasattr(readiness_module, "build_kairos_staging_deployment_readiness")
    assert callable(build_kairos_staging_deployment_readiness)


def test_kairos_staging_readiness_builds_complete_safe_payload() -> None:
    result = build_kairos_staging_deployment_readiness(**_safe_kwargs())

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_staging_deployment_readiness"
    assert result["readiness_version"] == "kairos_staging_deployment_readiness_v1"
    assert result["source_mode"] == "read_only_pre_deployment_checks"
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
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["probability_created"] is False
    assert result["staging_ready"] is True
    assert result["readiness_status"] == "ready"
    assert result["monitoring_gate"] == {
        "present": True,
        "monitoring_ready": True,
        "ready_for_staging_checks": True,
        "usage_band": "safe",
    }
    assert result["quality_gate"] == {
        "present": True,
        "ruff_passed": True,
        "pytest_passed": True,
        "diff_check_passed": True,
        "git_status_clean_expected": False,
    }
    assert result["staging_config_gate"] == {
        "present": True,
        "staging_config_declared": True,
        "secrets_configured_outside_repo": True,
        "no_secrets_in_payload": True,
        "manual_review_required": False,
    }
    assert result["release_gate"] == {
        "present": True,
        "release_notes_ready": True,
        "rollback_plan_ready": True,
        "manual_approval_required": True,
        "blockers_count": 0,
    }
    assert result["blocking_reasons"] == []


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"readiness_version": "   "}, "readiness_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_staging_readiness_blocks_empty_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_staging_deployment_readiness(
        **_safe_kwargs(),
        **kwargs,
    )

    assert result["staging_ready"] is False
    assert result["readiness_status"] == "blocked"
    assert expected_reason in result["blocking_reasons"]


@pytest.mark.parametrize(
    ("missing_key", "expected_reason"),
    [
        ("monitoring_payload", "missing_monitoring_payload"),
        ("quality_gates", "missing_quality_gates"),
        ("staging_config_snapshot", "missing_staging_config_snapshot"),
        ("release_checklist", "missing_release_checklist"),
    ],
)
def test_kairos_staging_readiness_missing_snapshots_return_partial(
    missing_key: str,
    expected_reason: str,
) -> None:
    kwargs = _safe_kwargs()
    kwargs[missing_key] = None

    result = build_kairos_staging_deployment_readiness(**kwargs)

    assert result["staging_ready"] is False
    assert result["readiness_status"] == "partial"
    assert expected_reason in result["blocking_reasons"]


def test_kairos_staging_readiness_blocks_wrong_provider() -> None:
    _assert_blocked(
        "monitoring_payload_wrong_provider",
        monitoring_payload=_monitoring_payload(provider="other-provider"),
    )


@pytest.mark.parametrize(
    ("forbidden_key", "expected_reason"),
    [
        ("api_key", "quality_gates_unsafe_credential_material_present"),
        ("auth", "quality_gates_unsafe_credential_material_present"),
        ("secret", "quality_gates_unsafe_credential_material_present"),
        ("token", "quality_gates_unsafe_credential_material_present"),
        ("raw_payload", "monitoring_payload_unsafe_source_material_present"),
        ("provider_url", "monitoring_payload_unsafe_provider_link_material_present"),
        ("request_url", "monitoring_payload_unsafe_provider_link_material_present"),
        ("deploy_url", "release_checklist_unsafe_runtime_target_material_present"),
        ("cloud_token", "release_checklist_unsafe_runtime_target_material_present"),
        ("cloud_secret", "release_checklist_unsafe_runtime_target_material_present"),
    ],
)
def test_kairos_staging_readiness_blocks_secret_source_and_runtime_material(
    forbidden_key: str,
    expected_reason: str,
) -> None:
    if forbidden_key in {"api_key", "auth", "secret", "token"}:
        result = _assert_blocked(
            expected_reason,
            quality_gates=_quality_gates(extra={forbidden_key: "blocked"}),
        )
    elif forbidden_key == "raw_payload":
        result = _assert_blocked(
            expected_reason,
            monitoring_payload=_monitoring_payload(extra={forbidden_key: "blocked"}),
        )
    elif forbidden_key in {"provider_url", "request_url"}:
        result = _assert_blocked(
            expected_reason,
            monitoring_payload=_monitoring_payload(extra={forbidden_key: "blocked"}),
        )
    else:
        result = _assert_blocked(
            expected_reason,
            release_checklist=_release_checklist(extra={forbidden_key: "blocked"}),
        )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    ("flag_name", "expected_reason"),
    [
        ("api_football_call_created", "monitoring_created_api_football_call_flag"),
        ("quota_consumed", "monitoring_consumed_quota_flag"),
        ("persistent_logs_created", "monitoring_created_persistent_logs_flag"),
        ("job_created", "monitoring_created_job_flag"),
        ("endpoint_created", "monitoring_created_endpoint_flag"),
        ("official_prediction_created", "monitoring_created_official_prediction_flag"),
        ("prediction_record_created", "monitoring_created_prediction_record_flag"),
        ("betting_created", "monitoring_created_betting_flag"),
        ("ml_model_used", "monitoring_used_ml_model"),
        ("probability_created", "monitoring_created_probability_flag"),
    ],
)
def test_kairos_staging_readiness_blocks_monitoring_side_effect_flags(
    flag_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        monitoring_payload=_monitoring_payload(**{flag_name: True}),
    )


@pytest.mark.parametrize(
    "forbidden_key",
    ["odds", "bookmaker", "stake"],
)
def test_kairos_staging_readiness_blocks_market_material(forbidden_key: str) -> None:
    result = _assert_blocked(
        "staging_config_snapshot_unsafe_market_material_present",
        staging_config_snapshot=_staging_config(extra={forbidden_key: "blocked"}),
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
def test_kairos_staging_readiness_blocks_predictive_material(
    forbidden_key: str,
) -> None:
    result = _assert_blocked(
        "release_checklist_unsafe_decision_material_present",
        release_checklist=_release_checklist(extra={forbidden_key: "blocked"}),
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    "forbidden_key",
    ["roi", "profit", "payout", "bankroll"],
)
def test_kairos_staging_readiness_blocks_financial_material(
    forbidden_key: str,
) -> None:
    result = _assert_blocked(
        "quality_gates_unsafe_financial_material_present",
        quality_gates=_quality_gates(extra={forbidden_key: "blocked"}),
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    ("usage_band", "expected_reason"),
    [
        ("critical", "usage_band_critical"),
        ("blocked", "usage_band_blocked"),
    ],
)
def test_kairos_staging_readiness_blocks_bad_usage_bands(
    usage_band: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        monitoring_payload=_monitoring_payload(
            quota_status={"usage_band": usage_band}
        ),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("ruff_passed", "quality_gate_ruff_failed"),
        ("pytest_passed", "quality_gate_pytest_failed"),
        ("diff_check_passed", "quality_gate_diff_check_failed"),
    ],
)
def test_kairos_staging_readiness_blocks_failed_quality_gates(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        quality_gates=_quality_gates(**{field_name: False}),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("staging_config_declared", "staging_config_not_declared"),
        ("secrets_configured_outside_repo", "staging_config_secret_boundary_missing"),
        ("no_secrets_in_payload", "staging_config_payload_secret_guard_missing"),
    ],
)
def test_kairos_staging_readiness_blocks_incomplete_staging_config(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        staging_config_snapshot=_staging_config(**{field_name: False}),
    )


@pytest.mark.parametrize(
    ("field_name", "expected_reason"),
    [
        ("release_notes_ready", "release_notes_not_ready"),
        ("rollback_plan_ready", "rollback_plan_not_ready"),
    ],
)
def test_kairos_staging_readiness_blocks_incomplete_release_checklist(
    field_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        expected_reason,
        release_checklist=_release_checklist(**{field_name: False}),
    )


def test_kairos_staging_readiness_blocks_release_blockers() -> None:
    result = _assert_blocked(
        "release_blockers_present",
        release_checklist=_release_checklist(blockers_count=2),
    )

    assert result["release_gate"]["blockers_count"] == 2


def test_kairos_staging_readiness_manual_approval_is_informational() -> None:
    result = build_kairos_staging_deployment_readiness(
        **{
            **_safe_kwargs(),
            "release_checklist": _release_checklist(manual_approval_required=True),
        }
    )

    assert result["staging_ready"] is True
    assert result["readiness_status"] == "ready"
    assert result["release_gate"]["manual_approval_required"] is True


def test_kairos_staging_readiness_output_does_not_echo_forbidden_material() -> None:
    result = build_kairos_staging_deployment_readiness(
        monitoring_payload=_monitoring_payload(
            extra={
                "raw_payload": {"blocked": True},
                "provider_url": "https://blocked.example/provider",
                "request_url": "https://blocked.example/request",
                "odds": {"home": 1.5},
                "bookmaker": "blocked-bookmaker",
                "stake": 100,
            }
        ),
        quality_gates=_quality_gates(
            extra={
                "api_key": "blocked-api-key",
                "auth": "blocked-auth",
                "secret": "blocked-secret",
                "token": "blocked-token",
                "roi": 0.1,
                "profit": 12,
                "payout": 20,
                "bankroll": 100,
            }
        ),
        staging_config_snapshot=_staging_config(
            extra={
                "deploy_url": "https://blocked.example/deploy",
                "cloud_token": "blocked-cloud-token",
                "cloud_secret": "blocked-cloud-secret",
                "production_url": "https://blocked.example/prod",
                "staging_url": "https://blocked.example/staging",
            }
        ),
        release_checklist=_release_checklist(
            extra={
                "probability": 0.7,
                "recommended_outcome": "blocked-recommendation",
                "suggested_bet": "blocked-suggested-bet",
                "final_pick": "blocked-final-pick",
                "win_probability": 0.8,
                "bet_signal": "blocked-bet-signal",
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


def test_kairos_staging_readiness_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_staging_deployment_readiness(**_safe_kwargs())
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


def test_kairos_staging_readiness_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(readiness_module)
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
    )
    for fragment in forbidden_lower_fragments:
        assert fragment not in module_source_lower


def test_kairos_staging_readiness_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 50" in doc_text
    assert "staging deployment readiness only" in doc_lower
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
    assert "phase 51" in doc_lower
    assert "mvp beta controlled release gate" in doc_lower


def test_kairos_staging_readiness_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "69_STAGING_DEPLOYMENT_READINESS.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
