from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from app.modules.providers import kairos_monitoring_quotas_logs_safe as monitoring_module
from app.modules.providers.kairos_monitoring_quotas_logs_safe import (
    build_kairos_monitoring_quotas_logs_safe,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "68_MONITORING_QUOTAS_LOGS_SAFE.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.md"
ACTIVE_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "active"
) / "049-phase-49-monitoring-quotas-logs-safe.md"
COMPLETED_PLAN_PATH = (
    REPO_ROOT / "docs" / "exec-plans" / "completed"
) / "049-phase-49-monitoring-quotas-logs-safe.md"
EXPECTED_OUTPUT_KEYS = {
    "provider",
    "mode",
    "monitoring_version",
    "source_mode",
    "read_only",
    "db_writes",
    "api_football_call_created",
    "quota_consumed",
    "persistent_logs_created",
    "job_created",
    "endpoint_created",
    "official_prediction_created",
    "prediction_record_created",
    "betting_created",
    "ml_model_used",
    "probability_created",
    "monitoring_ready",
    "quota_status",
    "logs_safety",
    "dashboard_status",
    "staging_readiness",
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


def _dashboard_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "provider": "api-football",
        "mode": "kairos_dashboard_mvp_read_only",
        "dashboard_version": "kairos_dashboard_mvp_v1",
        "source_mode": "read_only_aggregate",
        "read_only": True,
        "db_writes": False,
        "api_football_call_created": False,
        "ingestion_created": False,
        "official_prediction_created": False,
        "prediction_record_created": False,
        "betting_created": False,
        "ml_model_used": False,
        "probability_created": False,
        "dashboard_ready": True,
        "summary": {
            "overall_status": "ready",
            "confidence_band": "medium",
            "confidence_score_type": "technical_signal_quality",
            "not_probability": True,
            "not_for_betting": True,
            "not_a_guarantee": True,
        },
        "blocking_reasons": [],
    }
    payload.update(overrides)
    return payload


def _quota_snapshot(**overrides: object) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "provider": "api-football",
        "provider_plan": "free",
        "daily_limit": 100,
        "daily_used": 40,
    }
    snapshot.update(overrides)
    return snapshot


def _log_events() -> list[dict[str, object]]:
    return [
        {
            "event_type": "dashboard_check",
            "severity": "info",
            "safe_message": "dashboard payload inspected in memory",
        }
    ]


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
    *,
    dashboard_payload: dict[str, object] | None = None,
    quota_snapshot: dict[str, object] | None = None,
    log_events: list[dict[str, object]] | None = None,
    expected_reason: str,
) -> dict[str, object]:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=(
            _dashboard_payload()
            if dashboard_payload is None
            else dashboard_payload
        ),
        quota_snapshot=(
            _quota_snapshot()
            if quota_snapshot is None
            else quota_snapshot
        ),
        log_events=_log_events() if log_events is None else log_events,
    )

    assert result["monitoring_ready"] is False
    assert expected_reason in result["blocking_reasons"]
    assert result["staging_readiness"]["ready_for_staging_checks"] is False
    return result


def test_kairos_monitoring_module_and_function_exist() -> None:
    assert hasattr(monitoring_module, "build_kairos_monitoring_quotas_logs_safe")
    assert callable(build_kairos_monitoring_quotas_logs_safe)


