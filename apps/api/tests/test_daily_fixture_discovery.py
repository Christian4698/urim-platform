import asyncio
from datetime import UTC, date, datetime, timedelta
import hashlib
from typing import Any
from uuid import uuid4

import pytest

from app.cli import sports_sync
from app.cli.sports_sync import build_parser
from app.core.config import Settings
from app.modules.sports_data.discovery import (
    build_discovery_plan,
    select_recent_matches_for_statistics,
)
from app.modules.sports_data.normalization import NormalizationResult
from app.modules.sports_data.provider import (
    ApiFootballDisabledError,
    ApiFootballEnvelope,
    ApiFootballEnvelopeModel,
    ApiFootballRequestError,
)
from app.modules.sports_data.sync import (
    SportsSyncConfigurationError,
    SportsSyncService,
)

NOW = datetime(2026, 7, 28, 10, 0, tzinfo=UTC)
TARGET_DATE = date(2026, 7, 29)
COMPETITION_ID = 140
SEASON = 2026
HOME_ID = 1001
AWAY_ID = 1002


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeRepository:
    def __init__(self) -> None:
        self.run_id = uuid4()
        self.errors: list[dict[str, Any]] = []
        self.finished: dict[str, Any] | None = None
        self.seen: set[tuple[str, str, str]] = set()

    def ensure_provider(self, *, enabled: bool):
        assert enabled is True
        return uuid4()

    def start_run(self, **_kwargs: object):
        return self.run_id

    def insert_result(self, result, **_kwargs: object) -> tuple[int, int]:
        inserted = 0
        for row in result.rows:
            key = (
                result.resource,
                str(row["provider_event_id"]),
                str(row["raw_hash"]),
            )
            if key in self.seen:
                continue
            self.seen.add(key)
            inserted += 1
        return inserted, len(result.rows) - inserted

    def record_error(self, **kwargs: Any) -> None:
        self.errors.append(dict(kwargs))

    def finish_run(self, **kwargs: Any) -> None:
        self.finished = dict(kwargs)


