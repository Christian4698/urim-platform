from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

from app.modules.sports_data.normalization import NormalizationResult

MAX_DISCOVERY_COMPETITIONS: Final = 5
MINIMUM_RECENT_RESULTS_PER_TEAM: Final = 3
RECENT_RESULTS_LOOKBACK_DAYS: Final = 60
SCHEDULED_FIXTURE_STATUSES: Final = frozenset({"NS"})
RETENTION_FUNNEL_FIELDS: Final = (
    "fixtures_received",
    "retained",
    "rejected_competition",
    "rejected_season",
    "rejected_status",
    "rejected_kickoff_window",
    "rejected_missing_teams",
    "rejected_insufficient_coverage",
    "rejected_duplicate",
    "rejected_other",
)


@dataclass(frozen=True)
class RetentionFunnel:
    fixtures_received: int
    retained: int
    rejected_competition: int
    rejected_season: int
    rejected_status: int
    rejected_kickoff_window: int
    rejected_missing_teams: int
    rejected_insufficient_coverage: int
    rejected_duplicate: int
    rejected_other: int

    def __post_init__(self) -> None:
        values = tuple(getattr(self, field) for field in RETENTION_FUNNEL_FIELDS)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in values
        ):
            raise ValueError("Retention funnel counts must be non-negative integers.")
        rejected = sum(
            getattr(self, field)
            for field in RETENTION_FUNNEL_FIELDS
            if field.startswith("rejected_")
        )
        if self.fixtures_received != self.retained + rejected:
            raise ValueError("Retention funnel counts must reconcile exactly.")

    def as_dict(self) -> dict[str, int]:
        return {
            field: getattr(self, field)
            for field in RETENTION_FUNNEL_FIELDS
        }


@dataclass(frozen=True)
class DiscoveryCompetition:
    provider_competition_id: int
    season: int
    supports_standings: bool
    supports_fixture_statistics: bool
    supports_fixture_events: bool
    fixture_rows: tuple[Mapping[str, Any], ...]

    @property
    def enrichment_request_cost(self) -> int:
        return 2 + int(self.supports_standings)


@dataclass(frozen=True)
class DiscoveryPlan:
    competitions: tuple[DiscoveryCompetition, ...]
    ignored_reasons: Mapping[str, int]

    @property
    def fixture_rows(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            row
            for competition in self.competitions
            for row in competition.fixture_rows
        )


@dataclass(frozen=True)
class DailyDiscoverySummary:
    run_id: str
    sync_type: str
    status: str
    target_date: str
    days: int
    request_count: int
    fixture_dates_requested: int
    fixture_dates_succeeded: int
    fixture_dates_failed: int
    fixtures_received: int
    fixtures_retained: int
    fixtures_ignored: int
    ignored_reasons: Mapping[str, int]
    retention_funnel: RetentionFunnel
    competitions_selected: int
    competitions_added: int
    seasons_added: int
    teams_added: int
    standings_rows_available: int
    recent_results_received: int
    target_matches_added: int
    recent_results_added: int
    match_duplicates: int
    statistics_matches_available: int
    statistics_matches_unavailable: int
    statistics_matches_skipped_quota: int
    statistics_rows_added: int
    goal_event_matches_available: int
    goal_event_matches_unavailable: int
    goal_event_rows_added: int
    h2h_requests: int
    h2h_matches_received: int
    h2h_matches_added: int
    h2h_duplicates: int
    quota_remaining_daily: int | None
    quota_remaining_minute: int | None
    provider_unavailable_causes: tuple[str, ...]
    public_error_code: str | None
    runtime_configuration: Mapping[str, bool]


