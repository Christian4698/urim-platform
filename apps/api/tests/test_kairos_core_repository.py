from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any, cast

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.db import models
from app.modules.kairos.repository import (
    KAIROS_STATISTIC_TYPES,
    MAX_CARD_EVENTS_PER_MATCH,
    MAX_DAILY_TARGET_MATCHES,
    KairosRepository,
    build_latest_as_of_subquery,
)


class RecordingSession:
    def __init__(self) -> None:
        self.statement: Any = None

    def execute(self, statement: Any) -> SimpleNamespace:
        self.statement = statement
        return SimpleNamespace(mappings=lambda: ())


def test_latest_as_of_query_enforces_all_temporal_boundaries() -> None:
    as_of = datetime(2026, 7, 27, 12, tzinfo=UTC)
    latest = build_latest_as_of_subquery(
        models.api_football_matches,
        (models.api_football_matches.c.provider_match_id,),
        as_of=as_of,
    )
    sql = str(
        sa.select(latest).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    ).lower()

    assert "api_football_matches.available_at <=" in sql
    assert "api_football_matches.fetched_at <=" in sql
    assert "api_football_matches.created_at <=" in sql
    assert "api_football_matches.provider =" in sql
    assert "row_number() over" in sql
    assert "partition by api_football_matches.provider_match_id" in sql


def test_kairos_queries_are_select_only_and_use_no_prediction_or_odds_table() -> None:
    latest = build_latest_as_of_subquery(
        models.api_football_match_statistics,
        (
            models.api_football_match_statistics.c.provider_match_id,
            models.api_football_match_statistics.c.provider_team_id,
            models.api_football_match_statistics.c.statistic_type,
        ),
        as_of=datetime(2026, 7, 27, 12, tzinfo=UTC),
    )
    sql = str(
        sa.select(latest).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    ).lower()

    assert sql.lstrip().startswith("select")
    assert " insert " not in f" {sql} "
    assert " update " not in f" {sql} "
    assert " delete " not in f" {sql} "
    assert "predictions" not in sql
    assert "odds" not in sql


def test_provider_match_id_is_bound_and_never_interpolated_into_sql() -> None:
    payload = "1 UNION SELECT pg_sleep(10)"
    table = models.api_football_matches
    latest = build_latest_as_of_subquery(
        table,
        (table.c.provider_match_id,),
        as_of=datetime(2026, 7, 27, 12, tzinfo=UTC),
        scope_filters=(table.c.provider_match_id == payload,),
    )
    compiled = sa.select(latest).compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )

    assert payload not in str(compiled)
    assert payload in compiled.params.values()


def test_history_query_excludes_matches_kicking_off_at_or_after_as_of() -> None:
    as_of = datetime(2026, 7, 27, 12, tzinfo=UTC)
    session = RecordingSession()
    repository = KairosRepository(cast(Session, session))
    target = SimpleNamespace(
        provider_match_id=999,
        provider_competition_id=39,
        season=2026,
        kickoff_at=datetime(2026, 7, 28, 12, tzinfo=UTC),
    )

    result = repository._team_history(
        10,
        target=target,
        as_of=as_of,
        limit=20,
    )

    assert result == ()
    compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    sql = str(compiled).lower()
    assert sql.count("kickoff_at <") >= 2
    assert as_of in compiled.params.values()
    assert target.kickoff_at in compiled.params.values()


def test_statistics_and_card_event_queries_have_hard_row_bounds() -> None:
    as_of = datetime(2026, 7, 27, 12, tzinfo=UTC)
    session = RecordingSession()
    repository = KairosRepository(cast(Session, session))

    assert repository._statistics_as_of(
        match_ids=(1, 2, 3),
        team_ids=(10, 20),
        as_of=as_of,
    ) == ()
    statistics_compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    statistics_sql = str(statistics_compiled).lower()
    assert "lower(trim(" in statistics_sql
    assert " limit " in f" {statistics_sql} "
    assert (
        3 * 2 * len(KAIROS_STATISTIC_TYPES)
        in statistics_compiled.params.values()
    )

    assert repository._card_events_as_of(
        match_ids=(1, 2, 3),
        team_ids=(10, 20),
        as_of=as_of,
    ) == ()
    events_compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    events_sql = str(events_compiled).lower()
    assert " limit " in f" {events_sql} "
    assert (
        3 * MAX_CARD_EVENTS_PER_MATCH
        in events_compiled.params.values()
    )


def test_dataset_load_fetches_statistics_only_for_the_feature_window(
    monkeypatch,
) -> None:
    as_of = datetime(2026, 7, 27, 12, tzinfo=UTC)
    target = SimpleNamespace(
        home_team_provider_id=10,
        away_team_provider_id=20,
        provider_competition_id=39,
        season=2026,
    )
    home_history = tuple(
        SimpleNamespace(provider_match_id=100 + index)
        for index in range(20)
    )
    away_history = tuple(
        SimpleNamespace(provider_match_id=200 + index)
        for index in range(20)
    )
    captured: list[tuple[int, ...]] = []
    repository = KairosRepository(cast(Session, object()))
    monkeypatch.setattr(
        repository,
        "_match_as_of",
        lambda provider_match_id, as_of: target,
    )
    histories = iter((home_history, away_history))
    monkeypatch.setattr(
        repository,
        "_team_history",
        lambda team_id, target, as_of, limit: next(histories),
    )
    monkeypatch.setattr(
        repository,
        "_standings_as_of",
        lambda target, team_ids, as_of: (),
    )

    def capture_match_ids(*, match_ids, team_ids, as_of):
        captured.append(tuple(match_ids))
        return ()

    monkeypatch.setattr(repository, "_statistics_as_of", capture_match_ids)
    monkeypatch.setattr(repository, "_card_events_as_of", capture_match_ids)

    dataset = repository.load_match_dataset(
        999,
        as_of=as_of,
        recent_window=5,
    )

    assert dataset is not None
    assert captured == [
        (100, 101, 102, 103, 104, 200, 201, 202, 203, 204),
        (100, 101, 102, 103, 104, 200, 201, 202, 203, 204),
    ]


def test_daily_target_query_is_temporal_select_only_and_bounded() -> None:
    as_of = datetime(2026, 7, 27, 8, tzinfo=UTC)
    starts_at = datetime(2026, 7, 26, 23, tzinfo=UTC)
    ends_at = datetime(2026, 7, 27, 23, tzinfo=UTC)
    session = RecordingSession()
    repository = KairosRepository(cast(Session, session))

    assert (
        repository.list_target_matches_as_of(
            starts_at=starts_at,
            ends_at=ends_at,
            as_of=as_of,
        )
        == ()
    )
    compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": False},
    )
    sql = str(compiled).lower()

    assert sql.lstrip().startswith("select")
    assert "available_at <=" in sql
    assert "fetched_at <=" in sql
    assert "created_at <=" in sql
    assert "kickoff_at >" in sql
    assert "status_short in" in sql
    assert " limit " in f" {sql} "
    assert MAX_DAILY_TARGET_MATCHES in compiled.params.values()
    assert " insert " not in f" {sql} "
    assert " update " not in f" {sql} "
    assert " delete " not in f" {sql} "
