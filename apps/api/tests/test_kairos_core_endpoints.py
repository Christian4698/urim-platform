from contextlib import nullcontext
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import app.api.v1.routes.kairos as kairos_routes
from app.main import app
from app.modules.kairos.models import (
    KairosDataError,
    KairosTemporalIntegrityError,
)
from app.modules.kairos.rate_limit import RedisRateLimitUnavailable
from app.modules.kairos.repository import KairosRepository
from app.modules.kairos.schemas import (
    KairosAnalysisResponse,
    KairosDataFreshness,
    KairosFeatureAvailability,
    KairosMarketProbabilities,
    KairosProbabilities,
    KairosProvenance,
    KairosTeamSummary,
)
from app.modules.kairos.services import KairosAnalysisService
from app.modules.kairos.suggestions import build_kairos_suggestion

client = TestClient(app)


class _AllowAllLimiter:
    def retry_after(self, client_key: str) -> None:
        return None


@pytest.fixture(autouse=True)
def allow_rate_limited_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "_METHODOLOGY_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_ANALYSIS_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_SUGGESTIONS_RATE_LIMITER",
        _AllowAllLimiter(),
    )


def _response(
    as_of: datetime,
    *,
    provider_match_id: int = 999,
    strong_home_signal: bool = False,
) -> KairosAnalysisResponse:
    home_win = 0.8 if strong_home_signal else 0.4
    draw = 0.1 if strong_home_signal else 0.3
    away_win = 0.1 if strong_home_signal else 0.3
    probabilities = KairosProbabilities(
        home_win=home_win,
        draw=draw,
        away_win=away_win,
    )
    market_probabilities = KairosMarketProbabilities(
        home_win=home_win,
        draw=draw,
        away_win=away_win,
        home_or_draw=home_win + draw,
        away_or_draw=away_win + draw,
        home_or_away=home_win + away_win,
        over_2_5=0.6,
        under_2_5=0.4,
        btts=0.55,
    )
    suggestion = build_kairos_suggestion(
        provider_match_id=provider_match_id,
        kickoff_at=as_of + timedelta(hours=2),
        home_team_name="Home",
        away_team_name="Away",
        market_probabilities=market_probabilities,
        confidence_score=50,
        data_quality_score=75,
        freshness_status="fresh",
        analysis_reasons=[],
        analysis_warnings=[],
        feature_snapshot_hash="b" * 64,
    )
    return KairosAnalysisResponse(
        provider_match_id=provider_match_id,
        kickoff_at=as_of + timedelta(hours=2),
        prediction_id=UUID("00000000-0000-0000-0000-000000000001"),
        model_version="kairos_core_b2_2_v1",
        feature_snapshot_id=UUID(
            "00000000-0000-0000-0000-000000000002"
        ),
        prediction_time=as_of,
        probabilities=probabilities,
        market_probabilities=market_probabilities,
        home_win_probability=home_win,
        draw_probability=draw,
        away_win_probability=away_win,
        safety_decision="NO_BET",
        decision="NO_BET",
        confidence_score=50,
        data_quality_score=75,
        reasons=[],
        warnings=[],
        data_freshness=KairosDataFreshness(
            as_of=as_of,
            max_available_at=as_of - timedelta(minutes=2),
            target_fetched_at=as_of - timedelta(minutes=1),
            target_age_minutes=1,
            status="fresh",
            threshold_minutes=180,
        ),
        data_availability={
            "goals": KairosFeatureAvailability(
                home_samples=5,
                away_samples=5,
                required_samples_per_team=5,
                coverage_score=100,
                available_for_both_teams=True,
            )
        },
        home_team=KairosTeamSummary(
            provider_team_id=1,
            team_name="Home",
            recent_result_sample_size=5,
            venue_sample_size=3,
            form_points_per_game=2,
            goals_for_average=1.5,
            goals_against_average=0.8,
            standing_rank=2,
        ),
        away_team=KairosTeamSummary(
            provider_team_id=2,
            team_name="Away",
            recent_result_sample_size=5,
            venue_sample_size=3,
            form_points_per_game=1,
            goals_for_average=1,
            goals_against_average=1.4,
            standing_rank=10,
        ),
        provenance=KairosProvenance(
            source_observation_count=1,
            source_observation_ids=["source-1"],
            source_raw_hashes=["a" * 64],
            max_available_at=as_of - timedelta(minutes=2),
            feature_snapshot_hash="b" * 64,
        ),
        analytical_suggestion=suggestion,
        suggestion=suggestion,
        immutable_hash="c" * 64,
        analysis_status="ready",
    )


