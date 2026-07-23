from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
import hashlib
import json
import logging
import random
import time
from typing import Any, Final

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings, settings

API_FOOTBALL_PROVIDER: Final = "api-football"
API_FOOTBALL_BASE_URL: Final = "https://v3.football.api-sports.io"
API_FOOTBALL_SOURCE_VERSION: Final = "football-v3"
API_FOOTBALL_AUTH_HEADER: Final = "x-apisports-key"
RETRYABLE_STATUS_CODES: Final = frozenset({429, 500, 502, 503, 504})
FORBIDDEN_ENDPOINT_PARTS: Final = frozenset(
    {"odds", "prediction", "predictions", "bookmaker", "betting", "live"}
)
ALLOWED_ENDPOINT_PARAMETERS: Final[dict[str, frozenset[str]]] = {
    "leagues": frozenset(
        {"id", "name", "country", "code", "season", "team", "type", "current", "search", "last"}
    ),
    "teams": frozenset(
        {"id", "name", "league", "season", "country", "code", "venue", "search"}
    ),
    "fixtures": frozenset(
        {
            "id",
            "ids",
            "date",
            "league",
            "season",
            "team",
            "last",
            "next",
            "from",
            "to",
            "round",
            "status",
            "venue",
            "timezone",
        }
    ),
    "standings": frozenset({"league", "season", "team"}),
    "fixtures/statistics": frozenset({"fixture", "team", "type", "half"}),
    "fixtures/events": frozenset({"fixture", "team", "player", "type"}),
    "fixtures/lineups": frozenset({"fixture", "team", "player", "type"}),
    "injuries": frozenset(
        {"league", "season", "fixture", "team", "player", "date", "ids", "timezone"}
    ),
}

logger = logging.getLogger("urim.sports_data.provider")


class ApiFootballDisabledError(RuntimeError):
    public_code = "provider_disabled"


class ApiFootballRequestError(RuntimeError):
    public_code = "provider_unavailable"

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ApiFootballQuotaError(ApiFootballRequestError):
    public_code = "provider_quota_exhausted"


class ApiFootballRateLimitError(ApiFootballRequestError):
    public_code = "provider_rate_limited"


class ApiFootballRequestBudgetError(ApiFootballRequestError):
    public_code = "provider_request_budget_exhausted"


class ApiFootballValidationError(ApiFootballRequestError):
    public_code = "provider_response_invalid"


class ApiFootballPaging(BaseModel):
    current: int = Field(default=1, ge=0)
    total: int = Field(default=1, ge=0)

    model_config = ConfigDict(extra="ignore")


class ApiFootballEnvelopeModel(BaseModel):
    get: str
    parameters: dict[str, Any] | list[Any] = Field(default_factory=dict)
    errors: dict[str, Any] | list[Any] = Field(default_factory=list)
    results: int = Field(ge=0)
    paging: ApiFootballPaging = Field(default_factory=ApiFootballPaging)
    response: list[Any]

    model_config = ConfigDict(extra="ignore")


class ApiFootballEnvelope(BaseModel):
    endpoint: str
    request_id: str
    fetched_at: datetime
    observed_at: datetime
    available_at: datetime
    source_version: str
    raw_hash: str
    quota_limit_daily: int | None = None
    quota_remaining_daily: int | None = None
    quota_limit_minute: int | None = None
    quota_remaining_minute: int | None = None
    data: ApiFootballEnvelopeModel

    model_config = ConfigDict(extra="forbid")


