from datetime import UTC, datetime

import pytest

from app.cli.daily_operations import (
    DailyOperationsUnavailable,
    OperationMetrics,
    _record_success,
    _safe_step_metrics,
    _sanitize_saved_status,
)
from app.modules.sports_data.discovery import (
    build_discovery_plan,
    build_retention_funnel,
)
from app.modules.sports_data.normalization import NormalizationResult
from app.modules.sports_data.sync import _deduplicate_fixture_rows


def test_retention_funnel_explains_all_145_rejected_fixtures() -> None:
    funnel = build_retention_funnel(
        fixtures_received=145,
        retained=0,
        ignored_reasons={
            "competition_type_unsupported": 80,
            "competition_limit": 20,
            "season_metadata_unavailable": 10,
            "fixture_status_not_scheduled": 5,
            "fixture_not_future": 3,
            "fixture_missing_teams": 7,
            "insufficient_recent_results": 15,
            "duplicate_fixture": 3,
            "invalid_fixture": 2,
        },
    )

    payload = funnel.as_dict()
    assert payload == {
        "fixtures_received": 145,
        "retained": 0,
        "rejected_competition": 100,
        "rejected_season": 10,
        "rejected_status": 5,
        "rejected_kickoff_window": 3,
        "rejected_missing_teams": 7,
        "rejected_insufficient_coverage": 15,
        "rejected_duplicate": 3,
        "rejected_other": 2,
    }
    assert payload["fixtures_received"] == payload["retained"] + sum(
        value
        for key, value in payload.items()
        if key.startswith("rejected_")
    )


def test_fixture_outside_requested_kinshasa_day_has_one_terminal_reason() -> None:
    as_of = datetime(2026, 7, 30, 20, 0, tzinfo=UTC)
    outside_match = {
        "provider_match_id": 31,
        "provider_competition_id": 344,
        "season": 2026,
        "kickoff_at": datetime(2026, 7, 31, 23, 30, tzinfo=UTC),
        "status_short": "NS",
    }
    plan = build_discovery_plan(
        NormalizationResult(resource="matches", rows=(outside_match,)),
        NormalizationResult(
            resource="competitions",
            rows=(
                {
                    "provider_competition_id": 344,
                    "kind": "League",
                },
            ),
        ),
        NormalizationResult(
            resource="seasons",
            rows=(
                {
                    "provider_competition_id": 344,
                    "year": 2026,
                    "coverage": {
                        "standings": True,
                        "fixtures": {"statistics_fixtures": True},
                    },
                },
            ),
        ),
        priority_competitions=(),
        enrichment_request_budget=10,
        as_of=as_of,
        window_starts_at=datetime(2026, 7, 30, 23, 0, tzinfo=UTC),
        window_ends_at=datetime(2026, 7, 31, 23, 0, tzinfo=UTC),
    )

    assert plan.competitions == ()
    assert plan.ignored_reasons == {
        "fixture_outside_requested_window": 1
    }
    assert build_retention_funnel(
        fixtures_received=1,
        retained=0,
        ignored_reasons=plan.ignored_reasons,
    ).rejected_kickoff_window == 1


def test_duplicate_provider_fixture_is_rejected_once_without_db_confusion() -> None:
    unique, duplicate_count = _deduplicate_fixture_rows(
        [
            {"provider_match_id": 31},
            {"provider_match_id": 31},
            {"provider_match_id": 32},
        ]
    )

    assert [row["provider_match_id"] for row in unique] == [31, 32]
    assert duplicate_count == 1
    funnel = build_retention_funnel(
        fixtures_received=3,
        retained=2,
        ignored_reasons={"duplicate_fixture": duplicate_count},
    )
    assert funnel.rejected_duplicate == 1


