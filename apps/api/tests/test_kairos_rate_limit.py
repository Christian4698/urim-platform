from __future__ import annotations

from typing import Any

import pytest

from app.modules.kairos.rate_limit import (
    RATE_LIMIT_WINDOW_SECONDS,
    REDIS_KEY_PREFIX,
    RedisRateLimitUnavailable,
    RedisSlidingWindowRateLimiter,
)


class _FakeRedis:
    def __init__(
        self,
        result: object = (1, 0),
        *,
        failure: Exception | None = None,
    ) -> None:
        self.result = result
        self.failure = failure
        self.calls: list[tuple[str, int, tuple[Any, ...]]] = []

    def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: object,
    ) -> object:
        self.calls.append((script, numkeys, keys_and_args))
        if self.failure is not None:
            raise self.failure
        return self.result

    def ping(self) -> bool:
        return True


def test_distributed_limiter_uses_atomic_redis_time_script_and_hashed_client() -> None:
    redis = _FakeRedis()
    limiter = RedisSlidingWindowRateLimiter(
        scope="analysis",
        limit=30,
        redis_url="redis://placeholder.invalid",
        client=redis,
    )

    assert limiter.retry_after("198.51.100.42") is None

    script, numkeys, arguments = redis.calls[0]
    key, window_ms, limit, member = arguments
    assert numkeys == 1
    assert "redis.call('TIME')" in script
    assert "ZREMRANGEBYSCORE" in script
    assert "ZADD" in script
    assert str(key).startswith(f"{REDIS_KEY_PREFIX}:analysis:")
    assert "198.51.100.42" not in str(key)
    assert window_ms == RATE_LIMIT_WINDOW_SECONDS * 1_000
    assert limit == 30
    assert len(str(member)) == 32


@pytest.mark.parametrize(
    ("retry_ms", "expected_seconds"),
    ((1, 1), (1_001, 2), (60_000, 60), (99_999, 60)),
)
def test_distributed_limiter_returns_bounded_retry_after(
    retry_ms: int,
    expected_seconds: int,
) -> None:
    limiter = RedisSlidingWindowRateLimiter(
        scope="methodology",
        limit=120,
        client=_FakeRedis((0, retry_ms)),
    )

    assert limiter.retry_after("client") == expected_seconds


def test_distributed_limiter_fails_closed_without_redis_configuration() -> None:
    limiter = RedisSlidingWindowRateLimiter(
        scope="analysis",
        limit=30,
    )

    with pytest.raises(RedisRateLimitUnavailable):
        limiter.retry_after("client")


def test_distributed_limiter_fails_closed_on_invalid_redis_url() -> None:
    limiter = RedisSlidingWindowRateLimiter(
        scope="analysis",
        limit=30,
        redis_url="not-a-redis-url",
    )

    with pytest.raises(RedisRateLimitUnavailable):
        limiter.retry_after("client")


@pytest.mark.parametrize(
    "result",
    (None, (), (2, 0), (1, -1), ("unexpected", "response")),
)
def test_distributed_limiter_fails_closed_on_invalid_redis_response(
    result: object,
) -> None:
    limiter = RedisSlidingWindowRateLimiter(
        scope="analysis",
        limit=30,
        client=_FakeRedis(result),
    )

    with pytest.raises(RedisRateLimitUnavailable):
        limiter.retry_after("client")


def test_distributed_limiter_neutralizes_redis_failure_details() -> None:
    limiter = RedisSlidingWindowRateLimiter(
        scope="analysis",
        limit=30,
        client=_FakeRedis(
            failure=RuntimeError(
                "password=PRIVATE redis://private.internal"
            )
        ),
    )

    with pytest.raises(
        RedisRateLimitUnavailable,
        match="Redis rate limiting is unavailable",
    ) as captured:
        limiter.retry_after("client")

    assert "PRIVATE" not in str(captured.value)
    assert "private.internal" not in str(captured.value)


def test_production_limits_remain_30_analysis_and_120_methodology() -> None:
    analysis = RedisSlidingWindowRateLimiter(
        scope="analysis",
        limit=30,
        client=_FakeRedis(),
    )
    methodology = RedisSlidingWindowRateLimiter(
        scope="methodology",
        limit=120,
        client=_FakeRedis(),
    )

    assert analysis.limit == 30
    assert methodology.limit == 120