def build_discovery_plan(
    fixtures: NormalizationResult,
    competitions: NormalizationResult,
    seasons: NormalizationResult,
    *,
    priority_competitions: Sequence[int],
    enrichment_request_budget: int,
    as_of: datetime,
    max_competitions: int = MAX_DISCOVERY_COMPETITIONS,
    window_starts_at: datetime | None = None,
    window_ends_at: datetime | None = None,
) -> DiscoveryPlan:
    if enrichment_request_budget < 0:
        raise ValueError("enrichment_request_budget must be non-negative.")
    if max_competitions < 1 or max_competitions > MAX_DISCOVERY_COMPETITIONS:
        raise ValueError("max_competitions is outside the safe range.")
    if as_of.tzinfo is None or as_of.tzinfo.utcoffset(as_of) is None:
        raise ValueError("as_of must be timezone-aware.")
    if (window_starts_at is None) != (window_ends_at is None):
        raise ValueError("Both discovery window bounds are required together.")
    if window_starts_at is not None and window_ends_at is not None:
        if (
            window_starts_at.tzinfo is None
            or window_starts_at.tzinfo.utcoffset(window_starts_at) is None
            or window_ends_at.tzinfo is None
            or window_ends_at.tzinfo.utcoffset(window_ends_at) is None
        ):
            raise ValueError("Discovery window bounds must be timezone-aware.")
        if window_starts_at >= window_ends_at:
            raise ValueError("Discovery window bounds are invalid.")

    ignored: Counter[str] = Counter()
    if fixtures.rejected_count:
        explained_rejections = sum(
            value
            for value in fixtures.rejection_reasons.values()
            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and value > 0
            )
        )
        ignored.update(fixtures.rejection_reasons)
        if explained_rejections < fixtures.rejected_count:
            ignored["invalid_fixture"] += (
                fixtures.rejected_count - explained_rejections
            )

    competition_index = {
        int(row["provider_competition_id"]): row
        for row in competitions.rows
        if isinstance(row.get("provider_competition_id"), int)
    }
    season_index = {
        (int(row["provider_competition_id"]), int(row["year"])): row
        for row in seasons.rows
        if isinstance(row.get("provider_competition_id"), int)
        and isinstance(row.get("year"), int)
    }
    grouped: dict[tuple[int, int], list[Mapping[str, Any]]] = {}
    capability_index: dict[tuple[int, int], tuple[bool, bool, bool]] = {}

    for row in fixtures.rows:
        if row.get("status_short") not in SCHEDULED_FIXTURE_STATUSES:
            ignored["fixture_status_not_scheduled"] += 1
            continue
        kickoff_at = row.get("kickoff_at")
        if not isinstance(kickoff_at, datetime) or kickoff_at <= as_of:
            ignored["fixture_not_future"] += 1
            continue
        if (
            window_starts_at is not None
            and window_ends_at is not None
            and not window_starts_at <= kickoff_at < window_ends_at
        ):
            ignored["fixture_outside_requested_window"] += 1
            continue
        competition_id = row.get("provider_competition_id")
        season = row.get("season")
        if not isinstance(competition_id, int) or not isinstance(season, int):
            ignored["fixture_identity_invalid"] += 1
            continue
        competition = competition_index.get(competition_id)
        season_row = season_index.get((competition_id, season))
        if competition is None:
            ignored["competition_metadata_unavailable"] += 1
            continue
        if season_row is None:
            ignored["season_metadata_unavailable"] += 1
            continue
        if str(competition.get("kind") or "").strip().lower() != "league":
            ignored["competition_type_unsupported"] += 1
            continue

        coverage = season_row.get("coverage")
        supports_standings = _coverage_flag(coverage, "standings")
        supports_statistics = _fixture_coverage_flag(
            coverage,
            "statistics_fixtures",
        )
        supports_events = _fixture_coverage_flag(coverage, "events")
        if not supports_standings and not supports_statistics:
            ignored["insufficient_data_coverage"] += 1
            continue

        key = (competition_id, season)
        grouped.setdefault(key, []).append(row)
        capability_index[key] = (
            supports_standings,
            supports_statistics,
            supports_events,
        )

    priority_rank = {
        competition_id: index
        for index, competition_id in enumerate(priority_competitions)
    }
    candidates = [
        DiscoveryCompetition(
            provider_competition_id=competition_id,
            season=season,
            supports_standings=capability_index[(competition_id, season)][0],
            supports_fixture_statistics=capability_index[
                (competition_id, season)
            ][1],
            supports_fixture_events=capability_index[
                (competition_id, season)
            ][2],
            fixture_rows=tuple(rows),
        )
        for (competition_id, season), rows in grouped.items()
    ]
    candidates.sort(
        key=lambda candidate: (
            0
            if candidate.provider_competition_id in priority_rank
            else 1,
            priority_rank.get(
                candidate.provider_competition_id,
                len(priority_rank),
            ),
            not candidate.supports_fixture_statistics,
            not candidate.supports_standings,
            -len(candidate.fixture_rows),
            candidate.provider_competition_id,
        )
    )

    selected: list[DiscoveryCompetition] = []
    remaining_budget = enrichment_request_budget
    for candidate in candidates:
        if len(selected) >= max_competitions:
            ignored["competition_limit"] += len(candidate.fixture_rows)
            continue
        cost = candidate.enrichment_request_cost
        reserve_for_statistics = 1 if selected else 0
        if cost + reserve_for_statistics > remaining_budget:
            ignored["request_budget_competition_limit"] += len(
                candidate.fixture_rows
            )
            continue
        selected.append(candidate)
        remaining_budget -= cost

    return DiscoveryPlan(
        competitions=tuple(selected),
        ignored_reasons=dict(sorted(ignored.items())),
    )


