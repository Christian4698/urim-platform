from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
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
            raise ValueError("Upcoming window must be between 1 and 30 days.")
        starts_on = datetime.now(UTC).date()
        return await self._sync_match_window(
            "matches_upcoming",
            starts_on,
            starts_on + timedelta(days=window_days),
        )

    async def sync_results(
        self,
        *,
        starts_on: date,
        ends_on: date,
    ) -> SyncSummary:
        if ends_on < starts_on or (ends_on - starts_on).days > 31:
            raise ValueError("Results window must be ordered and at most 31 days.")
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
            raise ValueError("Statistics window must be ordered and at most 31 days.")
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
        )

    async def _sync_match_window(
        self,
        sync_type: str,
        starts_on: date,
        ends_on: date,
    ) -> SyncSummary:
        if ends_on < starts_on or (ends_on - starts_on).days > 31:
            raise ValueError("Match window must be ordered and at most 31 days.")
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

    async def _run(
        self,
        sync_type: str,
        scope: Mapping[str, Any],
        requests: Sequence[RequestSpec],
        *,
        stop_on_error: bool = False,
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
        last_checkpoint: dict[str, Any] = {}

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
            raise ValueError(
                "At least one priority competition must be configured."
            )
        return values

    def _season(self) -> int:
        season = self.settings.api_football_season
        if season is None or season < 1900 or season > 2100:
            raise ValueError("A valid API-Football season must be configured.")
        return season


__all__ = ["SportsSyncService", "SyncSummary"]
