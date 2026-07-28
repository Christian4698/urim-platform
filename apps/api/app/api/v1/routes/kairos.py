from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, time, timedelta
from threading import BoundedSemaphore
from typing import Annotated, Final
from zoneinfo import ZoneInfo

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BeforeValidator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_session_factory
from app.modules.kairos.models import (
    KairosDataError,
    KairosPreMatchWindowClosedError,
    KairosTemporalIntegrityError,
)
from app.modules.kairos.repository import KairosRepository
from app.modules.kairos.rate_limit import (
    RedisRateLimitUnavailable,
    RedisSlidingWindowRateLimiter,
)
from app.modules.kairos.schemas import (
    KairosAnalysisResponse,
    KairosDailySuggestionsResponse,
    KairosMethodologyResponse,
)
from app.modules.kairos.services import (
    RECENT_WINDOW_MATCHES,
    KairosAnalysisService,
    build_kairos_methodology,
)

router = APIRouter(prefix="/kairos", tags=["kairos"])
POSTGRES_BIGINT_MAX: Final = 9_223_372_036_854_775_807
KAIROS_MIN_AS_OF: Final = datetime(1900, 1, 1, tzinfo=UTC)
KAIROS_STATEMENT_TIMEOUT: Final = "3000ms"
MAX_CONCURRENT_KAIROS_ANALYSES: Final = 8
MAX_CONCURRENT_DAILY_SUGGESTIONS: Final = 2
MAX_DAILY_TARGET_MATCHES: Final = 16
MAX_DAILY_SUGGESTIONS: Final = 12
KAIROS_LOCAL_TIMEZONE: Final = ZoneInfo("Africa/Kinshasa")
_ANALYSIS_CAPACITY = BoundedSemaphore(MAX_CONCURRENT_KAIROS_ANALYSES)
_SUGGESTIONS_CAPACITY = BoundedSemaphore(MAX_CONCURRENT_DAILY_SUGGESTIONS)
_METHODOLOGY_RATE_LIMIT = 120
_ANALYSIS_RATE_LIMIT = 30
_SUGGESTIONS_RATE_LIMIT = 10
PUBLIC_DATABASE_ERROR = {
    "code": "kairos_data_unavailable",
    "message": "Les données nécessaires à l'analyse sont indisponibles.",
}
PUBLIC_TEMPORAL_ERROR = {
    "code": "kairos_temporal_integrity_blocked",
    "message": "L'analyse a été bloquée par le contrôle temporel.",
}
PUBLIC_PRE_MATCH_ERROR = {
    "code": "kairos_pre_match_only",
    "message": "Kairos Core B2.1 analyse uniquement un match avant son coup d'envoi.",
}
PUBLIC_DATA_INTEGRITY_ERROR = {
    "code": "kairos_data_integrity_blocked",
    "message": "L'analyse a été bloquée car les données ne sont pas sûres.",
}
PUBLIC_QUERY_ERROR = {
    "code": "kairos_query_parameters_invalid",
    "message": "Les paramètres de requête Kairos sont invalides.",
}
PUBLIC_CAPACITY_ERROR = {
    "code": "kairos_capacity_exceeded",
    "message": "La capacité temporaire d'analyse Kairos est atteinte.",
}
PUBLIC_RATE_LIMIT_ERROR = {
    "code": "kairos_rate_limit_exceeded",
    "message": "Trop de requêtes Kairos ont été reçues.",
}
PUBLIC_RATE_LIMIT_UNAVAILABLE_ERROR = {
    "code": "kairos_rate_limit_unavailable",
    "message": "Le contrôle de débit Kairos est temporairement indisponible.",
}


def _canonical_provider_match_id(value: object) -> object:
    if isinstance(value, str) and (
        not value.isascii()
        or not value.isdecimal()
        or value.startswith("0")
        or len(value) > 19
    ):
        raise ValueError("provider_match_id must be a canonical positive bigint")
    return value


ProviderMatchId = Annotated[
    int,
    BeforeValidator(_canonical_provider_match_id),
    Path(gt=0, le=POSTGRES_BIGINT_MAX),
]


def _analysis_capacity_dependency() -> Iterator[None]:
    if not _ANALYSIS_CAPACITY.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail=PUBLIC_CAPACITY_ERROR,
            headers={"Retry-After": "1"},
        )
    try:
        yield
    finally:
        _ANALYSIS_CAPACITY.release()


