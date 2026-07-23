from datetime import UTC, datetime, timedelta

from app.modules.sports_data.normalization import (
    normalize_fixtures,
    normalize_injuries,
    normalize_leagues,
    normalize_lineups,
    normalize_match_events,
    normalize_match_statistics,
    normalize_standings,
    normalize_teams,
)
from app.modules.sports_data.provider import (
    ApiFootballEnvelope,
    ApiFootballEnvelopeModel,
)


def envelope(endpoint: str, rows: list[object]) -> ApiFootballEnvelope:
    fetched_at = datetime(2026, 7, 23, 10, 0, tzinfo=UTC)
    return ApiFootballEnvelope(
        endpoint=endpoint,
        request_id="test-request",
        fetched_at=fetched_at,
        observed_at=fetched_at - timedelta(seconds=1),
        available_at=fetched_at,
        source_version="football-v3",
        raw_hash="a" * 64,
        data=ApiFootballEnvelopeModel(
            get=endpoint,
            parameters={},
            errors=[],
            results=len(rows),
            paging={"current": 1, "total": 1},
            response=rows,
        ),
    )


def assert_provenance(row: dict[str, object]) -> None:
    required = {
        "provider",
        "provider_event_id",
        "observed_at",
        "available_at",
        "fetched_at",
        "source_version",
        "quality_flags",
        "raw_hash",
        "freshness_status",
    }
    assert required <= row.keys()
    assert row["provider"] == "api-football"
    assert row["raw_hash"] == "a" * 64
    assert "RAW_PAYLOAD_NOT_STORED" in row["quality_flags"]


def test_normalizes_competitions_seasons_and_teams_without_media() -> None:
    competition_result, season_result = normalize_leagues(
        envelope(
            "leagues",
            [
                {
                    "league": {
                        "id": 39,
                        "name": "Competition Test",
                        "type": "League",
                        "logo": "https://media.invalid/logo.png",
                    },
                    "country": {
                        "name": "Test Country",
                        "code": "TC",
                        "flag": "https://media.invalid/flag.svg",
                    },
                    "seasons": [
                        {
                            "year": 2026,
                            "start": "2026-08-01",
                            "end": "2027-05-31",
                            "current": True,
                            "coverage": {"fixtures": {"events": True}},
                        }
                    ],
                }
            ],
        )
    )
    team_result = normalize_teams(
        envelope(
            "teams",
            [
                {
                    "team": {
                        "id": 1,
                        "name": "Team Test",
                        "code": None,
                        "country": "Test Country",
                        "founded": None,
                        "national": False,
                        "logo": "https://media.invalid/team.png",
                    },
                    "venue": None,
                }
            ],
        )
    )

    assert competition_result.rejected_count == 0
    assert season_result.rejected_count == 0
    assert team_result.rejected_count == 0
    assert competition_result.rows[0]["current_season"] == 2026
    assert season_result.rows[0]["is_current"] is True
    assert team_result.rows[0]["code"] is None
    assert "logo" not in competition_result.rows[0]
    assert "logo" not in team_result.rows[0]
    assert_provenance(competition_result.rows[0])
    assert_provenance(season_result.rows[0])
    assert_provenance(team_result.rows[0])


def test_normalizes_fixture_missing_scores_as_none() -> None:
    result = normalize_fixtures(
        envelope(
            "fixtures",
            [
                {
                    "fixture": {
                        "id": 10,
                        "date": "2026-07-23T14:00:00+00:00",
                        "timezone": "UTC",
                        "status": {"short": "NS", "long": "Not Started", "elapsed": None},
                        "venue": None,
                    },
                    "league": {"id": 39, "season": 2026, "round": "Round 1"},
                    "teams": {
                        "home": {"id": 1, "name": "Home Test"},
                        "away": {"id": 2, "name": "Away Test"},
                    },
                    "goals": {"home": None, "away": None},
                    "score": {"halftime": {}, "fulltime": {}},
                }
            ],
        )
    )

    assert result.rejected_count == 0
    assert result.rows[0]["goals_home"] is None
    assert result.rows[0]["score_fulltime_home"] is None
    assert_provenance(result.rows[0])