class FakeClient:
    enabled = True

    def __init__(
        self,
        responses: dict[str, list[ApiFootballEnvelope]],
        *,
        failure: ApiFootballRequestError | None = None,
    ) -> None:
        self.responses = responses
        self.failure = failure
        self.request_count = 0
        self.quota_remaining_daily: int | None = 100
        self.quota_remaining_minute: int | None = 100
        self.requests: list[tuple[str, object]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def get(
        self,
        endpoint: str,
        params: object,
    ) -> ApiFootballEnvelope:
        self.request_count += 1
        self.quota_remaining_daily = 100 - self.request_count
        self.quota_remaining_minute = 100 - self.request_count
        self.requests.append((endpoint, params))
        if self.failure is not None:
            raise self.failure
        return self.responses[endpoint].pop(0)


class DisabledClient(FakeClient):
    enabled = False


def _envelope(
    endpoint: str,
    response: list[object],
    marker: str,
) -> ApiFootballEnvelope:
    digest = hashlib.sha256(marker.encode("ascii")).hexdigest()
    return ApiFootballEnvelope(
        endpoint=endpoint,
        request_id=f"TEST_ONLY_{marker}",
        fetched_at=NOW,
        observed_at=NOW,
        available_at=NOW,
        source_version="football-v3-test-only",
        raw_hash=digest,
        quota_limit_daily=100,
        quota_remaining_daily=90,
        quota_limit_minute=100,
        quota_remaining_minute=90,
        data=ApiFootballEnvelopeModel(
            get=endpoint,
            parameters={},
            errors=[],
            results=len(response),
            paging={"current": 1, "total": 1},
            response=response,
        ),
    )


def _fixture(
    fixture_id: int,
    *,
    kickoff_at: datetime,
    status: str = "NS",
    home_id: int = HOME_ID,
    away_id: int = AWAY_ID,
) -> dict[str, object]:
    return {
        "fixture": {
            "id": fixture_id,
            "date": kickoff_at.isoformat(),
            "timezone": "UTC",
            "status": {"short": status, "long": "TEST_ONLY"},
            "venue": {},
        },
        "league": {
            "id": COMPETITION_ID,
            "season": SEASON,
            "round": "TEST_ONLY",
        },
        "teams": {
            "home": {"id": home_id, "name": f"TEST_ONLY_TEAM_{home_id}"},
            "away": {"id": away_id, "name": f"TEST_ONLY_TEAM_{away_id}"},
        },
        "goals": {"home": None, "away": None},
        "score": {"halftime": {}, "fulltime": {}},
    }


def _league() -> dict[str, object]:
    return {
        "league": {
            "id": COMPETITION_ID,
            "name": "TEST_ONLY_LEAGUE",
            "type": "League",
        },
        "country": {"name": "TEST_ONLY_COUNTRY", "code": "TT"},
        "seasons": [
            {
                "year": SEASON,
                "start": "2026-01-01",
                "end": "2026-12-31",
                "current": True,
                "coverage": {
                    "standings": True,
                    "fixtures": {"statistics_fixtures": True},
                },
            }
        ],
    }


def _team(team_id: int) -> dict[str, object]:
    return {
        "team": {
            "id": team_id,
            "name": f"TEST_ONLY_TEAM_{team_id}",
            "national": False,
        },
        "venue": {},
    }


def _standing(team_id: int, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "team": {"id": team_id, "name": f"TEST_ONLY_TEAM_{team_id}"},
        "points": 10,
        "goalsDiff": 1,
        "group": "TEST_ONLY_GROUP",
        "form": "WWD",
        "all": {
            "played": 3,
            "win": 2,
            "draw": 1,
            "lose": 0,
            "goals": {"for": 4, "against": 1},
        },
    }


def _responses() -> dict[str, list[ApiFootballEnvelope]]:
    history = [
        _fixture(
            2000 + index,
            kickoff_at=NOW - timedelta(days=7 * (index + 1)),
            status="FT",
        )
        for index in range(3)
    ]
    standings = {
        "league": {
            "id": COMPETITION_ID,
            "season": SEASON,
            "standings": [
                [
                    _standing(HOME_ID, 1),
                    _standing(AWAY_ID, 2),
                ]
            ],
        }
    }
    statistics = [
        _envelope(
            "fixtures/statistics",
            [
                {
                    "team": {"id": HOME_ID},
                    "statistics": [
                        {"type": "Total Shots", "value": 10}
                    ],
                },
                {
                    "team": {"id": AWAY_ID},
                    "statistics": [
                        {"type": "Total Shots", "value": 8}
                    ],
                },
            ],
            f"statistics-{index}",
        )
        for index in range(3)
    ]
    return {
        "fixtures": [
            _envelope(
                "fixtures",
                [
                    _fixture(
                        1234,
                        kickoff_at=datetime(
                            2026,
                            7,
                            29,
                            18,
                            0,
                            tzinfo=UTC,
                        ),
                    )
                ],
                "discovery",
            ),
            _envelope("fixtures", history, "history"),
        ],
        "leagues": [_envelope("leagues", [_league()], "leagues")],
        "teams": [
            _envelope(
                "teams",
                [_team(HOME_ID), _team(AWAY_ID)],
                "teams",
            )
        ],
        "standings": [_envelope("standings", [standings], "standings")],
        "fixtures/statistics": statistics,
    }


def _refresh_responses() -> dict[str, list[ApiFootballEnvelope]]:
    responses = _responses()
    discovery, history = responses["fixtures"]
    responses["fixtures"] = [
        discovery,
        *[
            _envelope("fixtures", [], f"discovery-empty-{offset}")
            for offset in range(1, 7)
        ],
        history,
    ]
    return responses


def _settings(
    max_requests: int = 10,
    *,
    priority_competitions: str = "39",
    season: int | None = None,
) -> Settings:
    return Settings(
        _env_file=None,
        api_football_max_requests_per_sync=max_requests,
        api_football_priority_competitions=priority_competitions,
        api_football_season=season,
    )


def test_cli_exposes_bounded_daily_commands() -> None:
    parser = build_parser()

    discovery = parser.parse_args(
        ["daily-discovery", "--date", "2026-07-29"]
    )
    refresh = parser.parse_args(["daily-refresh", "--days", "7"])

    assert discovery.command == "daily-discovery"
    assert discovery.date == TARGET_DATE
    assert refresh.command == "daily-refresh"
    assert refresh.days == 7


def test_discovery_plan_is_not_limited_to_priority_competitions() -> None:
    fixture_row = {
        "provider_competition_id": COMPETITION_ID,
        "season": SEASON,
        "status_short": "NS",
        "kickoff_at": NOW + timedelta(days=1),
    }
    plan = build_discovery_plan(
        NormalizationResult(resource="matches", rows=(fixture_row,)),
        NormalizationResult(
            resource="competitions",
            rows=(
                {
                    "provider_competition_id": COMPETITION_ID,
                    "kind": "League",
                },
            ),
        ),
        NormalizationResult(
            resource="seasons",
            rows=(
                {
                    "provider_competition_id": COMPETITION_ID,
                    "year": SEASON,
                    "coverage": {
                        "standings": True,
                        "fixtures": {"statistics_fixtures": True},
                    },
                },
            ),
        ),
        priority_competitions=(39,),
        enrichment_request_budget=5,
        as_of=NOW,
    )

    assert [item.provider_competition_id for item in plan.competitions] == [
        COMPETITION_ID
    ]
    assert plan.ignored_reasons == {}


def test_discovery_plan_rejects_past_and_unsupported_fixtures() -> None:
    rows = (
        {
            "provider_competition_id": COMPETITION_ID,
            "season": SEASON,
            "status_short": "FT",
            "kickoff_at": NOW - timedelta(hours=1),
        },
        {
            "provider_competition_id": COMPETITION_ID,
            "season": SEASON,
            "status_short": "NS",
            "kickoff_at": NOW - timedelta(minutes=1),
        },
    )
    plan = build_discovery_plan(
        NormalizationResult(resource="matches", rows=rows),
        NormalizationResult(resource="competitions", rows=()),
        NormalizationResult(resource="seasons", rows=()),
        priority_competitions=(),
        enrichment_request_budget=5,
        as_of=NOW,
    )

    assert plan.competitions == ()
    assert plan.ignored_reasons == {
        "fixture_not_future": 1,
        "fixture_status_not_scheduled": 1,
    }


def test_discovery_plan_never_selects_more_than_five_competitions() -> None:
    fixture_rows = tuple(
        {
            "provider_competition_id": competition_id,
            "season": SEASON,
            "status_short": "NS",
            "kickoff_at": NOW + timedelta(days=1),
        }
        for competition_id in range(100, 106)
    )
    competition_rows = tuple(
        {
            "provider_competition_id": competition_id,
            "kind": "League",
        }
        for competition_id in range(100, 106)
    )
    season_rows = tuple(
        {
            "provider_competition_id": competition_id,
            "year": SEASON,
            "coverage": {
                "standings": False,
                "fixtures": {"statistics_fixtures": True},
            },
        }
        for competition_id in range(100, 106)
    )

    plan = build_discovery_plan(
        NormalizationResult(resource="matches", rows=fixture_rows),
        NormalizationResult(
            resource="competitions",
            rows=competition_rows,
        ),
        NormalizationResult(resource="seasons", rows=season_rows),
        priority_competitions=(),
        enrichment_request_budget=20,
        as_of=NOW,
    )

    assert len(plan.competitions) == 5
    assert plan.ignored_reasons == {"competition_limit": 1}


def test_daily_discovery_ingests_only_kairos_inputs_and_reports_counts() -> None:
    session = FakeSession()
    client = FakeClient(_responses())
    service = SportsSyncService(
        session,  # type: ignore[arg-type]
        app_settings=_settings(),
        client=client,  # type: ignore[arg-type]
    )
    repository = FakeRepository()
    service.repository = repository  # type: ignore[assignment]

    summary = asyncio.run(
        service._sync_daily_window(
            sync_type="daily_discovery",
            starts_on=TARGET_DATE,
            days=1,
            started_at=NOW,
        )
    )

    assert summary.status == "SUCCEEDED"
    assert summary.fixtures_received == 1
    assert summary.fixtures_retained == 1
    assert summary.fixtures_ignored == 0
    assert summary.competitions_selected == 1
    assert summary.target_matches_added == 1
    assert summary.recent_results_added == 3
    assert summary.standings_rows_available == 2
    assert summary.statistics_matches_available == 3
    assert summary.statistics_matches_skipped_quota == 0
    assert summary.statistics_rows_added == 6
    assert summary.provider_unavailable_causes == ()
    assert summary.request_count == 8
    assert summary.runtime_configuration == {
        "api_football_enabled": False,
        "api_football_key_present": False,
        "api_football_season_present": False,
        "api_football_priority_competitions_present": True,
        "provider_runtime_ready": False,
    }
    assert all(
        endpoint
        in {
            "fixtures",
            "leagues",
            "teams",
            "standings",
            "fixtures/statistics",
        }
        for endpoint, _params in client.requests
    )
    assert repository.finished is not None
    assert repository.finished["checkpoint"]["fixtures_retained"] == 1


def test_daily_discovery_respects_request_budget_before_statistics() -> None:
    responses = _responses()
    responses["fixtures/statistics"] = []
    session = FakeSession()
    client = FakeClient(responses)
    service = SportsSyncService(
        session,  # type: ignore[arg-type]
        app_settings=_settings(max_requests=5),
        client=client,  # type: ignore[arg-type]
    )
    service.repository = FakeRepository()  # type: ignore[assignment]

    summary = asyncio.run(
        service._sync_daily_window(
            sync_type="daily_discovery",
            starts_on=TARGET_DATE,
            days=1,
            started_at=NOW,
        )
    )

    assert summary.fixtures_retained == 1
    assert summary.request_count == 5
    assert summary.statistics_matches_available == 0
    assert summary.statistics_matches_skipped_quota == 3
    assert all(
        endpoint != "fixtures/statistics"
        for endpoint, _params in client.requests
    )


def test_daily_refresh_queries_each_utc_date_in_temporal_order() -> None:
    session = FakeSession()
    client = FakeClient(_refresh_responses())
    service = SportsSyncService(
        session,  # type: ignore[arg-type]
        app_settings=_settings(max_requests=20),
        client=client,  # type: ignore[arg-type]
    )
    service.repository = FakeRepository()  # type: ignore[assignment]

    summary = asyncio.run(
        service._sync_daily_window(
            sync_type="daily_refresh",
            starts_on=TARGET_DATE,
            days=7,
            started_at=NOW,
        )
    )

    fixture_discovery_params = [
        params
        for endpoint, params in client.requests[:7]
        if endpoint == "fixtures"
    ]
    assert fixture_discovery_params == [
        {
            "date": (TARGET_DATE + timedelta(days=offset)).isoformat(),
            "timezone": "UTC",
        }
        for offset in range(7)
    ]
    assert all(
        "from" not in params and "to" not in params
        for params in fixture_discovery_params
    )
    assert summary.status == "SUCCEEDED"
    assert summary.fixture_dates_requested == 7
    assert summary.fixture_dates_succeeded == 7
    assert summary.fixture_dates_failed == 0
    assert summary.fixtures_received == 1
    assert summary.target_matches_added == 1
    assert summary.competitions_selected <= 5


def test_daily_discovery_is_idempotent_and_reports_match_duplicates() -> None:
    repository = FakeRepository()
    first_service = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(),
        client=FakeClient(_responses()),  # type: ignore[arg-type]
    )
    first_service.repository = repository  # type: ignore[assignment]
    second_service = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(),
        client=FakeClient(_responses()),  # type: ignore[arg-type]
    )
    second_service.repository = repository  # type: ignore[assignment]

    first = asyncio.run(
        first_service._sync_daily_window(
            sync_type="daily_discovery",
            starts_on=TARGET_DATE,
            days=1,
            started_at=NOW,
        )
    )
    second = asyncio.run(
        second_service._sync_daily_window(
            sync_type="daily_discovery",
            starts_on=TARGET_DATE,
            days=1,
            started_at=NOW,
        )
    )

    assert first.target_matches_added == 1
    assert first.recent_results_added == 3
    assert second.target_matches_added == 0
    assert second.recent_results_added == 0
    assert second.match_duplicates == 4
    assert second.statistics_rows_added == 0