def _suggestions_capacity_dependency() -> Iterator[None]:
    if not _SUGGESTIONS_CAPACITY.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail=PUBLIC_CAPACITY_ERROR,
            headers={"Retry-After": "1"},
        )
    try:
        yield
    finally:
        _SUGGESTIONS_CAPACITY.release()


@router.get("/methodology", response_model=KairosMethodologyResponse)
def methodology(request: Request) -> KairosMethodologyResponse:
    _validate_query_parameters(request, allowed=frozenset())
    _enforce_rate_limit(request, _METHODOLOGY_RATE_LIMITER)
    return build_kairos_methodology(
        ttl_minutes=settings.api_football_freshness_minutes,
    )


@router.get(
    "/suggestions/today",
    response_model=KairosDailySuggestionsResponse,
)
def daily_suggestions(
    request: Request,
    _capacity: Annotated[None, Depends(_suggestions_capacity_dependency)],
) -> KairosDailySuggestionsResponse:
    _validate_query_parameters(request, allowed=frozenset())
    _enforce_rate_limit(request, _SUGGESTIONS_RATE_LIMITER)
    as_of = datetime.now(UTC)
    local_date = as_of.astimezone(KAIROS_LOCAL_TIMEZONE).date()
    starts_at = datetime.combine(
        local_date,
        time.min,
        tzinfo=KAIROS_LOCAL_TIMEZONE,
    ).astimezone(UTC)
    ends_at = starts_at + timedelta(days=1)

    with _session() as session:
        repository = KairosRepository(session)
        targets = repository.list_target_matches_as_of(
            starts_at=starts_at,
            ends_at=ends_at,
            as_of=as_of,
            limit=MAX_DAILY_TARGET_MATCHES,
        )
        datasets = tuple(
            repository.load_match_dataset_for_target(
                target,
                as_of=as_of,
                recent_window=RECENT_WINDOW_MATCHES,
            )
            for target in targets
        )

    service = KairosAnalysisService(
        freshness_threshold_minutes=settings.api_football_freshness_minutes
    )
    suggestions = []
    skipped_unsafe_match_count = 0
    for dataset in datasets:
        try:
            suggestions.append(
                service.analyze(dataset).analytical_suggestion
            )
        except (
            KairosDataError,
            KairosPreMatchWindowClosedError,
            KairosTemporalIntegrityError,
        ):
            skipped_unsafe_match_count += 1

    suggestions.sort(
        key=lambda suggestion: (
            suggestion.no_bet,
            -suggestion.kairos_score,
            suggestion.kickoff_at,
            suggestion.provider_match_id,
        )
    )
    selected = suggestions[:MAX_DAILY_SUGGESTIONS]
    warnings = [
        (
            "Suggestions analytiques non calibrées, sans cote, mise, "
            "bookmaker ni automatisation."
        )
    ]
    if skipped_unsafe_match_count:
        warnings.append(
            "Des matchs ont été exclus par les contrôles d'intégrité."
        )
    return KairosDailySuggestionsResponse(
        local_date=local_date,
        as_of=as_of,
        suggestion_count=len(selected),
        evaluated_match_count=len(suggestions),
        skipped_unsafe_match_count=skipped_unsafe_match_count,
        suggestions=selected,
        warnings=warnings,
    )


