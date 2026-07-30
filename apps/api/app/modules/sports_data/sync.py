from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.modules.sports_data.discovery import (
    DailyDiscoverySummary,
    DiscoveryCompetition,
    MINIMUM_RECENT_RESULTS_PER_TEAM,
    RECENT_RESULTS_LOOKBACK_DAYS,
    build_discovery_plan,
    select_recent_matches_for_statistics,
)
from app.modules.sports_data.normalization import (
    NormalizationResult,
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
    ApiFootballClient,
    ApiFootballDisabledError,
    ApiFootballEnvelope,
    ApiFootballRequestBudgetError,
    ApiFootballRequestError,
)
from app.modules.sports_data.repository import SportsRepository

logger = logging.getLogger("urim.sports_data.sync")
MAX_H2H_ENRICHMENT_REQUESTS = 5
MIN_LOCAL_H2H_BEFORE_PROVIDER_REQUEST = 3
MAX_H2H_MATCHES_PER_PAIR = 5
BLOCKING_DISCOVERY_FAILURE_CAUSES = frozenset(
    {
        "daily_quota_exhausted",
        "provider_http_unavailable",
        "provider_network_unavailable",
        "provider_rate_limited",
        "provider_retry_exhausted",
        "sync_request_budget_exhausted",
    }
)
PUBLIC_SYNC_CONFIGURATION_CODES = frozenset(
    {
        "api_football_priority_competitions_missing",
        "api_football_season_invalid",
        "api_football_season_missing",
        "daily_discovery_date_out_of_range",
        "daily_refresh_window_invalid",
        "match_window_invalid",
        "results_window_invalid",
        "sports_database_url_missing",
        "statistics_window_invalid",
        "upcoming_window_invalid",
    }
)


class SportsSyncConfigurationError(ValueError):
    def __init__(self, public_code: str) -> None:
        if public_code not in PUBLIC_SYNC_CONFIGURATION_CODES:
            raise ValueError(
                "Unknown public synchronization configuration code."
            )
        super().__init__(public_code)
        self.public_code = public_code


@dataclass(frozen=True)
class SyncSummary:
    run_id: str
    sync_type: str
    status: str
    request_count: int
    records_received: int
    records_inserted: int
    records_duplicate: int
    records_rejected: int
    public_error_code: str | None


@dataclass(frozen=True)
class RequestSpec:
    endpoint: str
    params: Mapping[str, str | int | bool]
    normalize: Callable[[ApiFootballEnvelope], Sequence[NormalizationResult]]


@dataclass
class _DiscoveryRunState:
    records_received: int = 0
    records_inserted: int = 0
    records_duplicate: int = 0
    records_rejected: int = 0
    fixture_dates_requested: int = 0
    fixture_dates_succeeded: int = 0
    fixture_dates_failed: int = 0
    fixtures_received: int = 0
    competitions_added: int = 0
    seasons_added: int = 0
    teams_added: int = 0
    standings_rows_available: int = 0
    recent_results_received: int = 0
    target_matches_added: int = 0
    recent_results_added: int = 0
    match_duplicates: int = 0
    statistics_matches_available: int = 0
    statistics_matches_unavailable: int = 0
    statistics_matches_skipped_quota: int = 0
    statistics_rows_added: int = 0
    goal_event_matches_available: int = 0
    goal_event_matches_unavailable: int = 0
    goal_event_rows_added: int = 0
    h2h_requests: int = 0
    h2h_matches_received: int = 0
    h2h_matches_added: int = 0
    h2h_duplicates: int = 0
    error_codes: list[str] = field(default_factory=list)
    provider_unavailable_causes: list[str] = field(default_factory=list)
    ignored_reasons: Counter[str] = field(default_factory=Counter)
    last_quota: ApiFootballEnvelope | None = None