def test_daily_discovery_enriches_missing_h2h_with_bounded_idempotent_calls() -> None:
    def responses() -> dict[str, list[ApiFootballEnvelope]]:
        values = _responses()
        split_history = [
            *[
                _fixture(
                    3000 + index,
                    kickoff_at=NOW - timedelta(days=index + 1),
                    status="FT",
                    home_id=HOME_ID,
                    away_id=4000 + index,
                )
                for index in range(3)
            ],
            *[
                _fixture(
                    5000 + index,
                    kickoff_at=NOW - timedelta(days=index + 1),
                    status="FT",
                    home_id=6000 + index,
                    away_id=AWAY_ID,
                )
                for index in range(3)
            ],
        ]
        values["fixtures"][1] = _envelope(
            "fixtures",
            split_history,
            "split-history",
        )
        values["fixtures/headtohead"] = [
            _envelope(
                "fixtures/headtohead",
                [
                    _fixture(
                        7000 + index,
                        kickoff_at=NOW - timedelta(days=20 + index),
                        status="FT",
                    )
                    for index in range(2)
                ],
                "h2h",
            )
        ]
        return values

    repository = FakeRepository()
    summaries = []
    request_lists = []
    for _ in range(2):
        client = FakeClient(responses())
        service = SportsSyncService(
            FakeSession(),  # type: ignore[arg-type]
            app_settings=_settings(max_requests=6),
            client=client,  # type: ignore[arg-type]
        )
        service.repository = repository  # type: ignore[assignment]
        summaries.append(
            asyncio.run(
                service._sync_daily_window(
                    sync_type="daily_discovery",
                    starts_on=TARGET_DATE,
                    days=1,
                    started_at=NOW,
                )
            )
        )
        request_lists.append(client.requests)

    first, second = summaries
    assert first.h2h_requests == 1
    assert first.h2h_matches_received == 2
    assert first.h2h_matches_added == 2
    assert first.h2h_duplicates == 0
    assert second.h2h_matches_added == 0
    assert second.h2h_duplicates == 2
    assert all(
        sum(
            endpoint == "fixtures/headtohead"
            for endpoint, _params in requests
        )
        == 1
        for requests in request_lists
    )
    assert all(summary.request_count == 6 for summary in summaries)


