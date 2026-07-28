from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Final


API_FOOTBALL_PROVIDER: Final = "api-football"
MAX_REASONABLE_GOALS_PER_TEAM: Final = 100
COMPLETED_HISTORY_STATUSES: Final = frozenset({"FT", "AET", "PEN"})
MAX_OBSERVATION_ID_LENGTH: Final = 80
MAX_PROVIDER_EVENT_ID_LENGTH: Final = 240
MAX_SOURCE_VERSION_LENGTH: Final = 80
MAX_QUALITY_FLAGS: Final = 32
MAX_QUALITY_FLAG_LENGTH: Final = 160
VALID_FRESHNESS_STATUSES: Final = frozenset({"fresh", "stale", "unknown"})
SHA256_HEX_PATTERN: Final = re.compile(r"^[0-9a-fA-F]{64}$")


class KairosDataError(RuntimeError):
    """Base error for a dataset that cannot safely be analysed."""


class KairosTemporalIntegrityError(KairosDataError):
    """Raised when an observation is not valid for the requested as-of time."""


class KairosPreMatchWindowClosedError(KairosDataError):
    """Raised when a request would mix pre-match and live/post-match data."""


@dataclass(frozen=True, slots=True)
class SourceObservation:
    observation_id: str
    provider: str
    provider_event_id: str
    observed_at: datetime
    available_at: datetime
    fetched_at: datetime
    created_at: datetime
    source_version: str
    quality_flags: tuple[str, ...]
    raw_hash: str
    freshness_status: str


@dataclass(frozen=True, slots=True)
class MatchObservation:
    source: SourceObservation
    provider_match_id: int
    provider_competition_id: int
    season: int
    kickoff_at: datetime
    status_short: str
    home_team_provider_id: int
    home_team_name: str
    away_team_provider_id: int
    away_team_name: str
    goals_home: int | None
    goals_away: int | None
    score_fulltime_home: int | None
    score_fulltime_away: int | None

    def fulltime_score(self) -> tuple[int, int] | None:
        candidates = (
            (self.score_fulltime_home, self.score_fulltime_away),
            (self.goals_home, self.goals_away),
        )
        for home_score, away_score in candidates:
            if (
                home_score is not None
                and away_score is not None
                and 0 <= home_score <= MAX_REASONABLE_GOALS_PER_TEAM
                and 0 <= away_score <= MAX_REASONABLE_GOALS_PER_TEAM
            ):
                return home_score, away_score
        return None

    def score_for(self, team_id: int) -> tuple[int, int] | None:
        score = self.fulltime_score()
        if score is None:
            return None
        home_score, away_score = score
        if team_id == self.home_team_provider_id:
            return home_score, away_score
        if team_id == self.away_team_provider_id:
            return away_score, home_score
        return None


@dataclass(frozen=True, slots=True)
class StandingObservation:
    source: SourceObservation
    provider_team_id: int
    rank: int
    points: int | None
    played: int | None
    goals_diff: int | None


@dataclass(frozen=True, slots=True)
class StatisticObservation:
    source: SourceObservation
    provider_match_id: int
    provider_team_id: int
    statistic_type: str
    statistic_value: Any


@dataclass(frozen=True, slots=True)
class EventObservation:
    source: SourceObservation
    provider_match_id: int
    provider_team_id: int | None
    event_type: str
    detail: str | None


