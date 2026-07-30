from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, Final

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db import models
from app.modules.kairos.models import (
    API_FOOTBALL_PROVIDER,
    COMPLETED_HISTORY_STATUSES,
    EventObservation,
    KairosMatchDataset,
    MAX_QUALITY_FLAGS,
    MatchObservation,
    SourceObservation,
    StandingObservation,
    StatisticObservation,
)

COMPLETED_MATCH_STATUSES: Final = tuple(
    sorted(COMPLETED_HISTORY_STATUSES)
)
HISTORY_QUERY_MULTIPLIER: Final = 4
MAX_RECENT_WINDOW: Final = 25
MAX_DAILY_TARGET_MATCHES: Final = 16
MAX_KAIROS_EVENTS_PER_MATCH: Final = 96
# Compatibility name retained for existing B2.2 contract tests. The query now
# includes bounded goal events in addition to cards.
MAX_CARD_EVENTS_PER_MATCH: Final = MAX_KAIROS_EVENTS_PER_MATCH
MAX_H2H_MATCHES: Final = 10
KAIROS_STATISTIC_TYPES: Final = (
    "ball possession",
    "corner kicks",
    "corners",
    "possession",
    "red card",
    "red cards",
    "shots on goal",
    "shots on target",
    "shots total",
    "total shots",
    "yellow card",
    "yellow cards",
)


