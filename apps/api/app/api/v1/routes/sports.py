from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session_factory
from app.modules.sports_data.repository import (
    SportsRepository,
    apply_runtime_freshness,
)
from app.schemas.sports import (
    CompetitionCollection,
    CompetitionRead,
    FreshnessRead,
    InjuryRead,
    LineupRead,
    MatchCollection,
    MatchDetailRead,
    MatchEventRead,
    MatchRead,
    MatchStatisticRead,
    ResourceFreshness,
    SportsProviderStatus,
    SyncRunRead,
    SyncStatusRead,
)

router = APIRouter(prefix="/sports", tags=["sports-data"])
PUBLIC_DATABASE_ERROR = {
    "code": "sports_data_unavailable",
    "message": "Les données sportives sont temporairement indisponibles.",
}


@router.get("/provider", response_model=SportsProviderStatus)
def provider_status() -> SportsProviderStatus:
    configured = settings.api_football_key_configured
    enabled = settings.api_football_runtime_enabled
    last_success: dict[str, object] | None = None
    if enabled:
        try:
            with _session() as session:
                last_success = SportsRepository(session).last_successful_sync()
        except HTTPException:
            last_success = None

    if not configured:
        status = "disabled_missing_credential"
    elif not settings.api_football_enabled:
        status = "disabled_by_configuration"
    elif last_success is None:
        status = "degraded"
    else:
        status = "ready"
    return SportsProviderStatus(
        status=status,
        enabled=enabled,
        configured=configured,
        connected=last_success is not None,
        last_success_at=(
            last_success.get("completed_at")
            if isinstance(last_success, dict)
            else None
        ),
        quota_remaining_daily=(
            last_success.get("quota_remaining_daily")
            if isinstance(last_success, dict)
            else None
        ),
        quota_remaining_minute=(
            last_success.get("quota_remaining_minute")
            if isinstance(last_success, dict)
            else None
        ),
        priority_competition_count=len(
            settings.api_football_priority_competition_ids
        ),
        season=settings.api_football_season,
        max_requests_per_sync=settings.api_football_max_requests_per_sync,
    )


@router.get("/competitions", response_model=CompetitionCollection)
def competitions(
    limit: int = Query(default=100, ge=1, le=100),
) -> CompetitionCollection:
    with _session() as session:
        rows = SportsRepository(session).list_competitions(limit=limit)
    now = datetime.now(UTC)
    items = [
        CompetitionRead.model_validate(
            apply_runtime_freshness(
                row,
                now=now,
                threshold_minutes=settings.api_football_freshness_minutes,
            )
        )
        for row in rows
    ]
    return CompetitionCollection(items=items, count=len(items))


@router.get("/matches/today", response_model=MatchCollection)
def matches_today() -> MatchCollection:
    local_zone = ZoneInfo("Africa/Kinshasa")
    local_now = datetime.now(local_zone)
    starts_at = datetime.combine(local_now.date(), time.min, tzinfo=local_zone)
    return _match_collection(starts_at.astimezone(UTC), (starts_at + timedelta(days=1)).astimezone(UTC))


@router.get("/matches/upcoming", response_model=MatchCollection)
def matches_upcoming(
    days: int = Query(default=7, ge=1, le=30),
) -> MatchCollection:
    starts_at = datetime.now(UTC)
    return _match_collection(starts_at, starts_at + timedelta(days=days))