def test_daily_discovery_reports_neutralized_provider_cause() -> None:
    session = FakeSession()
    client = FakeClient(
        {},
        failure=ApiFootballRequestError(
            "TEST_ONLY_PRIVATE_DETAIL",
            retryable=True,
            reason_code="provider_network_unavailable",
        ),
    )
    service = SportsSyncService(
        session,  # type: ignore[arg-type]
        app_settings=_settings(),
        client=client,  # type: ignore[arg-type]
    )
    repository = FakeRepository()
    service.repository = repository  # type: ignore[assignment]

    summary = asyncio.run(
        service._sync_daily_window(
            sync_type="daily_discovery",
            starts_on=TARGET_DATE,
            days=1,
            started_at=NOW,
        )
    )

    assert summary.status == "FAILED"
    assert summary.public_error_code == "provider_unavailable"
    assert summary.fixture_dates_requested == 1
    assert summary.fixture_dates_succeeded == 0
    assert summary.fixture_dates_failed == 1
    assert summary.provider_unavailable_causes == (
        "provider_network_unavailable",
    )
    assert "TEST_ONLY_PRIVATE_DETAIL" not in repr(summary)
    assert repository.errors[0]["context"] == {
        "cause": "provider_network_unavailable"
    }


def test_daily_discovery_fails_closed_when_provider_is_disabled() -> None:
    service = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(),
        client=DisabledClient({}),  # type: ignore[arg-type]
    )

    with pytest.raises(ApiFootballDisabledError):
        asyncio.run(
            service._sync_daily_window(
                sync_type="daily_discovery",
                starts_on=TARGET_DATE,
                days=1,
                started_at=NOW,
            )
        )