def test_daily_operations_reports_four_retained_three_evaluated_and_one_opportunity() -> None:
    funnel = build_retention_funnel(
        fixtures_received=4,
        retained=4,
        ignored_reasons={},
    ).as_dict()
    discovery_metrics = _safe_step_metrics(
        "daily_discovery",
        {
            "status": "SUCCEEDED",
            "fixtures_received": 4,
            "fixtures_retained": 4,
            "retention_funnel": funnel,
        },
    )
    snapshot_metrics = _safe_step_metrics(
        "snapshot",
        {
            "matches_evaluated": 3,
            "opportunities_generated": 1,
            "no_bet_count": 2,
            "insufficient_data_count": 0,
            "snapshots_created": 1,
        },
    )
    metrics = OperationMetrics()

    _record_success(metrics, "daily_discovery", discovery_metrics)
    _record_success(metrics, "snapshot", snapshot_metrics)

    assert metrics.fixtures_received == 4
    assert metrics.fixtures_retained == 4
    assert metrics.retention_funnel == funnel
    assert metrics.matches_evaluated == 3
    assert metrics.snapshots_created == 1
    assert metrics.opportunities_generated == 1
    assert metrics.no_bet_count == 2
    assert metrics.insufficient_data_count == 0


def test_saved_daily_status_rejects_a_non_reconciling_funnel() -> None:
    funnel = build_retention_funnel(
        fixtures_received=4,
        retained=4,
        ignored_reasons={},
    ).as_dict()
    payload = {
        "status": "completed",
        "correlation_id": "00000000-0000-0000-0000-000000000001",
        "target_date": "2026-07-31",
        "started_at": "2026-07-30T23:00:00+00:00",
        "completed_at": "2026-07-30T23:01:00+00:00",
        "error_code": None,
        "steps": [
            {
                "step": "daily_discovery",
                "status": "completed",
                "critical": True,
                "duration_ms": 1,
                "metrics": {
                    "fixtures_received": 4,
                    "fixtures_retained": 4,
                    "retention_funnel": funnel,
                },
            }
        ],
        "metrics": {
            "fixtures_received": 4,
            "fixtures_retained": 4,
            "retention_funnel": funnel,
        },
    }

    assert _sanitize_saved_status(payload)["metrics"][
        "retention_funnel"
    ] == funnel

    invalid = {
        **payload,
        "metrics": {
            "retention_funnel": {
                **funnel,
                "rejected_other": 1,
            }
        },
    }
    with pytest.raises(
        DailyOperationsUnavailable,
        match="daily_operations_status_invalid",
    ):
        _sanitize_saved_status(invalid)

    for unsafe_value in (-1, True, "0"):
        malformed = {
            **payload,
            "metrics": {
                "retention_funnel": {
                    **funnel,
                    "rejected_other": unsafe_value,
                }
            },
        }
        with pytest.raises(
            DailyOperationsUnavailable,
            match="daily_operations_status_invalid",
        ):
            _sanitize_saved_status(malformed)


def test_retention_funnel_is_fail_closed_when_missing_or_inconsistent() -> None:
    funnel = build_retention_funnel(
        fixtures_received=4,
        retained=3,
        ignored_reasons={"invalid_fixture": 1},
    ).as_dict()

    with pytest.raises(
        DailyOperationsUnavailable,
        match="retention_funnel_invalid",
    ):
        _safe_step_metrics(
            "daily_discovery",
            {
                "fixtures_received": 4,
                "fixtures_retained": 3,
            },
        )

    with pytest.raises(
        DailyOperationsUnavailable,
        match="retention_funnel_invalid",
    ):
        _safe_step_metrics(
            "daily_discovery",
            {
                "fixtures_received": 5,
                "fixtures_retained": 3,
                "retention_funnel": funnel,
            },
        )

    saved_status = {
        "status": "completed",
        "correlation_id": "00000000-0000-0000-0000-000000000001",
        "target_date": "2026-07-31",
        "started_at": "2026-07-30T23:00:00+00:00",
        "completed_at": "2026-07-30T23:01:00+00:00",
        "error_code": None,
        "steps": [],
        "metrics": {
            "fixtures_received": 0,
            "fixtures_retained": 0,
        },
    }
    with pytest.raises(
        DailyOperationsUnavailable,
        match="daily_operations_status_invalid",
    ):
        _sanitize_saved_status(saved_status)