def build_retention_funnel(
    *,
    fixtures_received: int,
    retained: int,
    ignored_reasons: Mapping[str, int],
) -> RetentionFunnel:
    if (
        isinstance(fixtures_received, bool)
        or not isinstance(fixtures_received, int)
        or fixtures_received < 0
        or isinstance(retained, bool)
        or not isinstance(retained, int)
        or retained < 0
        or retained > fixtures_received
    ):
        raise ValueError("Retention funnel inputs are invalid.")

    remaining = fixtures_received - retained

    def allocate(*reason_codes: str) -> int:
        nonlocal remaining
        requested = sum(
            value
            for reason in reason_codes
            if (
                isinstance((value := ignored_reasons.get(reason)), int)
                and not isinstance(value, bool)
                and value > 0
            )
        )
        accepted = min(requested, remaining)
        remaining -= accepted
        return accepted

    rejected_competition = allocate(
        "fixture_competition_invalid",
        "competition_metadata_unavailable",
        "competition_type_unsupported",
        "competition_limit",
        "request_budget_competition_limit",
    )
    rejected_season = allocate(
        "fixture_season_invalid",
        "season_metadata_unavailable",
    )
    rejected_status = allocate(
        "fixture_status_invalid",
        "fixture_status_not_scheduled",
    )
    rejected_kickoff_window = allocate(
        "fixture_kickoff_invalid",
        "fixture_not_future",
        "fixture_outside_requested_window",
    )
    rejected_missing_teams = allocate(
        "fixture_missing_teams",
        "fixture_identity_invalid",
        "team_metadata_unavailable",
    )
    rejected_insufficient_coverage = allocate(
        "insufficient_data_coverage",
        "recent_results_unavailable",
        "insufficient_recent_results",
    )
    rejected_duplicate = allocate("duplicate_fixture")

    return RetentionFunnel(
        fixtures_received=fixtures_received,
        retained=retained,
        rejected_competition=rejected_competition,
        rejected_season=rejected_season,
        rejected_status=rejected_status,
        rejected_kickoff_window=rejected_kickoff_window,
        rejected_missing_teams=rejected_missing_teams,
        rejected_insufficient_coverage=rejected_insufficient_coverage,
        rejected_duplicate=rejected_duplicate,
        rejected_other=remaining,
    )


def select_recent_matches_for_statistics(
    rows: Sequence[Mapping[str, Any]],
    *,
    target_team_ids: Sequence[int],
    limit: int,
) -> tuple[int, ...]:
    if limit < 0:
        raise ValueError("limit must be non-negative.")
    if limit == 0:
        return ()

    ordered = sorted(
        (
            row
            for row in rows
            if isinstance(row.get("provider_match_id"), int)
            and isinstance(row.get("kickoff_at"), datetime)
        ),
        key=lambda row: (
            row["kickoff_at"],
            int(row["provider_match_id"]),
        ),
        reverse=True,
    )
    selected: list[int] = []
    selected_set: set[int] = set()
    team_rows = {
        team_id: [
            row
            for row in ordered
            if team_id
            in {
                row.get("home_team_provider_id"),
                row.get("away_team_provider_id"),
            }
        ]
        for team_id in sorted(set(target_team_ids))
    }
    offset = 0
    while len(selected) < limit:
        found = False
        for team_id in sorted(team_rows):
            candidates = team_rows[team_id]
            if offset >= len(candidates):
                continue
            found = True
            match_id = int(candidates[offset]["provider_match_id"])
            if match_id not in selected_set:
                selected.append(match_id)
                selected_set.add(match_id)
                if len(selected) == limit:
                    break
        if not found:
            break
        offset += 1
    return tuple(selected)


def _coverage_flag(coverage: object, key: str) -> bool:
    return isinstance(coverage, Mapping) and coverage.get(key) is True


def _fixture_coverage_flag(coverage: object, key: str) -> bool:
    if not isinstance(coverage, Mapping):
        return False
    fixture_coverage = coverage.get("fixtures")
    return (
        isinstance(fixture_coverage, Mapping)
        and fixture_coverage.get(key) is True
    )


__all__ = [
    "DailyDiscoverySummary",
    "DiscoveryCompetition",
    "DiscoveryPlan",
    "MAX_DISCOVERY_COMPETITIONS",
    "MINIMUM_RECENT_RESULTS_PER_TEAM",
    "RECENT_RESULTS_LOOKBACK_DAYS",
    "RETENTION_FUNNEL_FIELDS",
    "RetentionFunnel",
    "build_discovery_plan",
    "build_retention_funnel",
    "select_recent_matches_for_statistics",
]