@dataclass(frozen=True, slots=True)
class KairosMatchDataset:
    as_of: datetime
    target: MatchObservation
    home_history: tuple[MatchObservation, ...]
    away_history: tuple[MatchObservation, ...]
    standings: tuple[StandingObservation, ...]
    statistics: tuple[StatisticObservation, ...]
    events: tuple[EventObservation, ...]

    def source_observations(self) -> tuple[SourceObservation, ...]:
        sources = [self.target.source]
        sources.extend(match.source for match in self.home_history)
        sources.extend(match.source for match in self.away_history)
        sources.extend(standing.source for standing in self.standings)
        sources.extend(statistic.source for statistic in self.statistics)
        sources.extend(event.source for event in self.events)
        unique: dict[str, SourceObservation] = {}
        for source in sources:
            existing = unique.get(source.observation_id)
            if existing is not None and existing != source:
                raise KairosDataError(
                    "conflicting_source_observation_identity"
                )
            unique[source.observation_id] = source
        return tuple(unique[key] for key in sorted(unique))

    def validate_data_integrity(self) -> None:
        target = self.target
        if (
            target.provider_match_id <= 0
            or target.provider_competition_id <= 0
            or target.home_team_provider_id <= 0
            or target.away_team_provider_id <= 0
            or target.home_team_provider_id == target.away_team_provider_id
        ):
            raise KairosDataError("invalid_target_identity")

        history = (*self.home_history, *self.away_history)
        if any(
            match.provider_competition_id != target.provider_competition_id
            or match.season != target.season
            for match in history
        ):
            raise KairosDataError("history_scope_mismatch")
        if any(
            target.home_team_provider_id
            not in (
                match.home_team_provider_id,
                match.away_team_provider_id,
            )
            for match in self.home_history
        ):
            raise KairosDataError("home_history_team_mismatch")
        if any(
            target.away_team_provider_id
            not in (
                match.home_team_provider_id,
                match.away_team_provider_id,
            )
            for match in self.away_history
        ):
            raise KairosDataError("away_history_team_mismatch")
        if any(
            match.status_short not in COMPLETED_HISTORY_STATUSES
            for match in history
        ):
            raise KairosDataError("history_match_not_completed")

        expected_team_ids = {
            target.home_team_provider_id,
            target.away_team_provider_id,
        }
        history_match_ids = {
            match.provider_match_id for match in history
        }
        if any(
            standing.provider_team_id not in expected_team_ids
            for standing in self.standings
        ):
            raise KairosDataError("standing_scope_mismatch")
        if any(
            statistic.provider_match_id not in history_match_ids
            or statistic.provider_team_id not in expected_team_ids
            for statistic in self.statistics
        ):
            raise KairosDataError("statistic_scope_mismatch")
        if any(
            event.provider_match_id not in history_match_ids
            or (
                event.provider_team_id is not None
                and event.provider_team_id not in expected_team_ids
            )
            for event in self.events
        ):
            raise KairosDataError("event_scope_mismatch")

        for source in self.source_observations():
            if source.provider != API_FOOTBALL_PROVIDER:
                raise KairosDataError("unexpected_source_provider")
            string_fields = (
                source.observation_id,
                source.provider_event_id,
                source.source_version,
            )
            if any(
                not isinstance(value, str) or not value.strip()
                for value in string_fields
            ):
                raise KairosDataError("incomplete_source_provenance")
            if (
                len(source.observation_id) > MAX_OBSERVATION_ID_LENGTH
                or len(source.provider_event_id)
                > MAX_PROVIDER_EVENT_ID_LENGTH
                or len(source.source_version) > MAX_SOURCE_VERSION_LENGTH
                or not isinstance(source.quality_flags, tuple)
                or len(source.quality_flags) > MAX_QUALITY_FLAGS
                or any(
                    not isinstance(flag, str)
                    or not flag.strip()
                    or len(flag) > MAX_QUALITY_FLAG_LENGTH
                    for flag in source.quality_flags
                )
                or source.freshness_status not in VALID_FRESHNESS_STATUSES
            ):
                raise KairosDataError("invalid_source_provenance_shape")
            if (
                not isinstance(source.raw_hash, str)
                or SHA256_HEX_PATTERN.fullmatch(source.raw_hash) is None
            ):
                raise KairosDataError("invalid_source_raw_hash")

    def validate_temporal_integrity(self) -> None:
        if not _is_timezone_aware(self.as_of):
            raise KairosTemporalIntegrityError("as_of_must_be_timezone_aware")
        if not _is_timezone_aware(self.target.kickoff_at):
            raise KairosTemporalIntegrityError("kickoff_must_be_timezone_aware")
        if self.as_of >= self.target.kickoff_at:
            raise KairosPreMatchWindowClosedError("pre_match_window_closed")

        target_id = self.target.provider_match_id
        if any(
            match.provider_match_id == target_id
            for match in (*self.home_history, *self.away_history)
        ):
            raise KairosTemporalIntegrityError("target_match_leaked_into_history")

        for match in (*self.home_history, *self.away_history):
            if not _is_timezone_aware(match.kickoff_at):
                raise KairosTemporalIntegrityError(
                    "history_kickoff_must_be_timezone_aware"
                )
            if match.kickoff_at >= self.as_of:
                raise KairosTemporalIntegrityError(
                    "future_history_match_detected"
                )

        for source in self.source_observations():
            if not _is_timezone_aware(source.observed_at):
                raise KairosTemporalIntegrityError("observed_at_must_be_aware")
            if not _is_timezone_aware(source.available_at):
                raise KairosTemporalIntegrityError("available_at_must_be_aware")
            if not _is_timezone_aware(source.fetched_at):
                raise KairosTemporalIntegrityError("fetched_at_must_be_aware")
            if not _is_timezone_aware(source.created_at):
                raise KairosTemporalIntegrityError("created_at_must_be_aware")
            if source.available_at > self.as_of:
                raise KairosTemporalIntegrityError(
                    "future_available_observation_detected"
                )
            if source.fetched_at > self.as_of:
                raise KairosTemporalIntegrityError(
                    "future_fetched_observation_detected"
                )
            if source.created_at > self.as_of:
                raise KairosTemporalIntegrityError(
                    "future_persisted_observation_detected"
                )
            if not (
                source.observed_at
                <= source.available_at
                <= source.fetched_at
                <= source.created_at
            ):
                raise KairosTemporalIntegrityError(
                    "observation_temporal_order_invalid"
                )


def _is_timezone_aware(value: datetime) -> bool:
    try:
        return (
            isinstance(value, datetime)
            and value.tzinfo is not None
            and value.utcoffset() is not None
        )
    except (AttributeError, OverflowError, ValueError):
        return False


@dataclass(frozen=True, slots=True)
class TeamFeatureProfile:
    team_id: int
    team_name: str
    result_sample_size: int
    venue_sample_size: int
    form_points_per_game: float | None
    goals_for_average: float | None
    goals_against_average: float | None
    venue_points_per_game: float | None
    venue_goals_for_average: float | None
    venue_goals_against_average: float | None
    shots_average: float | None
    shots_sample_size: int
    possession_average: float | None
    possession_sample_size: int
    corners_average: float | None
    corners_sample_size: int
    cards_average: float | None
    cards_sample_size: int
    standing_rank: int | None
    standing_points_per_game: float | None


__all__ = [
    "API_FOOTBALL_PROVIDER",
    "EventObservation",
    "KairosDataError",
    "KairosMatchDataset",
    "KairosPreMatchWindowClosedError",
    "KairosTemporalIntegrityError",
    "MatchObservation",
    "SourceObservation",
    "StandingObservation",
    "StatisticObservation",
    "TeamFeatureProfile",
]