def test_normalizes_standings_statistics_events_lineups_and_injuries() -> None:
    standings = normalize_standings(
        envelope(
            "standings",
            [
                {
                    "league": {
                        "id": 39,
                        "season": 2026,
                        "standings": [
                            [
                                {
                                    "rank": 1,
                                    "team": {"id": 1, "name": "Team Test"},
                                    "points": 3,
                                    "goalsDiff": 1,
                                    "group": "League",
                                    "all": {
                                        "played": 1,
                                        "win": 1,
                                        "draw": 0,
                                        "lose": 0,
                                        "goals": {"for": 2, "against": 1},
                                    },
                                }
                            ]
                        ],
                    }
                }
            ],
        )
    )
    statistics = normalize_match_statistics(
        envelope(
            "fixtures/statistics",
            [
                {
                    "team": {"id": 1, "name": "Team Test"},
                    "statistics": [{"type": "Ball Possession", "value": "51%"}],
                }
            ],
        ),
        10,
    )
    events = normalize_match_events(
        envelope(
            "fixtures/events",
            [
                {
                    "time": {"elapsed": 12, "extra": None},
                    "team": {"id": 1, "name": "Team Test"},
                    "player": {"id": 100, "name": "Player Test"},
                    "assist": {"id": None, "name": None},
                    "type": "Card",
                    "detail": "Yellow Card",
                    "comments": None,
                }
            ],
        ),
        10,
    )
    lineups = normalize_lineups(
        envelope(
            "fixtures/lineups",
            [
                {
                    "team": {"id": 1, "name": "Team Test"},
                    "formation": "4-3-3",
                    "coach": {"id": 5, "name": "Coach Test"},
                    "startXI": [
                        {
                            "player": {
                                "id": 100,
                                "name": "Player Test",
                                "number": 1,
                                "pos": "G",
                                "grid": "1:1",
                            }
                        }
                    ],
                    "substitutes": [],
                }
            ],
        ),
        10,
    )
    injuries = normalize_injuries(
        envelope(
            "injuries",
            [
                {
                    "fixture": {"id": 10},
                    "league": {"id": 39, "season": 2026},
                    "team": {"id": 1, "name": "Team Test"},
                    "player": {
                        "id": 100,
                        "name": "Player Test",
                        "type": "Questionable",
                        "reason": None,
                    },
                }
            ],
        )
    )

    for result in (standings, statistics, events, lineups, injuries):
        assert result.rejected_count == 0
        assert result.rows
        assert_provenance(result.rows[0])
    assert statistics.rows[0]["statistic_value"] == "51%"
    assert lineups.rows[0]["role"] == "start_xi"
    assert injuries.rows[0]["reason"] is None


def test_invalid_rows_are_rejected_without_invented_fallbacks() -> None:
    result = normalize_fixtures(
        envelope(
            "fixtures",
            [
                {
                    "fixture": {"id": 0},
                    "league": {},
                    "teams": {},
                }
            ],
        )
    )
    assert result.rows == ()
    assert result.rejected_count == 1
    assert result.error_codes == ("invalid_matches_row",)


def test_temporal_order_is_blocking() -> None:
    invalid = envelope("fixtures", [])
    invalid.observed_at = invalid.fetched_at + timedelta(minutes=1)
    invalid.data.response = [
        {
            "fixture": {
                "id": 10,
                "date": "2026-07-23T14:00:00+00:00",
                "timezone": "UTC",
                "status": {"short": "NS", "long": "Not Started"},
            },
            "league": {"id": 39, "season": 2026},
            "teams": {
                "home": {"id": 1, "name": "Home Test"},
                "away": {"id": 2, "name": "Away Test"},
            },
        }
    ]
    result = normalize_fixtures(invalid)
    assert result.rows == ()
    assert result.rejected_count == 1