def test_daily_refresh_rejects_unbounded_windows_before_provider_access() -> None:
    client = FakeClient({})
    service = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(),
        client=client,  # type: ignore[arg-type]
    )

    with pytest.raises(SportsSyncConfigurationError) as caught:
        asyncio.run(service.daily_refresh(days=8))

    assert caught.value.public_code == "daily_refresh_window_invalid"
    assert client.request_count == 0


def test_upcoming_reports_exact_missing_runtime_configuration() -> None:
    missing_season = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(),
        client=FakeClient({}),  # type: ignore[arg-type]
    )
    with pytest.raises(SportsSyncConfigurationError) as season_error:
        asyncio.run(missing_season.sync_upcoming(days=30))
    assert season_error.value.public_code == "api_football_season_missing"

    missing_competitions = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(
            priority_competitions="",
            season=SEASON,
        ),
        client=FakeClient({}),  # type: ignore[arg-type]
    )
    with pytest.raises(SportsSyncConfigurationError) as competition_error:
        asyncio.run(missing_competitions.sync_upcoming(days=30))
    assert (
        competition_error.value.public_code
        == "api_football_priority_competitions_missing"
    )


def test_cli_preserves_exact_synchronization_configuration_code(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def fail_with_exact_code(_args: object) -> None:
        raise SportsSyncConfigurationError(
            "api_football_season_missing"
        )

    monkeypatch.setattr(sports_sync, "run_command", fail_with_exact_code)

    assert sports_sync.main(["upcoming", "--days", "30"]) == 4
    captured = capsys.readouterr()
    assert "api_football_season_missing" in captured.err
    assert "synchronization_configuration_invalid" not in captured.err


def test_upcoming_uses_an_inclusive_thirty_day_scoped_range() -> None:
    client = FakeClient(
        {"fixtures": [_envelope("fixtures", [], "upcoming-empty")]}
    )
    service = SportsSyncService(
        FakeSession(),  # type: ignore[arg-type]
        app_settings=_settings(season=SEASON),
        client=client,  # type: ignore[arg-type]
    )
    repository = FakeRepository()
    service.repository = repository  # type: ignore[assignment]

    summary = asyncio.run(service.sync_upcoming(days=30))

    assert summary.status == "SUCCEEDED"
    assert summary.records_received == 0
    assert len(client.requests) == 1
    endpoint, params = client.requests[0]
    assert endpoint == "fixtures"
    assert params["league"] == 39
    assert params["season"] == SEASON
    starts_on = date.fromisoformat(str(params["from"]))
    ends_on = date.fromisoformat(str(params["to"]))
    assert (ends_on - starts_on).days == 29


def test_statistics_selection_is_recent_and_fair_across_teams() -> None:
    rows = (
        {
            "provider_match_id": 1,
            "kickoff_at": NOW - timedelta(days=1),
            "home_team_provider_id": HOME_ID,
            "away_team_provider_id": 9001,
        },
        {
            "provider_match_id": 2,
            "kickoff_at": NOW - timedelta(days=2),
            "home_team_provider_id": AWAY_ID,
            "away_team_provider_id": 9002,
        },
        {
            "provider_match_id": 3,
            "kickoff_at": NOW - timedelta(days=3),
            "home_team_provider_id": HOME_ID,
            "away_team_provider_id": 9003,
        },
    )

    selected = select_recent_matches_for_statistics(
        rows,
        target_team_ids=(HOME_ID, AWAY_ID),
        limit=2,
    )

    assert selected == (1, 2)
