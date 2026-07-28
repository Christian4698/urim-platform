from __future__ import annotations

from collections.abc import Sequence
import hashlib
import math
from threading import RLock
from typing import Final, Protocol
from uuid import uuid4

from redis import Redis

from app.core.config import settings
from app.core.constants import DATABASE_OK, DATABASE_UNAVAILABLE

RATE_LIMIT_WINDOW_SECONDS: Final = 60
REDIS_SOCKET_TIMEOUT_SECONDS: Final = 1.0
REDIS_KEY_PREFIX: Final = "urim:kairos:rate-limit:v1"

_SLIDING_WINDOW_SCRIPT: Final = """
local current_time = redis.call('TIME')
local now_ms = (current_time[1] * 1000) + math.floor(current_time[2] / 1000)
local window_ms = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local member = ARGV[3]
local cutoff_ms = now_ms - window_ms

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', cutoff_ms)
local request_count = redis.call('ZCARD', KEYS[1])
if request_count >= limit then
    local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
    local retry_ms = window_ms
    if oldest[2] then
        retry_ms = math.max(1, window_ms - (now_ms - tonumber(oldest[2])))
    end
    redis.call('PEXPIRE', KEYS[1], window_ms)
    return {0, retry_ms}
end

redis.call('ZADD', KEYS[1], now_ms, member)
redis.call('PEXPIRE', KEYS[1], window_ms)
return {1, 0}
""".strip()


class RedisRateLimitUnavailable(RuntimeError):
    """Raised when the distributed limiter cannot make a safe decision."""


class RedisClient(Protocol):
    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> object: ...

    def ping(self) -> object: ...


_client_lock = RLock()
_shared_client: Redis[bytes] | None = None
_shared_client_url: str | None = None


class RedisSlidingWindowRateLimiter:
    def __init__(
        self,
        *,
        scope: str,
        limit: int,
        redis_url: str | None = None,
        client: RedisClient | None = None,
    ) -> None:
        if not scope or ":" in scope:
            raise ValueError("scope must be a non-empty Redis key segment")
        if limit <= 0:
            raise ValueError("limit must be positive")
        self.scope = scope
        self.limit = limit
        self.redis_url = redis_url
        self._client = client

    def retry_after(self, client_key: str) -> int | None:
        client = self._client
        if client is None:
            if not self.redis_url:
                raise RedisRateLimitUnavailable(
                    "Redis rate limiting is not configured."
                )

        digest = hashlib.sha256(client_key.encode("utf-8")).hexdigest()
        key = f"{REDIS_KEY_PREFIX}:{self.scope}:{digest}"
        member = uuid4().hex
        try:
            if client is None:
                client = _get_shared_client(self.redis_url)
            raw_result = client.eval(
                _SLIDING_WINDOW_SCRIPT,
                1,
                key,
                RATE_LIMIT_WINDOW_SECONDS * 1_000,
                self.limit,
                member,
            )
            allowed, retry_ms = _parse_script_result(raw_result)
        except Exception as exc:
            raise RedisRateLimitUnavailable(
                "Redis rate limiting is unavailable."
            ) from exc

        if allowed:
            return None
        return max(
            1,
            min(
                RATE_LIMIT_WINDOW_SECONDS,
                math.ceil(retry_ms / 1_000),
            ),
        )


def get_redis_rate_limit_status() -> str:
    if not settings.redis_url:
        return DATABASE_UNAVAILABLE
    try:
        return (
            DATABASE_OK
            if bool(_get_shared_client(settings.redis_url).ping())
            else DATABASE_UNAVAILABLE
        )
    except Exception:
        return DATABASE_UNAVAILABLE


def reset_redis_rate_limit_client() -> None:
    global _shared_client, _shared_client_url

    with _client_lock:
        if _shared_client is not None:
            _shared_client.close()
        _shared_client = None
        _shared_client_url = None


def _get_shared_client(redis_url: str) -> Redis[bytes]:
    global _shared_client, _shared_client_url

    with _client_lock:
        if _shared_client is None or _shared_client_url != redis_url:
            if _shared_client is not None:
                _shared_client.close()
            _shared_client = Redis.from_url(
                redis_url,
                socket_connect_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
                socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
                retry_on_timeout=False,
                health_check_interval=30,
                decode_responses=False,
            )
            _shared_client_url = redis_url
        return _shared_client


def _parse_script_result(raw_result: object) -> tuple[bool, int]:
    if (
        not isinstance(raw_result, Sequence)
        or isinstance(raw_result, (str, bytes, bytearray))
        or len(raw_result) != 2
    ):
        raise ValueError("Unexpected Redis rate-limit response.")
    allowed = int(raw_result[0])
    retry_ms = int(raw_result[1])
    if allowed not in (0, 1) or retry_ms < 0:
        raise ValueError("Invalid Redis rate-limit response.")
    return allowed == 1, retry_ms


__all__ = [
    "RATE_LIMIT_WINDOW_SECONDS",
    "RedisRateLimitUnavailable",
    "RedisSlidingWindowRateLimiter",
    "get_redis_rate_limit_status",
    "reset_redis_rate_limit_client",
]