@pytest.fixture
def read_only_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> datetime:
    as_of = datetime.now(UTC) - timedelta(minutes=5)
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset",
        lambda _self, provider_match_id, as_of, recent_window: object(),
    )
    monkeypatch.setattr(
        KairosAnalysisService,
        "analyze",
        lambda _self, _dataset: _response(as_of),
    )
    return as_of


def test_kairos_methodology_is_read_only_and_explicitly_restricted() -> None:
    response = client.get("/api/v1/kairos/methodology")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_version"] == "kairos_core_b2_2_v1"
    assert payload["market"] == "1X2_PRE_MATCH"
    assert payload["read_only"] is True
    assert payload["db_writes"] is False
    assert payload["provider_calls"] is False
    assert payload["automatic_betting_enabled"] is False
    assert payload["live_automatic_enabled"] is False
    assert payload["calibration_status"] == "not_calibrated"
    assert payload["drift_monitoring_status"] == "not_available"


def test_kairos_analysis_endpoint_returns_required_probabilities(
    read_only_dataset: datetime,
) -> None:
    response = client.get(
        "/api/v1/kairos/matches/999/analysis",
        params={"as_of": read_only_dataset.isoformat()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["home_win_probability"] == 0.4
    assert payload["draw_probability"] == 0.3
    assert payload["away_win_probability"] == 0.3
    assert payload["confidence_score"] == 50
    assert payload["data_quality_score"] == 75
    assert payload["safety_decision"] == "NO_BET"
    assert payload["decision"] == "NO_BET"
    assert payload["analytical_suggestion"] == payload["suggestion"]
    assert payload["read_only"] is True
    assert payload["persisted"] is False
    assert payload["automatic_betting_enabled"] is False
    assert payload["live_automatic_enabled"] is False
    serialized = response.text.lower()
    assert "api_football_key" not in serialized
    assert "database_url" not in serialized
    assert "password" not in serialized


def test_daily_suggestions_are_read_only_and_use_local_database_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = SimpleNamespace(provider_match_id=999)
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        KairosRepository,
        "list_target_matches_as_of",
        lambda _self, starts_at, ends_at, as_of, limit: (target,),
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset_for_target",
        lambda _self, target, as_of, recent_window: object(),
    )
    monkeypatch.setattr(
        KairosAnalysisService,
        "analyze",
        lambda _self, _dataset: _response(datetime.now(UTC)),
    )

    response = client.get("/api/v1/kairos/suggestions/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["timezone"] == "Africa/Kinshasa"
    assert payload["suggestion_count"] == 1
    assert payload["evaluated_match_count"] == 1
    assert payload["suggestions"][0]["provider_match_id"] == 999
    assert payload["suggestions"][0]["recommendation"] == "NO_BET"
    assert payload["read_only"] is True
    assert payload["db_writes"] is False
    assert payload["provider_calls"] is False
    assert payload["automatic_betting_enabled"] is False
    assert payload["live_automatic_enabled"] is False
    serialized = response.text.lower()
    assert "database_url" not in serialized
    assert "api_football_key" not in serialized


def test_daily_suggestions_reject_query_amplification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: pytest.fail("database must not be opened"),
    )

    response = client.get(
        "/api/v1/kairos/suggestions/today?limit=999999"
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "kairos_query_parameters_invalid"
    )


def test_daily_suggestions_sort_actionable_signal_before_no_bet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    targets = (
        SimpleNamespace(provider_match_id=2),
        SimpleNamespace(provider_match_id=1),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        KairosRepository,
        "list_target_matches_as_of",
        lambda _self, starts_at, ends_at, as_of, limit: targets,
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset_for_target",
        lambda _self, target, as_of, recent_window: target,
    )
    monkeypatch.setattr(
        KairosAnalysisService,
        "analyze",
        lambda _self, dataset: _response(
            datetime.now(UTC),
            provider_match_id=dataset.provider_match_id,
            strong_home_signal=dataset.provider_match_id == 1,
        ),
    )

    response = client.get("/api/v1/kairos/suggestions/today")

    assert response.status_code == 200
    suggestions = response.json()["suggestions"]
    assert [item["provider_match_id"] for item in suggestions] == [1, 2]
    assert suggestions[0]["no_bet"] is False
    assert suggestions[1]["no_bet"] is True


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/kairos/methodology",
        "/api/v1/kairos/suggestions/today",
        "/api/v1/kairos/matches/999/analysis",
    ],
)
def test_kairos_mutating_routes_are_absent(path: str) -> None:
    assert client.post(path, json={}).status_code == 405
    assert client.put(path, json={}).status_code == 405
    assert client.patch(path, json={}).status_code == 405
    assert client.delete(path).status_code == 405