class WindowRateLimiter:
    def __init__(
        self,
        requests_per_minute: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if requests_per_minute < 1 or requests_per_minute > 1_200:
            raise ValueError("requests_per_minute must be between 1 and 1200")
        self._limit = requests_per_minute
        self._clock = clock
        self._sleeper = sleeper
        self._timestamps: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = self._clock()
                while self._timestamps and now - self._timestamps[0] >= 60:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._limit:
                    self._timestamps.append(now)
                    return
                delay = max(0.001, 60 - (now - self._timestamps[0]))
            await self._sleeper(delay)


class ApiFootballClient:
    def __init__(
        self,
        *,
        api_key: str | None,
        enabled: bool,
        timeout_seconds: float = 10,
        max_retries: int = 2,
        requests_per_minute: int = 10,
        max_requests: int | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        sleeper: Callable[[float], Awaitable[None]] = asyncio.sleep,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 30:
            raise ValueError("timeout_seconds must be greater than 0 and at most 30")
        if max_retries < 0 or max_retries > 3:
            raise ValueError("max_retries must be between 0 and 3")
        if max_requests is not None and (max_requests < 1 or max_requests > 100):
            raise ValueError("max_requests must be between 1 and 100")
        self._api_key = api_key.strip() if api_key else ""
        self._enabled = enabled
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._max_requests = max_requests
        self._transport = transport
        self._sleeper = sleeper
        self._jitter = jitter
        self._rate_limiter = WindowRateLimiter(
            requests_per_minute,
            sleeper=sleeper,
        )
        self._client: httpx.AsyncClient | None = None
        self._request_count = 0
        self._quota_remaining_daily: int | None = None
        self._quota_remaining_minute: int | None = None

    @classmethod
    def from_settings(
        cls,
        app_settings: Settings = settings,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> ApiFootballClient:
        secret = (
            app_settings.api_football_key.get_secret_value()
            if app_settings.api_football_key
            else None
        )
        return cls(
            api_key=secret,
            enabled=app_settings.api_football_enabled,
            timeout_seconds=app_settings.api_football_request_timeout_seconds,
            max_retries=app_settings.api_football_max_retries,
            requests_per_minute=app_settings.api_football_requests_per_minute,
            max_requests=app_settings.api_football_max_requests_per_sync,
            transport=transport,
        )

    @property
    def request_count(self) -> int:
        return self._request_count

    @property
    def quota_remaining_daily(self) -> int | None:
        return self._quota_remaining_daily

    @property
    def quota_remaining_minute(self) -> int | None:
        return self._quota_remaining_minute

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._api_key)

    async def __aenter__(self) -> ApiFootballClient:
        self._ensure_enabled()
        self._client = httpx.AsyncClient(
            base_url=API_FOOTBALL_BASE_URL,
            headers={
                API_FOOTBALL_AUTH_HEADER: self._api_key,
                "Accept": "application/json",
                "User-Agent": "URIM-Sports-Data/1.0",
            },
            follow_redirects=False,
            timeout=httpx.Timeout(self._timeout_seconds),
            transport=self._transport,
            trust_env=False,
        )
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        endpoint: str,
        params: Mapping[str, str | int | bool] | None = None,
    ) -> ApiFootballEnvelope:
        self._ensure_enabled()
        normalized_endpoint, normalized_params = validate_provider_request(
            endpoint,
            params,
        )
        if self._quota_remaining_daily == 0:
            raise ApiFootballQuotaError("Le quota quotidien du fournisseur est épuisé.")
        if self._client is None:
            raise RuntimeError("ApiFootballClient must be used as an async context manager.")

        for attempt in range(self._max_retries + 1):
            if (
                self._max_requests is not None
                and self._request_count >= self._max_requests
            ):
                raise ApiFootballRequestBudgetError(
                    "Le budget de requêtes de synchronisation est épuisé."
                )
            await self._rate_limiter.acquire()
            self._request_count += 1
            try:
                response = await self._client.get(
                    f"/{normalized_endpoint}",
                    params=normalized_params,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                if attempt < self._max_retries:
                    await self._backoff(attempt)
                    continue
                raise ApiFootballRequestError(
                    "Le fournisseur sportif est temporairement indisponible.",
                    retryable=True,
                ) from exc

            self._update_quota(response.headers)
            if response.status_code in RETRYABLE_STATUS_CODES:
                if attempt < self._max_retries:
                    await self._backoff(attempt, response)
                    continue
                if response.status_code == 429:
                    raise ApiFootballRateLimitError(
                        "Le fournisseur sportif limite temporairement les requêtes.",
                        retryable=True,
                    )
                raise ApiFootballRequestError(
                    "Le fournisseur sportif est temporairement indisponible.",
                    retryable=True,
                )
            if response.status_code < 200 or response.status_code >= 300:
                raise ApiFootballRequestError(
                    "Le fournisseur sportif a refusé la requête.",
                    retryable=False,
                )

            envelope = self._validate_response(
                normalized_endpoint,
                response,
            )
            logger.info(
                "API-Football request completed endpoint=%s status=%s attempt=%s",
                normalized_endpoint,
                response.status_code,
                attempt + 1,
            )
            return envelope

        raise ApiFootballRequestError(
            "Le fournisseur sportif est temporairement indisponible.",
            retryable=True,
        )

    def _ensure_enabled(self) -> None:
        if not self._api_key:
            raise ApiFootballDisabledError(
                "Le fournisseur sportif est désactivé faute de configuration sécurisée."
            )
        if not self._enabled:
            raise ApiFootballDisabledError(
                "Le fournisseur sportif est désactivé par configuration."
            )

    async def _backoff(
        self,
        attempt: int,
        response: httpx.Response | None = None,
    ) -> None:
        retry_after = _safe_float(response.headers.get("Retry-After")) if response else None
        delay = retry_after if retry_after is not None else (2**attempt) + self._jitter()
        await self._sleeper(min(max(delay, 0), 10))

    def _update_quota(self, headers: httpx.Headers) -> None:
        self._quota_remaining_daily = _safe_int(
            headers.get("x-ratelimit-requests-remaining")
        )
        self._quota_remaining_minute = _safe_int(
            headers.get("x-ratelimit-remaining")
        )

    def _validate_response(
        self,
        endpoint: str,
        response: httpx.Response,
    ) -> ApiFootballEnvelope:
        try:
            payload = response.json()
            model = ApiFootballEnvelopeModel.model_validate(payload)
        except (ValueError, ValidationError) as exc:
            raise ApiFootballValidationError(
                "Le fournisseur sportif a retourné une réponse invalide."
            ) from exc

        if _has_provider_errors(model.errors):
            raise ApiFootballRequestError(
                "Le fournisseur sportif a refusé la requête.",
                retryable=False,
            )
        if model.results != len(model.response):
            raise ApiFootballValidationError(
                "Le fournisseur sportif a retourné une réponse incohérente."
            )

        fetched_at = datetime.now(UTC)
        observed_at = _provider_observed_at(response.headers, fetched_at)
        raw_hash = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()
        return ApiFootballEnvelope(
            endpoint=endpoint,
            request_id=response.headers.get("x-request-id", raw_hash[:16]),
            fetched_at=fetched_at,
            observed_at=observed_at,
            available_at=fetched_at,
            source_version=API_FOOTBALL_SOURCE_VERSION,
            raw_hash=raw_hash,
            quota_limit_daily=_safe_int(
                response.headers.get("x-ratelimit-requests-limit")
            ),
            quota_remaining_daily=self._quota_remaining_daily,
            quota_limit_minute=_safe_int(
                response.headers.get("x-ratelimit-limit")
            ),
            quota_remaining_minute=self._quota_remaining_minute,
            data=model,
        )


def validate_provider_request(
    endpoint: str,
    params: Mapping[str, str | int | bool] | None,
) -> tuple[str, dict[str, str | int | bool]]:
    normalized_endpoint = endpoint.strip().strip("/")
    if normalized_endpoint not in ALLOWED_ENDPOINT_PARAMETERS:
        raise ValueError("API-Football endpoint is not allowlisted.")
    if any(part in normalized_endpoint.lower() for part in FORBIDDEN_ENDPOINT_PARTS):
        raise ValueError("API-Football endpoint is forbidden in Programme B1.")

    normalized_params = dict(params or {})
    unknown = set(normalized_params) - ALLOWED_ENDPOINT_PARAMETERS[normalized_endpoint]
    if unknown:
        raise ValueError("API-Football request contains unsupported parameters.")
    if any(key.lower() in FORBIDDEN_ENDPOINT_PARTS for key in normalized_params):
        raise ValueError("API-Football request contains a forbidden parameter.")
    for key, value in normalized_params.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, int) and value >= 0:
            continue
        if isinstance(value, str) and value.strip() and len(value) <= 160:
            continue
        raise ValueError(f"API-Football parameter {key} has an invalid value.")
    return normalized_endpoint, normalized_params


def _has_provider_errors(errors: dict[str, Any] | list[Any]) -> bool:
    return bool(errors)


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _provider_observed_at(
    headers: httpx.Headers,
    fetched_at: datetime,
) -> datetime:
    header = headers.get("date")
    if not header:
        return fetched_at
    try:
        parsed = parsedate_to_datetime(header)
    except (TypeError, ValueError):
        return fetched_at
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    parsed = parsed.astimezone(UTC)
    return min(parsed, fetched_at)


__all__ = [
    "ALLOWED_ENDPOINT_PARAMETERS",
    "API_FOOTBALL_BASE_URL",
    "API_FOOTBALL_PROVIDER",
    "API_FOOTBALL_SOURCE_VERSION",
    "ApiFootballClient",
    "ApiFootballDisabledError",
    "ApiFootballEnvelope",
    "ApiFootballQuotaError",
    "ApiFootballRateLimitError",
    "ApiFootballRequestBudgetError",
    "ApiFootballRequestError",
    "ApiFootballValidationError",
    "WindowRateLimiter",
    "validate_provider_request",
]