class SportsSyncService:
    def __init__(
        self,
        session: Session,
        *,
        app_settings: Settings = settings,
        client: ApiFootballClient | None = None,
    ) -> None:
        self.session = session
        self.settings = app_settings
        self.repository = SportsRepository(session)
        self.client = client or ApiFootballClient.from_settings(app_settings)

    async def daily_discovery(
        self,
        target_date: date,
    ) -> DailyDiscoverySummary:
        now = datetime.now(UTC)
        if target_date < now.date() or target_date > now.date() + timedelta(days=30):
            raise SportsSyncConfigurationError(
                "daily_discovery_date_out_of_range"
            )
        return await self._sync_daily_window(
            sync_type="daily_discovery",
            starts_on=target_date,
            days=1,
            started_at=now,
        )

    async def daily_refresh(self, *, days: int = 7) -> DailyDiscoverySummary:
        if days < 1 or days > 7:
            raise SportsSyncConfigurationError(
                "daily_refresh_window_invalid"
            )
        now = datetime.now(UTC)
        return await self._sync_daily_window(
            sync_type="daily_refresh",
            starts_on=now.date(),
            days=days,
            started_at=now,
        )

    async def _sync_daily_window(
        self,
        *,
        sync_type: str,
        starts_on: date,
        days: int,
        started_at: datetime,
    ) -> DailyDiscoverySummary:
        if not self.client.enabled:
            raise ApiFootballDisabledError(
                "Le fournisseur sportif est désactivé par configuration."
            )
        if started_at.tzinfo is None or started_at.tzinfo.utcoffset(started_at) is None:
            raise ValueError("started_at must be timezone-aware.")

        ends_on = starts_on + timedelta(days=days - 1)
        provider_id = self.repository.ensure_provider(enabled=True)
        run_id = self.repository.start_run(
            provider_id=provider_id,
            sync_type=sync_type,
            scope={
                "starts_on": starts_on.isoformat(),
                "ends_on": ends_on.isoformat(),
                "days": days,
                "discovery_scope": "all_provider_competitions",
                "quality_filter": "kairos_minimum_v1",
            },
            started_at=started_at,
        )
        self.session.commit()

        state = _DiscoveryRunState()
        final_competitions: list[DiscoveryCompetition] = []
        final_fixture_rows: list[Mapping[str, Any]] = []
        statistic_history_rows: list[Mapping[str, Any]] = []
        statistic_team_ids: set[int] = set()
        all_history_rows: list[Mapping[str, Any]] = []
        event_competition_ids: set[int] = set()
        fatal_error = False

        try:
            async with self.client:
                fixture_rows: list[dict[str, Any]] = []
                fixture_rejected = 0
                fixture_error_codes: list[str] = []
                for day_offset in range(days):
                    fixture_date = starts_on + timedelta(days=day_offset)
                    state.fixture_dates_requested += 1
                    fixture_envelope = await self._discovery_request(
                        endpoint="fixtures",
                        params={
                            "date": fixture_date.isoformat(),
                            "timezone": "UTC",
                        },
                        run_id=run_id,
                        state=state,
                    )
                    if fixture_envelope is None:
                        state.fixture_dates_failed += 1
                        if (
                            state.provider_unavailable_causes
                            and state.provider_unavailable_causes[-1]
                            in BLOCKING_DISCOVERY_FAILURE_CAUSES
                        ):
                            break
                        continue
                    state.fixture_dates_succeeded += 1
                    state.fixtures_received += fixture_envelope.data.results
                    date_result = normalize_fixtures(fixture_envelope)
                    self._record_normalization_errors(
                        date_result,
                        endpoint="fixtures",
                        run_id=run_id,
                        state=state,
                    )
                    fixture_rows.extend(date_result.rows)
                    fixture_rejected += date_result.rejected_count
                    fixture_error_codes.extend(date_result.error_codes)
                fixture_rows.sort(
                    key=lambda row: (
                        row.get("kickoff_at"),
                        row.get("provider_match_id"),
                    )
                )
                fixture_result = NormalizationResult(
                    resource="matches",
                    rows=tuple(fixture_rows),
                    rejected_count=fixture_rejected,
                    error_codes=tuple(fixture_error_codes),
                )

                league_envelope = None
                if fixture_result.rows:
                    league_envelope = await self._discovery_request(
                        endpoint="leagues",
                        params={"current": True},
                        run_id=run_id,
                        state=state,
                    )

                if league_envelope is not None:
                    competition_result, season_result = normalize_leagues(
                        league_envelope
                    )
                    self._record_normalization_errors(
                        competition_result,
                        endpoint="leagues",
                        run_id=run_id,
                        state=state,
                    )
                    plan = build_discovery_plan(
                        fixture_result,
                        competition_result,
                        season_result,
                        priority_competitions=(
                            self.settings.api_football_priority_competition_ids
                        ),
                        enrichment_request_budget=(
                            self._remaining_discovery_requests()
                        ),
                        as_of=started_at,
                    )
                    state.ignored_reasons.update(plan.ignored_reasons)

                    for competition in plan.competitions:
                        cause_count_before = len(
                            state.provider_unavailable_causes
                        )
                        outcome = await self._enrich_discovery_competition(
                            competition=competition,
                            competition_result=competition_result,
                            season_result=season_result,
                            started_at=started_at,
                            run_id=run_id,
                            provider_id=provider_id,
                            state=state,
                        )
                        if outcome is None:
                            if (
                                len(state.provider_unavailable_causes)
                                > cause_count_before
                                and state.provider_unavailable_causes[-1]
                                in BLOCKING_DISCOVERY_FAILURE_CAUSES
                            ):
                                break
                            continue
                        (
                            retained_fixtures,
                            recent_rows,
                            target_team_ids,
                        ) = outcome
                        final_competitions.append(competition)
                        final_fixture_rows.extend(retained_fixtures)
                        all_history_rows.extend(recent_rows)
                        if competition.supports_fixture_statistics:
                            statistic_history_rows.extend(recent_rows)
                            statistic_team_ids.update(target_team_ids)
                        if competition.supports_fixture_events:
                            event_competition_ids.add(
                                competition.provider_competition_id
                            )
                elif fixture_result.rows:
                    state.ignored_reasons[
                        "competition_metadata_unavailable"
                    ] += len(fixture_result.rows)

                await self._enrich_missing_h2h(
                    target_rows=final_fixture_rows,
                    history_rows=all_history_rows,
                    started_at=started_at,
                    provider_id=provider_id,
                    run_id=run_id,
                    state=state,
                )

                all_statistic_match_ids = (
                    select_recent_matches_for_statistics(
                        statistic_history_rows,
                        target_team_ids=tuple(statistic_team_ids),
                        limit=len(statistic_history_rows),
                    )
                )
                event_match_ids = {
                    int(row["provider_match_id"])
                    for row in statistic_history_rows
                    if row.get("provider_competition_id")
                    in event_competition_ids
                    and isinstance(row.get("provider_match_id"), int)
                }
                per_match_cost = 2 if event_match_ids else 1
                statistics_limit = (
                    self._remaining_discovery_requests() // per_match_cost
                )
                statistic_match_ids = all_statistic_match_ids[
                    :statistics_limit
                ]
                state.statistics_matches_skipped_quota = max(
                    0,
                    len(all_statistic_match_ids) - len(statistic_match_ids),
                )
                for match_id in statistic_match_ids:
                    envelope = await self._discovery_request(
                        endpoint="fixtures/statistics",
                        params={"fixture": match_id},
                        run_id=run_id,
                        state=state,
                    )
                    if envelope is None:
                        break
                    result = normalize_match_statistics(envelope, match_id)
                    self._record_normalization_errors(
                        result,
                        endpoint="fixtures/statistics",
                        run_id=run_id,
                        state=state,
                    )
                    if not result.rows:
                        state.statistics_matches_unavailable += 1
                        continue
                    state.statistics_matches_available += 1
                    inserted, _ = self._insert_discovery_rows(
                        result,
                        provider_id=provider_id,
                        run_id=run_id,
                        state=state,
                    )
                    state.statistics_rows_added += inserted
                    self.session.commit()
                    if (
                        match_id in event_match_ids
                        and self._remaining_discovery_requests() > 0
                    ):
                        event_envelope = await self._discovery_request(
                            endpoint="fixtures/events",
                            params={"fixture": match_id},
                            run_id=run_id,
                            state=state,
                        )
                        if event_envelope is None:
                            state.goal_event_matches_unavailable += 1
                            continue
                        event_result = normalize_match_events(
                            event_envelope,
                            match_id,
                        )
                        self._record_normalization_errors(
                            event_result,
                            endpoint="fixtures/events",
                            run_id=run_id,
                            state=state,
                        )
                        goal_rows = tuple(
                            row
                            for row in event_result.rows
                            if str(row.get("event_type") or "").lower()
                            == "goal"
                        )
                        if not goal_rows:
                            state.goal_event_matches_unavailable += 1
                            continue
                        state.goal_event_matches_available += 1
                        inserted, _ = self._insert_discovery_rows(
                            NormalizationResult(
                                resource="match_events",
                                rows=goal_rows,
                            ),
                            provider_id=provider_id,
                            run_id=run_id,
                            state=state,
                        )
                        state.goal_event_rows_added += inserted
                        self.session.commit()
        except Exception as exc:
            self.session.rollback()
            fatal_error = True
            state.error_codes.append("synchronization_internal_error")
            logger.error(
                "Daily sports discovery failed safely type=%s",
                type(exc).__name__,
            )
            self.repository.record_error(
                run_id=run_id,
                endpoint="daily_discovery",
                error_code="synchronization_internal_error",
                retryable=True,
                occurred_at=datetime.now(UTC),
                context={"cause": "internal_error"},
            )
            self.session.commit()

        fixtures_retained = len(final_fixture_rows)
        fixtures_ignored = max(0, state.fixtures_received - fixtures_retained)
        status = (
            "FAILED"
            if fatal_error
            or (
                state.provider_unavailable_causes
                and fixtures_retained == 0
            )
            else "PARTIAL"
            if state.error_codes or state.records_rejected
            else "SUCCEEDED"
        )
        public_error_code = (
            state.error_codes[0] if state.error_codes else None
        )
        unavailable_causes = tuple(
            dict.fromkeys(state.provider_unavailable_causes)
        )
        checkpoint = {
            "fixture_dates_requested": state.fixture_dates_requested,
            "fixture_dates_succeeded": state.fixture_dates_succeeded,
            "fixture_dates_failed": state.fixture_dates_failed,
            "fixtures_received": state.fixtures_received,
            "fixtures_retained": fixtures_retained,
            "fixtures_ignored": fixtures_ignored,
            "ignored_reasons": dict(sorted(state.ignored_reasons.items())),
            "competitions_selected": len(final_competitions),
            "statistics_matches_available": (
                state.statistics_matches_available
            ),
            "statistics_matches_unavailable": (
                state.statistics_matches_unavailable
            ),
            "statistics_matches_skipped_quota": (
                state.statistics_matches_skipped_quota
            ),
            "goal_event_matches_available": (
                state.goal_event_matches_available
            ),
            "goal_event_matches_unavailable": (
                state.goal_event_matches_unavailable
            ),
            "goal_event_rows_added": state.goal_event_rows_added,
            "h2h_requests": state.h2h_requests,
            "h2h_matches_received": state.h2h_matches_received,
            "h2h_matches_added": state.h2h_matches_added,
            "h2h_duplicates": state.h2h_duplicates,
            "provider_unavailable_causes": unavailable_causes,
            "runtime_configuration": self._runtime_configuration_status(),
        }
        self.repository.finish_run(
            run_id=run_id,
            status=status,
            completed_at=datetime.now(UTC),
            request_count=self.client.request_count,
            records_received=state.records_received,
            records_inserted=state.records_inserted,
            records_duplicate=state.records_duplicate,
            records_rejected=state.records_rejected,
            quota_limit_daily=(
                state.last_quota.quota_limit_daily
                if state.last_quota
                else None
            ),
            quota_remaining_daily=self.client.quota_remaining_daily,
            quota_limit_minute=(
                state.last_quota.quota_limit_minute
                if state.last_quota
                else None
            ),
            quota_remaining_minute=self.client.quota_remaining_minute,
            checkpoint=checkpoint,
            public_error_code=public_error_code,
        )
        self.session.commit()
        return DailyDiscoverySummary(
            run_id=str(run_id),
            sync_type=sync_type,
            status=status,
            target_date=starts_on.isoformat(),
            days=days,
            request_count=self.client.request_count,
            fixture_dates_requested=state.fixture_dates_requested,
            fixture_dates_succeeded=state.fixture_dates_succeeded,
            fixture_dates_failed=state.fixture_dates_failed,
            fixtures_received=state.fixtures_received,
            fixtures_retained=fixtures_retained,
            fixtures_ignored=fixtures_ignored,
            ignored_reasons=dict(sorted(state.ignored_reasons.items())),
            competitions_selected=len(final_competitions),
            competitions_added=state.competitions_added,
            seasons_added=state.seasons_added,
            teams_added=state.teams_added,
            standings_rows_available=state.standings_rows_available,
            recent_results_received=state.recent_results_received,
            target_matches_added=state.target_matches_added,
            recent_results_added=state.recent_results_added,
            match_duplicates=state.match_duplicates,
            statistics_matches_available=state.statistics_matches_available,
            statistics_matches_unavailable=(
                state.statistics_matches_unavailable
            ),
            statistics_matches_skipped_quota=(
                state.statistics_matches_skipped_quota
            ),
            statistics_rows_added=state.statistics_rows_added,
            goal_event_matches_available=(
                state.goal_event_matches_available
            ),
            goal_event_matches_unavailable=(
                state.goal_event_matches_unavailable
            ),
            goal_event_rows_added=state.goal_event_rows_added,
            h2h_requests=state.h2h_requests,
            h2h_matches_received=state.h2h_matches_received,
            h2h_matches_added=state.h2h_matches_added,
            h2h_duplicates=state.h2h_duplicates,
            quota_remaining_daily=self.client.quota_remaining_daily,
            quota_remaining_minute=self.client.quota_remaining_minute,
            provider_unavailable_causes=unavailable_causes,
            public_error_code=public_error_code,
            runtime_configuration=self._runtime_configuration_status(),
        )

    async def _enrich_missing_h2h(
        self,
        *,
        target_rows: Sequence[Mapping[str, Any]],
        history_rows: Sequence[Mapping[str, Any]],
        started_at: datetime,
        provider_id: UUID,
        run_id: UUID,
        state: _DiscoveryRunState,
    ) -> None:
        unique_targets: dict[tuple[int, int, int], Mapping[str, Any]] = {}
        for row in target_rows:
            home_id = row.get("home_team_provider_id")
            away_id = row.get("away_team_provider_id")
            competition_id = row.get("provider_competition_id")
            if not all(
                isinstance(value, int)
                for value in (home_id, away_id, competition_id)
            ):
                continue
            pair = tuple(sorted((int(home_id), int(away_id))))
            unique_targets[(int(competition_id), *pair)] = row

        for (competition_id, first_team_id, second_team_id), _row in sorted(
            unique_targets.items()
        ):
            if state.h2h_requests >= MAX_H2H_ENRICHMENT_REQUESTS:
                break
            local_count = sum(
                1
                for history in history_rows
                if history.get("provider_competition_id") == competition_id
                and {
                    history.get("home_team_provider_id"),
                    history.get("away_team_provider_id"),
                }
                == {first_team_id, second_team_id}
                and history.get("status_short") in {"FT", "AET", "PEN"}
            )
            if local_count >= MIN_LOCAL_H2H_BEFORE_PROVIDER_REQUEST:
                continue
            if self._remaining_discovery_requests() <= 0:
                break
            state.h2h_requests += 1
            envelope = await self._discovery_request(
                endpoint="fixtures/headtohead",
                params={
                    "h2h": f"{first_team_id}-{second_team_id}",
                    "league": competition_id,
                    "last": MAX_H2H_MATCHES_PER_PAIR,
                    "status": "FT-AET-PEN",
                    "timezone": "UTC",
                },
                run_id=run_id,
                state=state,
            )
            if envelope is None:
                continue
            result = normalize_fixtures(envelope)
            self._record_normalization_errors(
                result,
                endpoint="fixtures/headtohead",
                run_id=run_id,
                state=state,
            )
            h2h_rows = tuple(
                row
                for row in result.rows
                if row.get("provider_competition_id") == competition_id
                and {
                    row.get("home_team_provider_id"),
                    row.get("away_team_provider_id"),
                }
                == {first_team_id, second_team_id}
                and row.get("status_short") in {"FT", "AET", "PEN"}
                and isinstance(row.get("kickoff_at"), datetime)
                and row["kickoff_at"] < started_at
            )[:MAX_H2H_MATCHES_PER_PAIR]
            state.h2h_matches_received += len(h2h_rows)
            inserted, duplicate = self._insert_discovery_rows(
                NormalizationResult(resource="matches", rows=h2h_rows),
                provider_id=provider_id,
                run_id=run_id,
                state=state,
            )
            state.h2h_matches_added += inserted
            state.h2h_duplicates += duplicate
            state.match_duplicates += duplicate
            self.session.commit()

    async def sync_competitions(self) -> SyncSummary:
        ids = self._priority_competitions()
        requests = [
            RequestSpec(
                endpoint="leagues",
                params={"id": competition_id},
                normalize=lambda envelope: normalize_leagues(envelope),
            )
            for competition_id in ids
        ]
        return await self._run(
            "competitions",
            {"competition_count": len(ids)},
            requests,
        )

    async def sync_seasons(self) -> SyncSummary:
        ids = self._priority_competitions()

        def seasons_only(envelope: ApiFootballEnvelope) -> Sequence[NormalizationResult]:
            _, seasons = normalize_leagues(envelope)
            return (seasons,)

        requests = [
            RequestSpec(
                endpoint="leagues",
                params={"id": competition_id},
                normalize=seasons_only,
            )
            for competition_id in ids
        ]
        return await self._run(
            "seasons",
            {"competition_count": len(ids)},
            requests,
        )

    async def sync_teams(self) -> SyncSummary:
        season = self._season()
        ids = self._priority_competitions()
        requests = [
            RequestSpec(
                endpoint="teams",
                params={"league": competition_id, "season": season},
                normalize=lambda envelope: (normalize_teams(envelope),),
            )
            for competition_id in ids
        ]
        return await self._run(
            "teams",
            {"competition_count": len(ids), "season": season},
            requests,
        )

    async def sync_standings(self) -> SyncSummary:
        season = self._season()
        ids = self._priority_competitions()
        requests = [
            RequestSpec(
                endpoint="standings",
                params={"league": competition_id, "season": season},
                normalize=lambda envelope: (normalize_standings(envelope),),
            )
            for competition_id in ids
        ]
        return await self._run(
            "standings",
            {"competition_count": len(ids), "season": season},
            requests,
        )

    async def sync_matches_for_date(self, match_date: date) -> SyncSummary:
        return await self._sync_match_window(
            "matches_date",
            match_date,
            match_date,
        )

    async def sync_upcoming(self, *, days: int | None = None) -> SyncSummary:
        window_days = days or self.settings.api_football_upcoming_days
        if window_days < 1 or window_days > 30:
            raise SportsSyncConfigurationError("upcoming_window_invalid")
        starts_on = datetime.now(UTC).date()
        return await self._sync_match_window(
            "matches_upcoming",
            starts_on,
            starts_on + timedelta(days=window_days - 1),
        )

    async def sync_results(
        self,
        *,
        starts_on: date,
        ends_on: date,
    ) -> SyncSummary:
        if ends_on < starts_on or (ends_on - starts_on).days > 31:
            raise SportsSyncConfigurationError("results_window_invalid")
        season = self._season()
        ids = self._priority_competitions()
        requests = [
            RequestSpec(
                endpoint="fixtures",
                params={
                    "league": competition_id,
                    "season": season,
                    "from": starts_on.isoformat(),
                    "to": ends_on.isoformat(),
                    "status": "FT-AET-PEN",
                    "timezone": "UTC",
                },
                normalize=lambda envelope: (normalize_fixtures(envelope),),
            )
            for competition_id in ids
        ]
        return await self._run(
            "results_finished",
            {
                "competition_count": len(ids),
                "season": season,
                "starts_on": starts_on.isoformat(),
                "ends_on": ends_on.isoformat(),
            },
            requests,
        )

    async def sync_statistics(
        self,
        *,
        starts_on: date,
        ends_on: date,
        include_related: bool = True,
    ) -> SyncSummary:
        if ends_on < starts_on or (ends_on - starts_on).days > 31:
            raise SportsSyncConfigurationError(
                "statistics_window_invalid"
            )
        starts_at = datetime.combine(starts_on, datetime.min.time(), tzinfo=UTC)
        ends_at = datetime.combine(
            ends_on + timedelta(days=1),
            datetime.min.time(),
            tzinfo=UTC,
        )
        max_matches = max(
            1,
            self.settings.api_football_max_requests_per_sync
            // (4 if include_related else 1),
        )
        match_ids = self.repository.completed_match_ids_without_statistics(
            starts_at=starts_at,
            ends_at=ends_at,
            limit=max_matches,
        )
        requests: list[RequestSpec] = []
        for match_id in match_ids:
            if include_related:
                requests.extend(
                    [
                        RequestSpec(
                            endpoint="fixtures/events",
                            params={"fixture": match_id},
                            normalize=lambda envelope, match_id=match_id: (
                                normalize_match_events(envelope, match_id),
                            ),
                        ),
                        RequestSpec(
                            endpoint="fixtures/lineups",
                            params={"fixture": match_id},
                            normalize=lambda envelope, match_id=match_id: (
                                normalize_lineups(envelope, match_id),
                            ),
                        ),
                        RequestSpec(
                            endpoint="injuries",
                            params={"fixture": match_id},
                            normalize=lambda envelope: (
                                normalize_injuries(envelope),
                            ),
                        ),
                    ]
                )
            requests.append(
                RequestSpec(
                    endpoint="fixtures/statistics",
                    params={"fixture": match_id},
                    normalize=lambda envelope, match_id=match_id: (
                        normalize_match_statistics(envelope, match_id),
                    ),
                )
            )
        return await self._run(
            "match_statistics",
            {
                "starts_on": starts_on.isoformat(),
                "ends_on": ends_on.isoformat(),
                "match_count": len(match_ids),
                "related_resources": include_related,
            },
            requests,
            stop_on_error=True,
            empty_reason="no_completed_matches_without_statistics",
        )

    async def _sync_match_window(
        self,
        sync_type: str,
        starts_on: date,
        ends_on: date,
    ) -> SyncSummary:
        if ends_on < starts_on or (ends_on - starts_on).days > 31:
            raise SportsSyncConfigurationError("match_window_invalid")
        season = self._season()
        ids = self._priority_competitions()
        requests = [
            RequestSpec(
                endpoint="fixtures",
                params={
                    "league": competition_id,
                    "season": season,
                    "from": starts_on.isoformat(),
                    "to": ends_on.isoformat(),
                    "timezone": "UTC",
                },
                normalize=lambda envelope: (normalize_fixtures(envelope),),
            )
            for competition_id in ids
        ]
        return await self._run(
            sync_type,
            {
                "competition_count": len(ids),
                "season": season,
                "starts_on": starts_on.isoformat(),
                "ends_on": ends_on.isoformat(),
            },
            requests,
        )

    async def _enrich_discovery_competition(
        self,
        *,
        competition: DiscoveryCompetition,
        competition_result: NormalizationResult,
        season_result: NormalizationResult,
        started_at: datetime,
        run_id: UUID,
        provider_id: UUID,
        state: _DiscoveryRunState,
    ) -> tuple[
        tuple[Mapping[str, Any], ...],
        tuple[Mapping[str, Any], ...],
        tuple[int, ...],
    ] | None:
        candidate_fixtures = tuple(competition.fixture_rows)
        candidate_team_ids = _fixture_team_ids(candidate_fixtures)
        team_envelope = await self._discovery_request(
            endpoint="teams",
            params={
                "league": competition.provider_competition_id,
                "season": competition.season,
            },
            run_id=run_id,
            state=state,
        )
        if team_envelope is None:
            state.ignored_reasons["team_metadata_unavailable"] += len(
                candidate_fixtures
            )
            return None

        team_result = normalize_teams(team_envelope)
        self._record_normalization_errors(
            team_result,
            endpoint="teams",
            run_id=run_id,
            state=state,
        )
        available_team_ids = {
            int(row["provider_team_id"])
            for row in team_result.rows
            if isinstance(row.get("provider_team_id"), int)
        }
        team_valid_fixtures = tuple(
            row
            for row in candidate_fixtures
            if {
                row.get("home_team_provider_id"),
                row.get("away_team_provider_id"),
            }.issubset(available_team_ids)
        )
        _increment_reason(
            state.ignored_reasons,
            "team_metadata_unavailable",
            len(candidate_fixtures) - len(team_valid_fixtures),
        )
        if not team_valid_fixtures:
            return None

        history_ends_on = started_at.date() - timedelta(days=1)
        history_starts_on = history_ends_on - timedelta(
            days=RECENT_RESULTS_LOOKBACK_DAYS - 1
        )
        history_envelope = await self._discovery_request(
            endpoint="fixtures",
            params={
                "league": competition.provider_competition_id,
                "season": competition.season,
                "from": history_starts_on.isoformat(),
                "to": history_ends_on.isoformat(),
                "status": "FT-AET-PEN",
                "timezone": "UTC",
            },
            run_id=run_id,
            state=state,
        )
        if history_envelope is None:
            state.ignored_reasons["recent_results_unavailable"] += len(
                team_valid_fixtures
            )
            return None

        history_result = normalize_fixtures(history_envelope)
        self._record_normalization_errors(
            history_result,
            endpoint="fixtures",
            run_id=run_id,
            state=state,
        )
        relevant_history = tuple(
            row
            for row in history_result.rows
            if row.get("status_short") in {"FT", "AET", "PEN"}
            and isinstance(row.get("kickoff_at"), datetime)
            and row["kickoff_at"] < started_at
            and (
                row.get("home_team_provider_id") in candidate_team_ids
                or row.get("away_team_provider_id") in candidate_team_ids
            )
        )
        state.recent_results_received += len(relevant_history)
        history_counts = Counter(
            team_id
            for row in relevant_history
            for team_id in (
                row.get("home_team_provider_id"),
                row.get("away_team_provider_id"),
            )
            if team_id in candidate_team_ids
        )
        retained_fixtures = tuple(
            row
            for row in team_valid_fixtures
            if history_counts[row["home_team_provider_id"]]
            >= MINIMUM_RECENT_RESULTS_PER_TEAM
            and history_counts[row["away_team_provider_id"]]
            >= MINIMUM_RECENT_RESULTS_PER_TEAM
        )
        _increment_reason(
            state.ignored_reasons,
            "insufficient_recent_results",
            len(team_valid_fixtures) - len(retained_fixtures),
        )
        if not retained_fixtures:
            return None

        target_team_ids = _fixture_team_ids(retained_fixtures)
        retained_history = tuple(
            row
            for row in relevant_history
            if row.get("home_team_provider_id") in target_team_ids
            or row.get("away_team_provider_id") in target_team_ids
        )

        standings_rows: tuple[Mapping[str, Any], ...] = ()
        if competition.supports_standings:
            standings_envelope = await self._discovery_request(
                endpoint="standings",
                params={
                    "league": competition.provider_competition_id,
                    "season": competition.season,
                },
                run_id=run_id,
                state=state,
            )
            if standings_envelope is not None:
                standings_result = normalize_standings(standings_envelope)
                self._record_normalization_errors(
                    standings_result,
                    endpoint="standings",
                    run_id=run_id,
                    state=state,
                )
                standings_rows = tuple(
                    row
                    for row in standings_result.rows
                    if row.get("provider_team_id") in target_team_ids
                )
                state.standings_rows_available += len(standings_rows)

        competition_rows = tuple(
            row
            for row in competition_result.rows
            if row.get("provider_competition_id")
            == competition.provider_competition_id
        )
        season_rows = tuple(
            row
            for row in season_result.rows
            if row.get("provider_competition_id")
            == competition.provider_competition_id
            and row.get("year") == competition.season
        )
        team_rows = tuple(
            row
            for row in team_result.rows
            if row.get("provider_team_id") in target_team_ids
        )
        resources = (
            ("competitions", competition_rows),
            ("seasons", season_rows),
            ("teams", team_rows),
            ("matches", retained_fixtures),
            ("matches", retained_history),
            ("standings", standings_rows),
        )
        for resource, rows in resources:
            if not rows:
                continue
            inserted, duplicate = self._insert_discovery_rows(
                NormalizationResult(resource=resource, rows=tuple(rows)),
                provider_id=provider_id,
                run_id=run_id,
                state=state,
            )
            if resource == "competitions":
                state.competitions_added += inserted
            elif resource == "seasons":
                state.seasons_added += inserted
            elif resource == "teams":
                state.teams_added += inserted
            elif resource == "matches" and rows is retained_fixtures:
                state.target_matches_added += inserted
                state.match_duplicates += duplicate
            elif resource == "matches":
                state.recent_results_added += inserted
                state.match_duplicates += duplicate
        self.session.commit()
        return retained_fixtures, retained_history, tuple(target_team_ids)

    async def _discovery_request(
        self,
        *,
        endpoint: str,
        params: Mapping[str, str | int | bool],
        run_id: UUID,
        state: _DiscoveryRunState,
    ) -> ApiFootballEnvelope | None:
        try:
            envelope = await self.client.get(endpoint, params)
        except ApiFootballRequestError as exc:
            state.error_codes.append(exc.public_code)
            state.provider_unavailable_causes.append(exc.reason_code)
            self.repository.record_error(
                run_id=run_id,
                endpoint=endpoint,
                error_code=exc.public_code,
                retryable=exc.retryable,
                occurred_at=datetime.now(UTC),
                context={"cause": exc.reason_code},
            )
            self.session.commit()
            return None
        state.last_quota = envelope
        state.records_received += envelope.data.results
        return envelope

    def _record_normalization_errors(
        self,
        result: NormalizationResult,
        *,
        endpoint: str,
        run_id: UUID,
        state: _DiscoveryRunState,
    ) -> None:
        state.records_rejected += result.rejected_count
        for error_code in result.error_codes:
            state.error_codes.append(error_code)
            self.repository.record_error(
                run_id=run_id,
                endpoint=endpoint,
                error_code=error_code,
                retryable=False,
                occurred_at=datetime.now(UTC),
                context={"rejected_count": result.rejected_count},
            )

    def _insert_discovery_rows(
        self,
        result: NormalizationResult,
        *,
        provider_id: UUID,
        run_id: UUID,
        state: _DiscoveryRunState,
    ) -> tuple[int, int]:
        inserted, duplicate = self.repository.insert_result(
            result,
            provider_id=provider_id,
            run_id=run_id,
        )
        state.records_inserted += inserted
        state.records_duplicate += duplicate
        return inserted, duplicate

    def _remaining_discovery_requests(self) -> int:
        remaining = max(
            0,
            self.settings.api_football_max_requests_per_sync
            - self.client.request_count,
        )
        for quota in (
            self.client.quota_remaining_daily,
            self.client.quota_remaining_minute,
        ):
            if isinstance(quota, int):
                remaining = min(remaining, max(0, quota))
        return remaining

    def _runtime_configuration_status(self) -> dict[str, bool]:
        return {
            "api_football_enabled": self.settings.api_football_enabled,
            "api_football_key_present": (
                self.settings.api_football_key_configured
            ),
            "api_football_season_present": (
                self.settings.api_football_season is not None
            ),
            "api_football_priority_competitions_present": bool(
                self.settings.api_football_priority_competition_ids
            ),
            "provider_runtime_ready": (
                self.settings.api_football_runtime_enabled
            ),
        }

    async def _run(
        self,
        sync_type: str,
        scope: Mapping[str, Any],
        requests: Sequence[RequestSpec],
        *,
        stop_on_error: bool = False,
        empty_reason: str | None = None,
    ) -> SyncSummary:
        if not self.client.enabled:
            raise ApiFootballDisabledError(
                "Le fournisseur sportif est désactivé par configuration."
            )
        started_at = datetime.now(UTC)
        provider_id = self.repository.ensure_provider(enabled=True)
        run_id = self.repository.start_run(
            provider_id=provider_id,
            sync_type=sync_type,
            scope=scope,
            started_at=started_at,
        )
        self.session.commit()

        received = inserted = duplicate = rejected = 0
        error_codes: list[str] = []
        fatal_error = False
        last_quota: ApiFootballEnvelope | None = None
        last_checkpoint: dict[str, Any] = (
            {"no_request_reason": empty_reason}
            if not requests and empty_reason
            else {}
        )

        try:
            async with self.client:
                for spec in requests:
                    try:
                        envelope = await self.client.get(spec.endpoint, spec.params)
                        last_quota = envelope
                        received += envelope.data.results
                        last_checkpoint = {"endpoint": spec.endpoint}
                        rejected_before_request = rejected
                        for result in spec.normalize(envelope):
                            result_inserted, result_duplicate = (
                                self.repository.insert_result(
                                    result,
                                    provider_id=provider_id,
                                    run_id=run_id,
                                )
                            )
                            inserted += result_inserted
                            duplicate += result_duplicate
                            rejected += result.rejected_count
                            for error_code in result.error_codes:
                                error_codes.append(error_code)
                                self.repository.record_error(
                                    run_id=run_id,
                                    endpoint=spec.endpoint,
                                    error_code=error_code,
                                    retryable=False,
                                    occurred_at=datetime.now(UTC),
                                )
                        self.session.commit()
                        if stop_on_error and rejected > rejected_before_request:
                            break
                    except ApiFootballRequestError as exc:
                        error_codes.append(exc.public_code)
                        self.repository.record_error(
                            run_id=run_id,
                            endpoint=spec.endpoint,
                            error_code=exc.public_code,
                            retryable=exc.retryable,
                            occurred_at=datetime.now(UTC),
                            context={"cause": exc.reason_code},
                        )
                        self.session.commit()
                        if stop_on_error or isinstance(
                            exc,
                            ApiFootballRequestBudgetError,
                        ):
                            break
        except Exception as exc:
            self.session.rollback()
            public_code = "synchronization_internal_error"
            fatal_error = True
            error_codes.append(public_code)
            logger.error(
                "Sports synchronization failed safely type=%s",
                type(exc).__name__,
            )
            self.repository.record_error(
                run_id=run_id,
                endpoint=str(last_checkpoint.get("endpoint", "synchronization")),
                error_code=public_code,
                retryable=True,
                occurred_at=datetime.now(UTC),
            )
            self.session.commit()

        status = (
            "FAILED"
            if fatal_error or (error_codes and inserted == 0 and received == 0)
            else "PARTIAL"
            if error_codes or rejected
            else "SUCCEEDED"
        )
        public_error_code = error_codes[0] if error_codes else None
        self.repository.finish_run(
            run_id=run_id,
            status=status,
            completed_at=datetime.now(UTC),
            request_count=self.client.request_count,
            records_received=received,
            records_inserted=inserted,
            records_duplicate=duplicate,
            records_rejected=rejected,
            quota_limit_daily=last_quota.quota_limit_daily if last_quota else None,
            quota_remaining_daily=self.client.quota_remaining_daily,
            quota_limit_minute=last_quota.quota_limit_minute if last_quota else None,
            quota_remaining_minute=self.client.quota_remaining_minute,
            checkpoint=last_checkpoint,
            public_error_code=public_error_code,
        )
        self.session.commit()
        return SyncSummary(
            run_id=str(run_id),
            sync_type=sync_type,
            status=status,
            request_count=self.client.request_count,
            records_received=received,
            records_inserted=inserted,
            records_duplicate=duplicate,
            records_rejected=rejected,
            public_error_code=public_error_code,
        )

    def _priority_competitions(self) -> tuple[int, ...]:
        values = self.settings.api_football_priority_competition_ids
        if not values:
            raise SportsSyncConfigurationError(
                "api_football_priority_competitions_missing"
            )
        return values

    def _season(self) -> int:
        season = self.settings.api_football_season
        if season is None:
            raise SportsSyncConfigurationError(
                "api_football_season_missing"
            )
        if season < 1900 or season > 2100:
            raise SportsSyncConfigurationError(
                "api_football_season_invalid"
            )
        return season


def _fixture_team_ids(
    fixtures: Sequence[Mapping[str, Any]],
) -> set[int]:
    return {
        team_id
        for fixture in fixtures
        for team_id in (
            fixture.get("home_team_provider_id"),
            fixture.get("away_team_provider_id"),
        )
        if isinstance(team_id, int)
    }


def _increment_reason(
    reasons: Counter[str],
    reason: str,
    count: int,
) -> None:
    if count > 0:
        reasons[reason] += count


__all__ = [
    "DailyDiscoverySummary",
    "SportsSyncConfigurationError",
    "SportsSyncService",
    "SyncSummary",
]