@router.get(
    "/matches/{provider_match_id}/analysis",
    response_model=KairosAnalysisResponse,
)
def match_analysis(
    request: Request,
    provider_match_id: ProviderMatchId,
    _capacity: Annotated[None, Depends(_analysis_capacity_dependency)],
    as_of: datetime | None = Query(default=None),
) -> KairosAnalysisResponse:
    _validate_query_parameters(
        request,
        allowed=frozenset({"as_of"}),
        singular=frozenset({"as_of"}),
    )
    _enforce_rate_limit(request, _ANALYSIS_RATE_LIMITER)
    now = datetime.now(UTC)
    as_of_value = as_of or now
    if as_of_value.tzinfo is None:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "kairos_as_of_timezone_required",
                "message": "Le paramètre as_of doit inclure un fuseau horaire.",
            },
        )
    try:
        if as_of_value.utcoffset() is None:
            raise ValueError("timezone offset is missing")
        as_of_value = as_of_value.astimezone(UTC)
    except (OverflowError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "kairos_invalid_as_of",
                "message": "Le paramètre as_of n'est pas une date valide.",
            },
        ) from exc
    if as_of_value > now:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "kairos_future_as_of_forbidden",
                "message": "Le paramètre as_of ne peut pas être dans le futur.",
            },
        )
    if as_of_value < KAIROS_MIN_AS_OF:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "kairos_as_of_out_of_range",
                "message": "Le paramètre as_of est hors de la plage supportée.",
            },
        )

    with _session() as session:
        dataset = KairosRepository(session).load_match_dataset(
            provider_match_id,
            as_of=as_of_value,
            recent_window=RECENT_WINDOW_MATCHES,
        )
    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "kairos_match_not_found_as_of",
                "message": "Match introuvable avec les données disponibles à as_of.",
            },
        )

    try:
        return KairosAnalysisService(
            freshness_threshold_minutes=(
                settings.api_football_freshness_minutes
            )
        ).analyze(dataset)
    except KairosPreMatchWindowClosedError as exc:
        raise HTTPException(
            status_code=409,
            detail=PUBLIC_PRE_MATCH_ERROR,
        ) from exc
    except KairosTemporalIntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=PUBLIC_TEMPORAL_ERROR,
        ) from exc
    except KairosDataError as exc:
        raise HTTPException(
            status_code=409,
            detail=PUBLIC_DATA_INTEGRITY_ERROR,
        ) from exc


class _SessionContext:
    def __enter__(self) -> Session:
        self._session: Session | None = None
        try:
            session = get_session_factory()()
            self._session = session
            _configure_read_only_session(session)
        except Exception:
            if self._session is not None:
                try:
                    self._session.close()
                except Exception:
                    pass
            raise HTTPException(
                status_code=503,
                detail=PUBLIC_DATABASE_ERROR,
            ) from None
        return session

    def __exit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        close_failed = False
        try:
            if self._session is not None:
                self._session.close()
        except Exception:
            close_failed = True
        if close_failed or (
            exc is not None and not isinstance(exc, HTTPException)
        ):
            raise HTTPException(
                status_code=503,
                detail=PUBLIC_DATABASE_ERROR,
            ) from None


def _session() -> _SessionContext:
    return _SessionContext()


def _configure_read_only_session(session: Session) -> None:
    if session.get_bind().dialect.name != "postgresql":
        return
    session.execute(sa.text("SET TRANSACTION READ ONLY"))
    session.execute(
        sa.text(
            "SELECT set_config("
            "'statement_timeout', :statement_timeout, true"
            ")"
        ),
        {"statement_timeout": KAIROS_STATEMENT_TIMEOUT},
    )


def _validate_query_parameters(
    request: Request,
    *,
    allowed: frozenset[str],
    singular: frozenset[str] = frozenset(),
) -> None:
    supplied = frozenset(request.query_params.keys())
    has_duplicates = any(
        len(request.query_params.getlist(name)) != 1
        for name in singular
        if name in supplied
    )
    if not supplied.issubset(allowed) or has_duplicates:
        raise HTTPException(status_code=422, detail=PUBLIC_QUERY_ERROR)


_METHODOLOGY_RATE_LIMITER = RedisSlidingWindowRateLimiter(
    scope="methodology",
    limit=_METHODOLOGY_RATE_LIMIT,
    redis_url=settings.redis_url,
)
_ANALYSIS_RATE_LIMITER = RedisSlidingWindowRateLimiter(
    scope="analysis",
    limit=_ANALYSIS_RATE_LIMIT,
    redis_url=settings.redis_url,
)
_SUGGESTIONS_RATE_LIMITER = RedisSlidingWindowRateLimiter(
    scope="daily-suggestions",
    limit=_SUGGESTIONS_RATE_LIMIT,
    redis_url=settings.redis_url,
)


def _enforce_rate_limit(
    request: Request,
    limiter: RedisSlidingWindowRateLimiter,
) -> None:
    client_key = request.client.host if request.client else "unknown"
    try:
        retry_after = limiter.retry_after(client_key)
    except RedisRateLimitUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=PUBLIC_RATE_LIMIT_UNAVAILABLE_ERROR,
            headers={"Retry-After": "1"},
        ) from exc
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail=PUBLIC_RATE_LIMIT_ERROR,
            headers={"Retry-After": str(retry_after)},
        )


__all__ = ["router"]