class KairosRepository:
    """Read-only access to B1 observations for one reproducible analysis."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def load_match_dataset(
        self,
        provider_match_id: int,
        *,
        as_of: datetime,
        recent_window: int,
    ) -> KairosMatchDataset | None:
        if recent_window < 1 or recent_window > MAX_RECENT_WINDOW:
            raise ValueError("recent_window is outside the safe range.")
        target = self._match_as_of(provider_match_id, as_of=as_of)
        if target is None:
            return None
        return self.load_match_dataset_for_target(
            target,
            as_of=as_of,
            recent_window=recent_window,
        )

    def load_match_dataset_for_target(
        self,
        target: MatchObservation,
        *,
        as_of: datetime,
        recent_window: int,
    ) -> KairosMatchDataset:
        if recent_window < 1 or recent_window > MAX_RECENT_WINDOW:
            raise ValueError("recent_window is outside the safe range.")

        history_limit = recent_window * HISTORY_QUERY_MULTIPLIER
        home_history = self._team_history(
            target.home_team_provider_id,
            target=target,
            as_of=as_of,
            limit=history_limit,
        )
        away_history = self._team_history(
            target.away_team_provider_id,
            target=target,
            as_of=as_of,
            limit=history_limit,
        )
        feature_match_ids = sorted(
            {
                match.provider_match_id
                for match in (
                    *home_history[:recent_window],
                    *away_history[:recent_window],
                )
            }
        )
        team_ids = (
            target.home_team_provider_id,
            target.away_team_provider_id,
        )

        return KairosMatchDataset(
            as_of=as_of,
            target=target,
            home_history=home_history,
            away_history=away_history,
            standings=self._standings_as_of(
                target=target,
                team_ids=team_ids,
                as_of=as_of,
            ),
            statistics=self._statistics_as_of(
                match_ids=feature_match_ids,
                team_ids=team_ids,
                as_of=as_of,
            ),
            events=self._card_events_as_of(
                match_ids=feature_match_ids,
                team_ids=team_ids,
                as_of=as_of,
            ),
            h2h_history=self._h2h_history(
                target=target,
                as_of=as_of,
                limit=MAX_H2H_MATCHES,
            ),
        )

    def list_target_matches_as_of(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
        as_of: datetime,
        limit: int = MAX_DAILY_TARGET_MATCHES,
    ) -> tuple[MatchObservation, ...]:
        if starts_at.tzinfo is None or ends_at.tzinfo is None:
            raise ValueError("Daily target bounds must be timezone-aware.")
        if starts_at >= ends_at:
            raise ValueError("Daily target bounds are invalid.")
        if limit < 1 or limit > MAX_DAILY_TARGET_MATCHES:
            raise ValueError("Daily target limit is outside the safe range.")

        table = models.api_football_matches
        latest = build_latest_as_of_subquery(
            table,
            (table.c.provider_match_id,),
            as_of=as_of,
            scope_filters=(
                table.c.kickoff_at >= starts_at,
                table.c.kickoff_at < ends_at,
            ),
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.kickoff_at >= starts_at,
                latest.c.kickoff_at < ends_at,
                latest.c.kickoff_at > as_of,
                latest.c.status_short.in_(("NS", "TBD")),
            )
            .order_by(
                latest.c.kickoff_at,
                latest.c.provider_match_id,
            )
            .limit(limit)
        )
        return tuple(
            _match_from_row(row)
            for row in self.session.execute(statement).mappings()
        )

    def _match_as_of(
        self,
        provider_match_id: int,
        *,
        as_of: datetime,
    ) -> MatchObservation | None:
        table = models.api_football_matches
        latest = build_latest_as_of_subquery(
            table,
            (table.c.provider_match_id,),
            as_of=as_of,
            scope_filters=(
                table.c.provider_match_id == provider_match_id,
            ),
        )
        statement = sa.select(latest).where(
            latest.c.observation_rank == 1,
            latest.c.provider_match_id == provider_match_id,
        )
        row = self.session.execute(statement).mappings().first()
        return _match_from_row(row) if row else None

    def _team_history(
        self,
        team_id: int,
        *,
        target: MatchObservation,
        as_of: datetime,
        limit: int,
    ) -> tuple[MatchObservation, ...]:
        table = models.api_football_matches
        candidate_match_ids = sa.select(table.c.provider_match_id).where(
            table.c.provider == API_FOOTBALL_PROVIDER,
            table.c.available_at <= as_of,
            table.c.fetched_at <= as_of,
            table.c.created_at <= as_of,
            table.c.provider_competition_id
            == target.provider_competition_id,
            table.c.season == target.season,
            table.c.kickoff_at < as_of,
            table.c.kickoff_at < target.kickoff_at,
            table.c.status_short.in_(COMPLETED_MATCH_STATUSES),
            sa.or_(
                table.c.home_team_provider_id == team_id,
                table.c.away_team_provider_id == team_id,
            ),
        )
        latest = build_latest_as_of_subquery(
            table,
            (table.c.provider_match_id,),
            as_of=as_of,
            scope_filters=(
                table.c.provider_match_id.in_(candidate_match_ids),
            ),
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.provider_match_id != target.provider_match_id,
                latest.c.provider_competition_id
                == target.provider_competition_id,
                latest.c.season == target.season,
                latest.c.kickoff_at < as_of,
                latest.c.kickoff_at < target.kickoff_at,
                latest.c.status_short.in_(COMPLETED_MATCH_STATUSES),
                sa.or_(
                    latest.c.home_team_provider_id == team_id,
                    latest.c.away_team_provider_id == team_id,
                ),
            )
            .order_by(
                latest.c.kickoff_at.desc(),
                latest.c.provider_match_id.desc(),
            )
            .limit(limit)
        )
        return tuple(
            _match_from_row(row)
            for row in self.session.execute(statement).mappings()
        )

    def _standings_as_of(
        self,
        *,
        target: MatchObservation,
        team_ids: Sequence[int],
        as_of: datetime,
    ) -> tuple[StandingObservation, ...]:
        table = models.api_football_standings
        latest = build_latest_as_of_subquery(
            table,
            (
                table.c.provider_competition_id,
                table.c.season,
                table.c.provider_team_id,
            ),
            as_of=as_of,
            scope_filters=(
                table.c.provider_competition_id
                == target.provider_competition_id,
                table.c.season == target.season,
                table.c.provider_team_id.in_(team_ids),
            ),
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.provider_competition_id
                == target.provider_competition_id,
                latest.c.season == target.season,
                latest.c.provider_team_id.in_(team_ids),
            )
            .order_by(latest.c.provider_team_id)
        )
        return tuple(
            _standing_from_row(row)
            for row in self.session.execute(statement).mappings()
        )

    def _h2h_history(
        self,
        *,
        target: MatchObservation,
        as_of: datetime,
        limit: int,
    ) -> tuple[MatchObservation, ...]:
        if not isinstance(target, MatchObservation):
            return ()
        table = models.api_football_matches
        team_ids = (
            target.home_team_provider_id,
            target.away_team_provider_id,
        )
        candidate_match_ids = sa.select(table.c.provider_match_id).where(
            table.c.provider == API_FOOTBALL_PROVIDER,
            table.c.available_at <= as_of,
            table.c.fetched_at <= as_of,
            table.c.created_at <= as_of,
            table.c.provider_competition_id
            == target.provider_competition_id,
            table.c.kickoff_at < as_of,
            table.c.kickoff_at < target.kickoff_at,
            table.c.status_short.in_(COMPLETED_MATCH_STATUSES),
            table.c.home_team_provider_id.in_(team_ids),
            table.c.away_team_provider_id.in_(team_ids),
        )
        latest = build_latest_as_of_subquery(
            table,
            (table.c.provider_match_id,),
            as_of=as_of,
            scope_filters=(table.c.provider_match_id.in_(candidate_match_ids),),
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.provider_match_id != target.provider_match_id,
                latest.c.provider_competition_id
                == target.provider_competition_id,
                latest.c.kickoff_at < as_of,
                latest.c.kickoff_at < target.kickoff_at,
                latest.c.status_short.in_(COMPLETED_MATCH_STATUSES),
                latest.c.home_team_provider_id.in_(team_ids),
                latest.c.away_team_provider_id.in_(team_ids),
            )
            .order_by(
                latest.c.kickoff_at.desc(),
                latest.c.provider_match_id.desc(),
            )
            .limit(limit)
        )
        return tuple(
            _match_from_row(row)
            for row in self.session.execute(statement).mappings()
        )

    def _statistics_as_of(
        self,
        *,
        match_ids: Sequence[int],
        team_ids: Sequence[int],
        as_of: datetime,
    ) -> tuple[StatisticObservation, ...]:
        if not match_ids:
            return ()
        table = models.api_football_match_statistics
        latest = build_latest_as_of_subquery(
            table,
            (
                table.c.provider_match_id,
                table.c.provider_team_id,
                table.c.statistic_type,
            ),
            as_of=as_of,
            scope_filters=(
                table.c.provider_match_id.in_(match_ids),
                table.c.provider_team_id.in_(team_ids),
                sa.func.lower(sa.func.trim(table.c.statistic_type)).in_(
                    KAIROS_STATISTIC_TYPES
                ),
            ),
        )
        row_limit = (
            len(match_ids)
            * len(team_ids)
            * len(KAIROS_STATISTIC_TYPES)
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.provider_match_id.in_(match_ids),
                latest.c.provider_team_id.in_(team_ids),
                sa.func.lower(sa.func.trim(latest.c.statistic_type)).in_(
                    KAIROS_STATISTIC_TYPES
                ),
            )
            .order_by(
                latest.c.provider_match_id,
                latest.c.provider_team_id,
                latest.c.statistic_type,
            )
            .limit(row_limit)
        )
        return tuple(
            _statistic_from_row(row)
            for row in self.session.execute(statement).mappings()
        )

    def _card_events_as_of(
        self,
        *,
        match_ids: Sequence[int],
        team_ids: Sequence[int],
        as_of: datetime,
    ) -> tuple[EventObservation, ...]:
        if not match_ids:
            return ()
        table = models.api_football_match_events
        latest = build_latest_as_of_subquery(
            table,
            (table.c.provider_event_id,),
            as_of=as_of,
            scope_filters=(
                table.c.provider_match_id.in_(match_ids),
                table.c.provider_team_id.in_(team_ids),
                sa.func.lower(table.c.event_type).in_(("card", "goal")),
            ),
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.provider_match_id.in_(match_ids),
                latest.c.provider_team_id.in_(team_ids),
                sa.func.lower(latest.c.event_type).in_(("card", "goal")),
            )
            .order_by(latest.c.provider_match_id, latest.c.provider_event_id)
            .limit(len(match_ids) * MAX_KAIROS_EVENTS_PER_MATCH)
        )
        return tuple(
            _event_from_row(row)
            for row in self.session.execute(statement).mappings()
        )


def build_latest_as_of_subquery(
    table: sa.Table,
    identity_columns: Sequence[sa.Column],
    *,
    as_of: datetime,
    scope_filters: Sequence[Any] = (),
) -> sa.Subquery:
    """Return the latest locally persisted observation available at ``as_of``."""

    return (
        sa.select(
            table,
            sa.func.row_number()
            .over(
                partition_by=tuple(identity_columns),
                order_by=(
                    table.c.available_at.desc(),
                    table.c.fetched_at.desc(),
                    table.c.created_at.desc(),
                ),
            )
            .label("observation_rank"),
        )
        .where(
            table.c.provider == API_FOOTBALL_PROVIDER,
            table.c.available_at <= as_of,
            table.c.fetched_at <= as_of,
            table.c.created_at <= as_of,
            *scope_filters,
        )
        .subquery()
    )


def _source_from_row(row: Mapping[str, Any]) -> SourceObservation:
    quality_flags = row.get("quality_flags")
    if quality_flags is None:
        flags: tuple[str, ...] = ()
    elif (
        not isinstance(quality_flags, list | tuple)
        or len(quality_flags) > MAX_QUALITY_FLAGS
        or any(not isinstance(flag, str) for flag in quality_flags)
    ):
        raise ValueError("Kairos expected bounded string quality flags.")
    else:
        flags = tuple(quality_flags)
    return SourceObservation(
        observation_id=str(row["id"]),
        provider=str(row["provider"]),
        provider_event_id=str(row["provider_event_id"]),
        observed_at=_datetime(row["observed_at"]),
        available_at=_datetime(row["available_at"]),
        fetched_at=_datetime(row["fetched_at"]),
        created_at=_datetime(row["created_at"]),
        source_version=str(row["source_version"]),
        quality_flags=flags,
        raw_hash=str(row["raw_hash"]),
        freshness_status=str(row["freshness_status"]),
    )


def _match_from_row(row: Mapping[str, Any]) -> MatchObservation:
    return MatchObservation(
        source=_source_from_row(row),
        provider_match_id=int(row["provider_match_id"]),
        provider_competition_id=int(row["provider_competition_id"]),
        season=int(row["season"]),
        kickoff_at=_datetime(row["kickoff_at"]),
        status_short=str(row["status_short"]).upper(),
        home_team_provider_id=int(row["home_team_provider_id"]),
        home_team_name=str(row["home_team_name"]),
        away_team_provider_id=int(row["away_team_provider_id"]),
        away_team_name=str(row["away_team_name"]),
        goals_home=_optional_int(row.get("goals_home")),
        goals_away=_optional_int(row.get("goals_away")),
        score_fulltime_home=_optional_int(row.get("score_fulltime_home")),
        score_fulltime_away=_optional_int(row.get("score_fulltime_away")),
        score_halftime_home=_optional_int(row.get("score_halftime_home")),
        score_halftime_away=_optional_int(row.get("score_halftime_away")),
    )


def _standing_from_row(row: Mapping[str, Any]) -> StandingObservation:
    return StandingObservation(
        source=_source_from_row(row),
        provider_team_id=int(row["provider_team_id"]),
        rank=int(row["rank"]),
        points=_optional_int(row.get("points")),
        played=_optional_int(row.get("played")),
        goals_diff=_optional_int(row.get("goals_diff")),
    )


def _statistic_from_row(row: Mapping[str, Any]) -> StatisticObservation:
    return StatisticObservation(
        source=_source_from_row(row),
        provider_match_id=int(row["provider_match_id"]),
        provider_team_id=int(row["provider_team_id"]),
        statistic_type=str(row["statistic_type"]),
        statistic_value=row.get("statistic_value"),
    )


def _event_from_row(row: Mapping[str, Any]) -> EventObservation:
    return EventObservation(
        source=_source_from_row(row),
        provider_match_id=int(row["provider_match_id"]),
        provider_team_id=_optional_int(row.get("provider_team_id")),
        event_type=str(row["event_type"]),
        detail=str(row["detail"]) if row.get("detail") is not None else None,
        elapsed=_optional_int(row.get("elapsed")),
        extra=_optional_int(row.get("extra")),
    )


def _datetime(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("Kairos expected a database datetime.")
    return value


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    return int(value)


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "COMPLETED_MATCH_STATUSES",
    "KairosRepository",
    "build_latest_as_of_subquery",
]
