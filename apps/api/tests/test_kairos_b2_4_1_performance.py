from __future__ import annotations

from contextlib import nullcontext
from datetime import UTC, datetime
import re
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

import app.api.v1.routes.kairos as kairos_routes
from app.main import app
from app.modules.kairos.performance import (
    KairosPerformanceRepository,
    _segment_from_row,
)
from app.modules.kairos.schemas import KairosPerformanceResponse


class _AllowAllLimiter:
    def retry_after(self, client_key: str) -> None:
        return None


class _Result:
    def __init__(
        self,
        *,
        row: dict[str, Any] | None = None,
        rows: tuple[dict[str, Any], ...] = (),
    ) -> None:
        self.row = row
        self.rows = rows

    def mappings(self) -> _Result:
        return self

    def one(self) -> dict[str, Any]:
        assert self.row is not None
        return self.row

    def __iter__(self):
        return iter(self.rows)


class _RecordingSession:
    def __init__(self) -> None:
        self.statements: list[Any] = []
        self.results = [
            _Result(
                row={
                    "total_snapshots": 0,
                    "resolved_sample_size": 0,
                    "void_count": 0,
                    "unresolved_count": 0,
                    "success_count": 0,
                    "last_resolution_at": None,
                }
            ),
            _Result(),
            _Result(),
            _Result(),
            _Result(),
            _Result(),
        ]

    def execute(self, statement):
        self.statements.append(statement)
        return self.results.pop(0)


def _segment_row(*, resolved: int) -> dict[str, object]:
    return {
        "segment_key": "SECOND_HALF_OVER_0_5",
        "segment_label": "Seconde période · au moins un but",
        "total_snapshots": resolved + 2,
        "resolved_sample_size": resolved,
        "success_count": round(resolved * 0.7),
        "void_count": 1,
        "unresolved_count": 1,
        "estimated_probability_mean": 0.76 if resolved else None,
    }


def test_performance_empty_report_exposes_every_market_without_claim() -> None:
    session = _RecordingSession()
    report = KairosPerformanceRepository(
        cast(Session, session)
    ).report(generated_at=datetime(2026, 7, 30, 12, tzinfo=UTC))

    assert report.total_snapshots == 0
    assert report.observed_hit_rate is None
    assert report.sample_status == "no_sample"
    assert len(report.performance_by_market) == 9
    assert all(
        segment.sample_status == "no_sample"
        for segment in report.performance_by_market
    )
    assert any(
        "Échantillon insuffisant" in warning
        for warning in report.warnings
    )
    overall_sql = str(
        session.statements[0].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "SUCCESS" in overall_sql
    assert "FAILURE" in overall_sql
    assert "VOID" in overall_sql
    assert "IS NULL" in overall_sql
    competition_sql = str(
        session.statements[2].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "AVAILABLE_AT <=" in competition_sql
    assert "FETCHED_AT <=" in competition_sql
    assert "CREATED_AT <=" in competition_sql
    assert "LATERAL" in competition_sql
    assert "ANALYSIS_TIME" in competition_sql
    assert len(re.findall(r"\bLIMIT 1\b", competition_sql)) == 2
    assert (
        "API_FOOTBALL_MATCHES.AVAILABLE_AT <= "
        "KAIROS_ANALYSIS_JOURNAL.ANALYSIS_TIME"
    ) in competition_sql
    assert (
        "API_FOOTBALL_COMPETITIONS.AVAILABLE_AT <= "
        "KAIROS_ANALYSIS_JOURNAL.ANALYSIS_TIME"
    ) in competition_sql
    assert "API_FOOTBALL_COMPETITIONS" in competition_sql
    assert "API_FOOTBALL_COMPETITIONS.NAME" in competition_sql
    assert "COMPÉTITION INCONNUE" in competition_sql
    assert "CONCAT(" not in competition_sql
    calibration_sql = str(
        session.statements[5].compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "CALIBRATION_0_70_0_79" in calibration_sql
    assert "CALIBRATION_0_90_1_00" in calibration_sql


def test_performance_under_thirty_stays_insufficient() -> None:
    segment = _segment_from_row(cast(Any, _segment_row(resolved=29)))

    assert segment.resolved_sample_size == 29
    assert segment.observed_hit_rate is not None
    assert segment.sample_status == "insufficient_sample"
    assert segment.total_snapshots == (
        segment.resolved_sample_size
        + segment.void_count
        + segment.unresolved_count
    )


def test_performance_from_thirty_is_descriptive_not_calibrated() -> None:
    segment = _segment_from_row(cast(Any, _segment_row(resolved=30)))

    assert segment.resolved_sample_size == 30
    assert segment.sample_status == "descriptive_sample_available"
    assert segment.estimated_probability_mean == 0.76
    assert segment.observed_hit_rate == 0.7


def test_performance_endpoint_is_read_only_and_secret_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = KairosPerformanceResponse(
        generated_at=datetime(2026, 7, 30, 12, tzinfo=UTC),
        total_snapshots=0,
        resolved=0,
        unresolved=0,
        void=0,
        resolved_sample_size=0,
        success_count=0,
        observed_hit_rate=None,
        sample_status="no_sample",
        performance_by_market=[],
        performance_by_competition=[],
        performance_by_probability_band=[],
        performance_by_quality_level=[],
        calibration_buckets=[],
        last_resolution_at=None,
        last_report_generated_at=datetime(
            2026,
            7,
            30,
            12,
            tzinfo=UTC,
        ),
        warnings=["Échantillon insuffisant."],
    )
    monkeypatch.setattr(
        kairos_routes,
        "_PERFORMANCE_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        KairosPerformanceRepository,
        "report",
        lambda _self, generated_at: report,
    )

    response = TestClient(app).get("/api/v1/kairos/performance")

    assert response.status_code == 200
    payload = response.json()
    assert payload["observed_hit_rate"] is None
    assert payload["sample_status"] == "no_sample"
    assert payload["read_only"] is True
    assert payload["db_writes"] is False
    assert payload["provider_calls"] is False
    assert payload["automatic_betting_enabled"] is False
    serialized = response.text.lower()
    assert "database_url" not in serialized
    assert "api_football_key" not in serialized


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_performance_mutations_are_absent(method: str) -> None:
    response = TestClient(app).request(
        method,
        "/api/v1/kairos/performance",
    )

    assert response.status_code == 405
