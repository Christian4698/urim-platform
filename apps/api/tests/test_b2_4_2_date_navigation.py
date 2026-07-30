from contextlib import nullcontext
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.api.v1.routes.kairos as kairos_routes
from app.main import app
from app.modules.kairos.journal import KairosJournalRepository
from app.modules.kairos.opportunities import KairosOpportunityService
from app.modules.kairos.rate_limit import RedisRateLimitUnavailable
from app.modules.kairos.repository import KairosRepository
from app.modules.kairos.schemas import (
    KairosHalfTimeMarketAnalysis,
    KairosMatchOpportunity,
    KairosOpportunityCandidate,
)
from app.modules.kairos.services import KairosAnalysisService
from app.modules.kairos.suggestions import build_kairos_suggestion


client = TestClient(app)
BEFORE_KINSHASA_MIDNIGHT = datetime(
    2026,
    7,
    30,
    22,
    30,
    tzinfo=UTC,
)
AT_KINSHASA_MIDNIGHT = datetime(
    2026,
    7,
    30,
    23,
    0,
    tzinfo=UTC,
)
TARGET_30 = SimpleNamespace(
    provider_match_id=30,
    kickoff_at=datetime(2026, 7, 30, 22, 45, tzinfo=UTC),
    home_team_name="Kinshasa Home 30",
    away_team_name="Kinshasa Away 30",
    competition_name="Ligue réelle 30",
)
TARGET_31 = SimpleNamespace(
    provider_match_id=31,
    kickoff_at=datetime(2026, 7, 30, 23, 30, tzinfo=UTC),
    home_team_name="Kinshasa Home 31",
    away_team_name="Kinshasa Away 31",
    competition_name="Ligue réelle 31",
)


class _AllowAllLimiter:
    def retry_after(self, client_key: str) -> None:
        return None


@pytest.fixture(autouse=True)
def isolated_daily_routes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "_SUGGESTIONS_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_OPPORTUNITIES_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )

    def list_targets(
        _self: KairosRepository,
        *,
        starts_at: datetime,
        ends_at: datetime,
        as_of: datetime,
        limit: int,
    ) -> tuple[SimpleNamespace, ...]:
        del limit
        return tuple(
            target
            for target in (TARGET_30, TARGET_31)
            if starts_at <= target.kickoff_at < ends_at
            and target.kickoff_at > as_of
        )

    monkeypatch.setattr(
        KairosRepository,
        "list_target_matches_as_of",
        list_targets,
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset_for_target",
        lambda _self, target, as_of, recent_window: target,
    )
    monkeypatch.setattr(
        KairosAnalysisService,
        "analyze",
        lambda _self, target: SimpleNamespace(
            analytical_suggestion=_suggestion(target)
        ),
    )
    monkeypatch.setattr(
        KairosOpportunityService,
        "analyze",
        lambda _self, target: _opportunity(target),
    )
    monkeypatch.setattr(
        KairosJournalRepository,
        "resolved_metrics",
        lambda _self: {},
    )


def test_explicit_dates_never_mix_suggestions_between_days(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "utc_now",
        lambda: BEFORE_KINSHASA_MIDNIGHT,
    )

    july_30 = client.get(
        "/api/v1/kairos/suggestions",
        params={"date": "2026-07-30"},
    )
    july_31 = client.get(
        "/api/v1/kairos/suggestions",
        params={"date": "2026-07-31"},
    )

    assert july_30.status_code == 200
    assert july_31.status_code == 200
    assert july_30.json()["local_date"] == "2026-07-30"
    assert july_31.json()["local_date"] == "2026-07-31"
    assert [
        item["provider_match_id"] for item in july_30.json()["suggestions"]
    ] == [30]
    assert [
        item["provider_match_id"] for item in july_31.json()["suggestions"]
    ] == [31]
    assert july_31.json()["suggestions"][0]["competition_name"] == (
        "Ligue réelle 31"
    )


def test_today_switches_exactly_at_kinshasa_midnight(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "utc_now",
        lambda: BEFORE_KINSHASA_MIDNIGHT,
    )
    before = client.get("/api/v1/kairos/suggestions/today")
    dated_before = client.get(
        "/api/v1/kairos/suggestions",
        params={"date": "2026-07-30"},
    )

    monkeypatch.setattr(
        kairos_routes,
        "utc_now",
        lambda: AT_KINSHASA_MIDNIGHT,
    )
    after = client.get("/api/v1/kairos/suggestions/today")

    assert before.status_code == 200
    assert dated_before.status_code == 200
    assert after.status_code == 200
    assert before.json()["local_date"] == "2026-07-30"
    assert after.json()["local_date"] == "2026-07-31"
    assert before.json()["suggestions"][0]["provider_match_id"] == 30
    assert before.json()["suggestions"] == dated_before.json()["suggestions"]
    assert after.json()["suggestions"][0]["provider_match_id"] == 31