def test_kairos_monitoring_builds_complete_safe_payload() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(),
        log_events=_log_events(),
    )

    assert set(result) == EXPECTED_OUTPUT_KEYS
    assert result["provider"] == "api-football"
    assert result["mode"] == "kairos_monitoring_quotas_logs_safe"
    assert result["monitoring_version"] == "kairos_monitoring_quotas_logs_safe_v1"
    assert result["source_mode"] == "read_only_in_memory_snapshots"
    assert result["read_only"] is True
    assert result["db_writes"] is False
    assert result["api_football_call_created"] is False
    assert result["quota_consumed"] is False
    assert result["persistent_logs_created"] is False
    assert result["job_created"] is False
    assert result["endpoint_created"] is False
    assert result["official_prediction_created"] is False
    assert result["prediction_record_created"] is False
    assert result["betting_created"] is False
    assert result["ml_model_used"] is False
    assert result["probability_created"] is False
    assert result["monitoring_ready"] is True
    assert result["quota_status"] == {
        "snapshot_present": True,
        "provider_plan": "free",
        "daily_limit": 100,
        "daily_used": 40,
        "daily_remaining": 60,
        "usage_band": "safe",
    }
    assert result["logs_safety"] == {
        "events_count": 1,
        "safe_events_count": 1,
        "blocked_events_count": 0,
        "redaction_required": False,
        "contains_secret": False,
        "contains_raw_payload": False,
    }
    assert result["dashboard_status"] == {
        "dashboard_payload_present": True,
        "dashboard_ready": True,
        "overall_status": "ready",
    }
    assert result["staging_readiness"] == {
        "ready_for_staging_checks": True,
        "requires_manual_review": False,
    }
    assert result["blocking_reasons"] == []


@pytest.mark.parametrize(
    ("kwargs", "expected_reason"),
    [
        ({"monitoring_version": "   "}, "monitoring_version_missing"),
        ({"source_mode": "   "}, "source_mode_missing"),
    ],
)
def test_kairos_monitoring_blocks_missing_metadata(
    kwargs: dict[str, str],
    expected_reason: str,
) -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(),
        log_events=_log_events(),
        **kwargs,
    )

    assert result["monitoring_ready"] is False
    assert expected_reason in result["blocking_reasons"]


def test_kairos_monitoring_dashboard_payload_absent_is_not_ready() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=None,
        quota_snapshot=_quota_snapshot(),
        log_events=_log_events(),
    )

    assert result["monitoring_ready"] is False
    assert result["dashboard_status"] == {
        "dashboard_payload_present": False,
        "dashboard_ready": False,
        "overall_status": "unknown",
    }
    assert "dashboard_payload_missing" in result["blocking_reasons"]


def test_kairos_monitoring_quota_snapshot_absent_is_unknown() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=None,
        log_events=_log_events(),
    )

    assert result["monitoring_ready"] is False
    assert result["quota_status"]["snapshot_present"] is False
    assert result["quota_status"]["usage_band"] == "unknown"
    assert "quota_snapshot_missing" in result["blocking_reasons"]


def test_kairos_monitoring_log_events_absent_returns_zero_counts() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(),
        log_events=None,
    )

    assert result["monitoring_ready"] is True
    assert result["logs_safety"] == {
        "events_count": 0,
        "safe_events_count": 0,
        "blocked_events_count": 0,
        "redaction_required": False,
        "contains_secret": False,
        "contains_raw_payload": False,
    }


@pytest.mark.parametrize(
    ("dashboard_provider", "quota_provider", "expected_reason"),
    [
        ("other-provider", "api-football", "dashboard_payload_wrong_provider"),
        ("api-football", "other-provider", "quota_snapshot_wrong_provider"),
    ],
)
def test_kairos_monitoring_blocks_wrong_provider(
    dashboard_provider: str,
    quota_provider: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        dashboard_payload=_dashboard_payload(provider=dashboard_provider),
        quota_snapshot=_quota_snapshot(provider=quota_provider),
        expected_reason=expected_reason,
    )


@pytest.mark.parametrize(
    "forbidden_key",
    ["api_key", "auth", "secret", "token"],
)
def test_kairos_monitoring_blocks_credentials(forbidden_key: str) -> None:
    result = _assert_blocked(
        log_events=[{"message": "redaction needed", forbidden_key: "blocked"}],
        expected_reason="log_events_unsafe_credential_material_present",
    )

    assert result["logs_safety"]["contains_secret"] is True
    assert result["logs_safety"]["redaction_required"] is True