def test_kairos_rejects_future_as_of_without_opening_database_session() -> None:
    response = client.get(
        "/api/v1/kairos/matches/999/analysis",
        params={"as_of": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "kairos_future_as_of_forbidden"
    )


@pytest.mark.parametrize(
    "provider_match_id",
    ["0", "-1", "9223372036854775808", "1%20OR%201=1"],
)
def test_kairos_rejects_invalid_or_non_bigint_match_ids(
    provider_match_id: str,
) -> None:
    response = client.get(
        f"/api/v1/kairos/matches/{provider_match_id}/analysis"
    )

    assert response.status_code == 422


def test_kairos_rejects_timezone_naive_as_of() -> None:
    response = client.get(
        "/api/v1/kairos/matches/999/analysis",
        params={"as_of": "2026-07-27T12:00:00"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "kairos_as_of_timezone_required"
    )


def test_kairos_returns_not_found_for_missing_as_of_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset",
        lambda _self, provider_match_id, as_of, recent_window: None,
    )

    response = client.get("/api/v1/kairos/matches/999/analysis")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == (
        "kairos_match_not_found_as_of"
    )


def test_kairos_neutralizes_database_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_session_factory():
        raise RuntimeError("password=PRIVATE host=internal")

    monkeypatch.setattr(
        kairos_routes,
        "get_session_factory",
        fail_session_factory,
    )

    response = client.get("/api/v1/kairos/matches/999/analysis")

    assert response.status_code == 503
    assert "PRIVATE" not in response.text
    assert "internal" not in response.text
    assert response.json()["detail"]["code"] == "kairos_data_unavailable"


def test_kairos_fails_closed_when_distributed_rate_limit_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _UnavailableLimiter:
        def retry_after(self, client_key: str) -> None:
            raise RedisRateLimitUnavailable("private redis endpoint")

    monkeypatch.setattr(
        kairos_routes,
        "_METHODOLOGY_RATE_LIMITER",
        _UnavailableLimiter(),
    )

    response = client.get("/api/v1/kairos/methodology")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "1"
    assert response.json()["detail"]["code"] == (
        "kairos_rate_limit_unavailable"
    )
    assert "private redis endpoint" not in response.text


def test_kairos_temporal_failure_is_public_safe(
    read_only_dataset: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_temporal(_self: object, _dataset: object) -> None:
        raise KairosTemporalIntegrityError("private future row details")

    monkeypatch.setattr(
        KairosAnalysisService,
        "analyze",
        fail_temporal,
    )

    response = client.get(
        "/api/v1/kairos/matches/999/analysis",
        params={"as_of": read_only_dataset.isoformat()},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "kairos_temporal_integrity_blocked"
    )
    assert "private future row details" not in response.text


def test_kairos_data_integrity_failure_is_public_safe(
    read_only_dataset: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_integrity(_self: object, _dataset: object) -> None:
        raise KairosDataError("password=PRIVATE internal-provider-row")

    monkeypatch.setattr(
        KairosAnalysisService,
        "analyze",
        fail_integrity,
    )

    response = client.get(
        "/api/v1/kairos/matches/999/analysis",
        params={"as_of": read_only_dataset.isoformat()},
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == (
        "kairos_data_integrity_blocked"
    )
    assert "PRIVATE" not in response.text
    assert "internal-provider-row" not in response.text