def test_dated_opportunities_and_legacy_today_are_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "utc_now",
        lambda: AT_KINSHASA_MIDNIGHT,
    )

    dated = client.get(
        "/api/v1/kairos/opportunities",
        params={"date": "2026-07-31"},
    )
    legacy = client.get("/api/v1/kairos/opportunities/today")

    assert dated.status_code == 200
    assert legacy.status_code == 200
    assert dated.json()["local_date"] == "2026-07-31"
    assert dated.json()["opportunity_count"] == 1
    assert dated.json()["evaluated_match_count"] == 1
    assert dated.json()["opportunities"][0]["provider_match_id"] == 31
    assert dated.json()["opportunities"][0]["competition_name"] == (
        "Ligue réelle 31"
    )
    assert dated.json()["opportunities"] == legacy.json()["opportunities"]


@pytest.mark.parametrize(
    "path",
    (
        "/api/v1/kairos/suggestions",
        "/api/v1/kairos/opportunities",
    ),
)
def test_dated_endpoints_reject_missing_invalid_duplicate_or_unknown_dates(
    path: str,
) -> None:
    assert client.get(path).status_code == 422
    assert client.get(path, params={"date": "31-07-2026"}).status_code == 422
    assert client.get(f"{path}?date=2026-07-31&date=2026-08-01").status_code == 422
    assert client.get(
        path,
        params={"date": "2026-07-31", "as_of": "2026-07-30T22:00:00Z"},
    ).status_code == 422


@pytest.mark.parametrize(
    "unsafe_date",
    (
        "0",
        "2026-7-31",
        "2026-07-31T00:00:00Z",
        "0001-01-01",
        "9999-12-31",
    ),
)
@pytest.mark.parametrize(
    "path",
    (
        "/api/v1/kairos/suggestions",
        "/api/v1/kairos/opportunities",
    ),
)
def test_dated_endpoints_require_a_canonical_bounded_civil_date(
    path: str,
    unsafe_date: str,
) -> None:
    assert client.get(path, params={"date": unsafe_date}).status_code == 422


def test_invalid_date_query_is_rejected_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: pytest.fail("database access must not occur"),
    )

    response = client.get(
        "/api/v1/kairos/opportunities",
        params={"date": "2026-07-31", "unexpected": "1"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("path", "limiter_name"),
    (
        (
            "/api/v1/kairos/suggestions?date=2026-07-31",
            "_SUGGESTIONS_RATE_LIMITER",
        ),
        (
            "/api/v1/kairos/opportunities?date=2026-07-31",
            "_OPPORTUNITIES_RATE_LIMITER",
        ),
    ),
)
def test_dated_endpoints_fail_closed_when_redis_rate_limit_is_unavailable(
    path: str,
    limiter_name: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _UnavailableLimiter:
        def retry_after(self, client_key: str) -> None:
            raise RedisRateLimitUnavailable("private redis endpoint")

    monkeypatch.setattr(
        kairos_routes,
        limiter_name,
        _UnavailableLimiter(),
    )

    response = client.get(path)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == (
        "kairos_rate_limit_unavailable"
    )
    assert "private redis endpoint" not in response.text


def _suggestion(target: SimpleNamespace):
    return build_kairos_suggestion(
        provider_match_id=target.provider_match_id,
        kickoff_at=target.kickoff_at,
        home_team_name=target.home_team_name,
        away_team_name=target.away_team_name,
        competition_name=target.competition_name,
        market_probabilities=None,
        confidence_score=0,
        data_quality_score=0,
        freshness_status="fresh",
        analysis_reasons=[],
        analysis_warnings=[],
        feature_snapshot_hash="a" * 64,
    )


def _opportunity(target: SimpleNamespace) -> KairosMatchOpportunity:
    market = KairosHalfTimeMarketAnalysis(
        market="SECOND_HALF_OVER_0_5",
        estimated_probability=0.8,
        data_quality_score=80,
        technical_confidence_score=60,
        sample_size=10,
        h2h_sample_size=3,
        risk="guarded",
        reasons=["Historique complet."],
        guardrails=[],
        eligible_for_opportunity=True,
        insufficient_data=False,
        analysis_hash="b" * 64,
    )
    candidate = KairosOpportunityCandidate(
        market="SECOND_HALF_OVER_0_5",
        estimated_probability=0.8,
        data_quality_score=80,
        technical_confidence_score=60,
        sample_size=10,
        risk="guarded",
        reasons=["Historique complet."],
        guardrails=[],
        analysis_hash="b" * 64,
    )
    return KairosMatchOpportunity(
        provider_match_id=target.provider_match_id,
        kickoff_at=target.kickoff_at,
        home_team_name=target.home_team_name,
        away_team_name=target.away_team_name,
        competition_name=target.competition_name,
        section="GOAL_MARKETS",
        safety_decision="ANALYSIS_ALLOWED",
        primary_analysis=candidate,
        alternative_analyses=[],
        evaluated_markets=[market],
    )