def test_kairos_monitoring_blocks_raw_payload() -> None:
    result = _assert_blocked(
        log_events=[{"raw_payload": {"blocked": True}}],
        expected_reason="log_events_unsafe_source_material_present",
    )

    assert result["logs_safety"]["contains_raw_payload"] is True
    assert result["logs_safety"]["blocked_events_count"] == 1


@pytest.mark.parametrize(
    "forbidden_key",
    ["provider_url", "request_url"],
)
def test_kairos_monitoring_blocks_provider_links(forbidden_key: str) -> None:
    _assert_blocked(
        quota_snapshot=_quota_snapshot(extra={"nested": {forbidden_key: "blocked"}}),
        expected_reason="quota_snapshot_unsafe_provider_link_material_present",
    )


@pytest.mark.parametrize(
    ("flag_name", "expected_reason"),
    [
        ("official_prediction_created", "created_official_prediction_flag"),
        ("prediction_record_created", "created_prediction_record_flag"),
        ("betting_created", "created_betting_flag"),
        ("ml_model_used", "used_ml_model"),
        ("probability_created", "created_probability_flag"),
    ],
)
def test_kairos_monitoring_blocks_dashboard_flags(
    flag_name: str,
    expected_reason: str,
) -> None:
    _assert_blocked(
        dashboard_payload=_dashboard_payload(**{flag_name: True}),
        expected_reason=f"dashboard_payload_{expected_reason}",
    )


@pytest.mark.parametrize(
    "forbidden_key",
    ["odds", "bookmaker", "stake"],
)
def test_kairos_monitoring_blocks_market_material(forbidden_key: str) -> None:
    result = _assert_blocked(
        dashboard_payload=_dashboard_payload(
            extra={"nested": {forbidden_key: "blocked"}}
        ),
        expected_reason="dashboard_payload_unsafe_market_material_present",
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
def test_kairos_monitoring_blocks_predictive_material(forbidden_key: str) -> None:
    result = _assert_blocked(
        dashboard_payload=_dashboard_payload(
            extra={"nested": {forbidden_key: "blocked"}}
        ),
        expected_reason="dashboard_payload_unsafe_decision_material_present",
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    "forbidden_key",
    ["roi", "profit", "payout", "bankroll"],
)
def test_kairos_monitoring_blocks_financial_material(forbidden_key: str) -> None:
    result = _assert_blocked(
        quota_snapshot=_quota_snapshot(extra={"nested": {forbidden_key: "blocked"}}),
        expected_reason="quota_snapshot_unsafe_financial_material_present",
    )

    assert forbidden_key not in _all_keys(result)


@pytest.mark.parametrize(
    ("daily_used", "expected_band"),
    [
        (60, "safe"),
        (61, "watch"),
        (85, "watch"),
        (86, "critical"),
        (100, "blocked"),
        (120, "blocked"),
    ],
)
def test_kairos_monitoring_usage_bands(
    daily_used: int,
    expected_band: str,
) -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(daily_limit=100, daily_used=daily_used),
        log_events=_log_events(),
    )

    assert result["quota_status"]["usage_band"] == expected_band
    assert result["monitoring_ready"] is (expected_band in {"safe", "watch"})


def test_kairos_monitoring_unknown_usage_band_for_missing_or_non_numeric_counts() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(daily_limit="not-numeric", daily_used=10),
        log_events=_log_events(),
    )

    assert result["quota_status"]["usage_band"] == "unknown"
    assert result["monitoring_ready"] is False
    assert "quota_usage_unknown" in result["blocking_reasons"]


