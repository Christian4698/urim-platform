from contextlib import nullcontext
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import app.api.v1.routes.sports as sports_routes
from app.main import app
from app.modules.sports_data.repository import SportsRepository

client = TestClient(app)
NOW = datetime.now(UTC)


def provenance(event_id: str) -> dict[str, object]:
    return {
        "provider": "api-football",
        "provider_event_id": event_id,
        "observed_at": NOW - timedelta(seconds=2),
        "available_at": NOW - timedelta(seconds=1),
        "fetched_at": NOW,
        "source_version": "football-v3",
        "quality_flags": ["REAL_PROVIDER_DATA", "NORMALIZED"],
        "raw_hash": "a" * 64,
        "freshness_status": "fresh",
    }


@pytest.fixture
def fake_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sports_routes, "_session", lambda: nullcontext(object()))


def test_provider_status_is_disabled_without_key_and_exposes_no_secret() -> None:
    response = client.get("/api/v1/sports/provider")
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "api-football"
    assert payload["enabled"] is False
    assert payload["configured"] is False
    assert payload["status"] == "disabled_missing_credential"
    assert payload["prediction_creation_enabled"] is False
    assert payload["live_automatic_enabled"] is False
    assert payload["bookmakers_enabled"] is False
    assert payload["betting_enabled"] is False
    serialized = response.text.lower()
    assert "api_football_key" not in serialized
    assert "x-apisports-key" not in serialized


def test_competitions_and_matches_endpoints_are_read_only(
    fake_session: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    competition_row = {
        **provenance("competition:39"),
        "provider_competition_id": 39,
        "name": "Competition Test",
        "kind": "League",
        "country_name": "Test Country",
        "country_code": "TC",
        "current_season": 2026,
        "coverage": {"fixtures": True},
    }
    match_row = {
        **provenance("match:10"),
        "provider_match_id": 10,
        "provider_competition_id": 39,
        "season": 2026,
        "kickoff_at": NOW + timedelta(hours=2),
        "timezone": "UTC",
        "status_short": "NS",
        "status_long": "Not Started",
        "elapsed": None,
        "round": "Round 1",
        "venue_name": None,
        "venue_city": None,
        "home_team_provider_id": 1,
        "home_team_name": "Home Test",
        "away_team_provider_id": 2,
        "away_team_name": "Away Test",
        "goals_home": None,
        "goals_away": None,
        "score_halftime_home": None,
        "score_halftime_away": None,
        "score_fulltime_home": None,
        "score_fulltime_away": None,
    }
    monkeypatch.setattr(
        SportsRepository,
        "list_competitions",
        lambda _self, limit: [competition_row],
    )
    monkeypatch.setattr(
        SportsRepository,
        "list_matches",
        lambda _self, starts_at, ends_at, limit=200: [match_row],
    )

    competitions = client.get("/api/v1/sports/competitions")
    today = client.get("/api/v1/sports/matches/today")
    upcoming = client.get("/api/v1/sports/matches/upcoming?days=7")

    assert competitions.status_code == 200
    assert competitions.json()["count"] == 1
    assert competitions.json()["items"][0]["name"] == "Competition Test"
    assert today.status_code == 200
    assert today.json()["read_only"] is True
    assert upcoming.status_code == 200
    assert upcoming.json()["items"][0]["goals_home"] is None
    assert client.post("/api/v1/sports/competitions", json={}).status_code == 405


def test_match_detail_returns_only_sports_data_without_prediction_surfaces(
    fake_session: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    match_row = {
        **provenance("match:10"),
        "provider_match_id": 10,
        "provider_competition_id": 39,
        "season": 2026,
        "kickoff_at": NOW,
        "timezone": "UTC",
        "status_short": "FT",
        "status_long": "Match Finished",
        "elapsed": 90,
        "round": None,
        "venue_name": None,
        "venue_city": None,
        "home_team_provider_id": 1,
        "home_team_name": "Home Test",
        "away_team_provider_id": 2,
        "away_team_name": "Away Test",
        "goals_home": 1,
        "goals_away": 0,
        "score_halftime_home": 0,
        "score_halftime_away": 0,
        "score_fulltime_home": 1,
        "score_fulltime_away": 0,
    }
    statistic = {
        **provenance("match-statistic:10:1:shots"),
        "provider_match_id": 10,
        "provider_team_id": 1,
        "statistic_type": "Shots on Goal",
        "statistic_value": 4,
    }
    monkeypatch.setattr(SportsRepository, "get_match", lambda _self, _id: match_row)
    monkeypatch.setattr(
        SportsRepository,
        "list_match_resource",
        lambda _self, resource, _id: [statistic]
        if resource == "match_statistics"
        else [],
    )

    response = client.get("/api/v1/sports/matches/10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["match"]["provider_match_id"] == 10
    assert payload["statistics"][0]["statistic_value"] == 4
    assert payload["events"] == []
    assert payload["lineups"] == []
    assert payload["injuries"] == []
    assert "predictions" not in payload
    assert "betting" not in payload


def test_sync_status_and_freshness_are_public_safe(
    fake_session: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        SportsRepository,
        "latest_sync_status",
        lambda _self: {
            "id": "00000000-0000-0000-0000-000000000001",
            "sync_type": "matches_date",
            "status": "PARTIAL",
            "started_at": NOW - timedelta(minutes=2),
            "completed_at": NOW,
            "request_count": 2,
            "records_received": 10,
            "records_inserted": 9,
            "records_duplicate": 0,
            "records_rejected": 1,
            "quota_remaining_daily": 98,
            "quota_remaining_minute": 8,
            "public_error_code": "invalid_matches_row",
        },
    )
    monkeypatch.setattr(
        SportsRepository,
        "recent_public_errors",
        lambda _self: ["invalid_matches_row"],
    )
    monkeypatch.setattr(
        SportsRepository,
        "resource_freshness",
        lambda _self: [
            {
                "resource": "matches",
                "latest_fetched_at": NOW,
                "row_count": 10,
            },
            {
                "resource": "statistics",
                "latest_fetched_at": None,
                "row_count": 0,
            },
        ],
    )

    sync = client.get("/api/v1/sports/sync/status")
    freshness = client.get("/api/v1/sports/freshness")
    assert sync.status_code == 200
    assert sync.json()["latest"]["public_error_code"] == "invalid_matches_row"
    assert freshness.status_code == 200
    assert freshness.json()["resources"][0]["status"] == "fresh"
    assert freshness.json()["resources"][1]["status"] == "missing"
    assert "password" not in sync.text.lower()
    assert "database_url" not in sync.text.lower()


def test_database_failures_are_neutralized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_session_factory():
        raise RuntimeError("password=PRIVATE host=internal")

    monkeypatch.setattr(
        sports_routes,
        "get_session_factory",
        fail_session_factory,
    )
    response = client.get("/api/v1/sports/competitions")
    assert response.status_code == 503
    assert "PRIVATE" not in response.text
    assert "internal" not in response.text