@router.get("/matches/{provider_match_id}", response_model=MatchDetailRead)
def match_detail(provider_match_id: int) -> MatchDetailRead:
    if provider_match_id <= 0:
        raise HTTPException(status_code=422, detail="Identifiant de match invalide.")
    with _session() as session:
        repository = SportsRepository(session)
        match = repository.get_match(provider_match_id)
        if match is None:
            raise HTTPException(status_code=404, detail="Match introuvable.")
        statistics = repository.list_match_resource(
            "match_statistics",
            provider_match_id,
        )
        events = repository.list_match_resource("match_events", provider_match_id)
        lineups = repository.list_match_resource("lineups", provider_match_id)
        injuries = repository.list_match_resource("injuries", provider_match_id)
    now = datetime.now(UTC)
    threshold = settings.api_football_freshness_minutes
    return MatchDetailRead(
        match=MatchRead.model_validate(
            apply_runtime_freshness(
                match,
                now=now,
                threshold_minutes=threshold,
            )
        ),
        statistics=[
            MatchStatisticRead.model_validate(
                apply_runtime_freshness(
                    row,
                    now=now,
                    threshold_minutes=threshold,
                )
            )
            for row in statistics
        ],
        events=[
            MatchEventRead.model_validate(
                apply_runtime_freshness(
                    row,
                    now=now,
                    threshold_minutes=threshold,
                )
            )
            for row in events
        ],
        lineups=[
            LineupRead.model_validate(
                apply_runtime_freshness(
                    row,
                    now=now,
                    threshold_minutes=threshold,
                )
            )
            for row in lineups
        ],
        injuries=[
            InjuryRead.model_validate(
                apply_runtime_freshness(
                    row,
                    now=now,
                    threshold_minutes=threshold,
                )
            )
            for row in injuries
        ],
    )


@router.get("/sync/status", response_model=SyncStatusRead)
def sync_status() -> SyncStatusRead:
    with _session() as session:
        repository = SportsRepository(session)
        latest = repository.latest_sync_status()
        errors = repository.recent_public_errors()
    latest_schema = (
        SyncRunRead(
            run_id=str(latest["id"]),
            sync_type=str(latest["sync_type"]),
            status=str(latest["status"]),
            started_at=latest["started_at"],
            completed_at=latest.get("completed_at"),
            request_count=int(latest["request_count"]),
            records_received=int(latest["records_received"]),
            records_inserted=int(latest["records_inserted"]),
            records_duplicate=int(latest["records_duplicate"]),
            records_rejected=int(latest["records_rejected"]),
            quota_remaining_daily=latest.get("quota_remaining_daily"),
            quota_remaining_minute=latest.get("quota_remaining_minute"),
            public_error_code=latest.get("public_error_code"),
        )
        if latest
        else None
    )
    return SyncStatusRead(latest=latest_schema, recent_errors=errors)


@router.get("/freshness", response_model=FreshnessRead)
def freshness() -> FreshnessRead:
    with _session() as session:
        resources = SportsRepository(session).resource_freshness()
    now = datetime.now(UTC)
    threshold = settings.api_football_freshness_minutes
    items: list[ResourceFreshness] = []
    for resource in resources:
        latest = resource["latest_fetched_at"]
        age_minutes = (
            max(0, int((now - latest.astimezone(UTC)).total_seconds() // 60))
            if isinstance(latest, datetime) and latest.tzinfo is not None
            else None
        )
        status = (
            "missing"
            if age_minutes is None
            else "fresh"
            if age_minutes <= threshold
            else "stale"
        )
        items.append(
            ResourceFreshness(
                resource=str(resource["resource"]),
                latest_fetched_at=latest,
                age_minutes=age_minutes,
                status=status,
                row_count=int(resource["row_count"]),
            )
        )
    return FreshnessRead(
        as_of=now,
        threshold_minutes=threshold,
        resources=items,
    )


def _match_collection(
    starts_at: datetime,
    ends_at: datetime,
) -> MatchCollection:
    with _session() as session:
        rows = SportsRepository(session).list_matches(
            starts_at=starts_at,
            ends_at=ends_at,
        )
    now = datetime.now(UTC)
    items = [
        MatchRead.model_validate(
            apply_runtime_freshness(
                row,
                now=now,
                threshold_minutes=settings.api_football_freshness_minutes,
            )
        )
        for row in rows
    ]
    return MatchCollection(items=items, count=len(items))


class _SessionContext:
    def __enter__(self) -> Session:
        try:
            self._session = get_session_factory()()
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=PUBLIC_DATABASE_ERROR,
            ) from exc
        return self._session

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self._session.close()
        if exc is not None and not isinstance(exc, HTTPException):
            raise HTTPException(
                status_code=503,
                detail=PUBLIC_DATABASE_ERROR,
            ) from None


def _session() -> _SessionContext:
    return _SessionContext()