def test_kairos_monitoring_staging_readiness_requires_safe_conditions() -> None:
    safe_result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(daily_used=60),
        log_events=_log_events(),
    )
    critical_result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(daily_used=86),
        log_events=_log_events(),
    )
    blocked_dashboard_result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(
            dashboard_ready=False,
            summary={"overall_status": "blocked"},
        ),
        quota_snapshot=_quota_snapshot(daily_used=60),
        log_events=_log_events(),
    )
    redaction_result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(daily_used=60),
        log_events=[{"secret": "blocked"}],
    )

    assert safe_result["staging_readiness"]["ready_for_staging_checks"] is True
    assert critical_result["staging_readiness"]["ready_for_staging_checks"] is False
    assert (
        blocked_dashboard_result["staging_readiness"]["ready_for_staging_checks"]
        is False
    )
    assert redaction_result["staging_readiness"]["ready_for_staging_checks"] is False


def test_kairos_monitoring_output_does_not_echo_forbidden_material() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(
            extra={
                "api_key": "blocked-api-key",
                "auth": "blocked-auth",
                "token": "blocked-token",
                "provider_url": "https://blocked.example",
                "request_url": "https://blocked.example/request",
                "odds": {"home": 1.5},
                "bookmaker": "blocked-bookmaker",
                "stake": 100,
                "probability": 0.7,
                "recommended_outcome": "blocked-recommendation",
                "suggested_bet": "blocked-suggested-bet",
                "final_pick": "blocked-final-pick",
                "win_probability": 0.8,
                "bet_signal": "blocked-bet-signal",
            }
        ),
        quota_snapshot=_quota_snapshot(
            extra={
                "raw_payload": {"blocked": True},
                "roi": 0.1,
                "profit": 12,
                "payout": 20,
                "bankroll": 100,
            }
        ),
        log_events=[{"safe_message": "monitoring event"}],
    )
    serialized_result = json.dumps(result, sort_keys=True)
    output_keys = _all_keys(result)

    assert FORBIDDEN_EXACT_OUTPUT_KEYS.isdisjoint(output_keys)
    assert "blocked-api-key" not in serialized_result
    assert "blocked-auth" not in serialized_result
    assert "blocked-token" not in serialized_result
    assert "https://blocked.example" not in serialized_result
    assert "blocked-bookmaker" not in serialized_result
    assert "blocked-recommendation" not in serialized_result
    assert "blocked-suggested-bet" not in serialized_result
    assert "blocked-final-pick" not in serialized_result
    assert "blocked-bet-signal" not in serialized_result
    assert "\"api_key\"" not in serialized_result
    assert "\"auth\"" not in serialized_result
    assert "\"token\"" not in serialized_result
    assert "\"provider_url\"" not in serialized_result
    assert "\"request_url\"" not in serialized_result
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


def test_kairos_monitoring_runtime_text_avoids_betting_claims() -> None:
    result = build_kairos_monitoring_quotas_logs_safe(
        dashboard_payload=_dashboard_payload(),
        quota_snapshot=_quota_snapshot(),
        log_events=_log_events(),
    )
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


def test_kairos_monitoring_source_has_no_writes_or_provider_calls() -> None:
    module_source = inspect.getsource(monitoring_module)
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
    )
    for fragment in forbidden_lower_fragments:
        assert fragment not in module_source_lower


def test_kairos_monitoring_doc_exists_and_documents_scope() -> None:
    doc_text = DOC_PATH.read_text(encoding="utf-8")
    doc_lower = doc_text.lower()

    assert "Phase 49" in doc_text
    assert "monitoring/quotas/logs safe only" in doc_lower
    assert "no real api call" in doc_lower
    assert "no quota consumption" in doc_lower
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
    assert "phase 50" in doc_lower
    assert "staging deployment readiness" in doc_lower


def test_kairos_monitoring_doc_index_and_plan_state() -> None:
    index_text = INDEX_PATH.read_text(encoding="utf-8")

    assert "68_MONITORING_QUOTAS_LOGS_SAFE.md" in index_text
    assert COMPLETED_PLAN_PATH.exists()
    assert not ACTIVE_PLAN_PATH.exists()
