from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import ipaddress
import os
from urllib.parse import urlsplit
from uuid import uuid4

from redis import Redis

from app.modules.kairos.rate_limit import (
    RATE_LIMIT_WINDOW_SECONDS,
    REDIS_KEY_PREFIX,
    RedisRateLimitUnavailable,
    RedisSlidingWindowRateLimiter,
)

REDIS_ENV_NAME = "REDIS_URL"
SOCKET_TIMEOUT_SECONDS = 3.0
CONCURRENT_REQUEST_COUNT = 64
CONCURRENT_WORKERS = 16
LOCAL_HOSTNAMES = frozenset(
    {
        "host.docker.internal",
        "localhost",
        "localhost.localdomain",
        "redis",
    }
)
PLACEHOLDER_HOST_MARKERS = frozenset(
    {
        "changeme",
        "dummy",
        "example",
        "fake",
        "invalid",
        "placeholder",
    }
)


@dataclass(slots=True)
class RedisGateEvidence:
    ping: bool = False
    atomic_concurrency: bool = False
    ttl: bool = False
    limit_30: bool = False
    limit_120: bool = False
    client_hash: bool = False
    fail_closed: bool = False
    cleanup: bool = False

    @property
    def passed(self) -> bool:
        return all(
            (
                self.ping,
                self.atomic_concurrency,
                self.ttl,
                self.limit_30,
                self.limit_120,
                self.client_hash,
                self.fail_closed,
                self.cleanup,
            )
        )


def validate_redis_url(value: str | None) -> tuple[bool, str]:
    if value is None or not value.strip():
        return False, "REDIS_URL_MISSING"
    normalized = value.strip()
    if any(character in normalized for character in ("\x00", "\r", "\n")):
        return False, "REDIS_URL_INVALID"
    try:
        parsed = urlsplit(normalized)
        hostname = (parsed.hostname or "").casefold()
        _ = parsed.port
    except ValueError:
        return False, "REDIS_URL_INVALID"
    if parsed.scheme.casefold() not in {"redis", "rediss"} or not hostname:
        return False, "REDIS_URL_INVALID"
    if parsed.fragment:
        return False, "REDIS_URL_INVALID"
    if (
        hostname in LOCAL_HOSTNAMES
        or hostname.endswith(".localhost")
        or hostname.endswith(".local")
    ):
        return False, "REDIS_URL_LOCAL_FORBIDDEN"
    if any(marker in hostname for marker in PLACEHOLDER_HOST_MARKERS):
        return False, "REDIS_URL_PLACEHOLDER_FORBIDDEN"
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        address = None
    if address is not None and (
        address.is_loopback or address.is_unspecified or address.is_link_local
    ):
        return False, "REDIS_URL_LOCAL_FORBIDDEN"
    return True, "REDIS_URL_ACCEPTED"


def run_redis_gate(redis_url: str) -> RedisGateEvidence:
    evidence = RedisGateEvidence(fail_closed=_fail_closed_probe())
    client: Redis[bytes] | None = None
    created_keys: list[str] = []
    try:
        client = Redis.from_url(
            redis_url,
            socket_connect_timeout=SOCKET_TIMEOUT_SECONDS,
            socket_timeout=SOCKET_TIMEOUT_SECONDS,
            retry_on_timeout=False,
            health_check_interval=30,
            decode_responses=False,
        )
        evidence.ping = bool(client.ping())
        if not evidence.ping:
            return evidence

        token = uuid4().hex
        client_key = f"render-gate-client-{token}"
        digest = hashlib.sha256(client_key.encode("utf-8")).hexdigest()

        scope_30 = f"rendergate30{token}"
        key_30 = _expected_key(scope_30, digest)
        created_keys.append(key_30)
        limiter_30 = RedisSlidingWindowRateLimiter(
            scope=scope_30,
            limit=30,
            client=client,
        )
        outcomes_30 = [
            limiter_30.retry_after(client_key) for _ in range(31)
        ]
        evidence.limit_30 = (
            sum(outcome is None for outcome in outcomes_30) == 30
            and outcomes_30[-1] is not None
        )
        ttl_30 = int(client.pttl(key_30))

        scope_120 = f"rendergate120{token}"
        key_120 = _expected_key(scope_120, digest)
        created_keys.append(key_120)
        limiter_120 = RedisSlidingWindowRateLimiter(
            scope=scope_120,
            limit=120,
            client=client,
        )
        outcomes_120 = [
            limiter_120.retry_after(client_key) for _ in range(121)
        ]
        evidence.limit_120 = (
            sum(outcome is None for outcome in outcomes_120) == 120
            and outcomes_120[-1] is not None
        )
        ttl_120 = int(client.pttl(key_120))

        concurrent_scope = f"rendergateconcurrent{token}"
        concurrent_key = _expected_key(concurrent_scope, digest)
        created_keys.append(concurrent_key)
        concurrent_limiter = RedisSlidingWindowRateLimiter(
            scope=concurrent_scope,
            limit=30,
            client=client,
        )
        with ThreadPoolExecutor(
            max_workers=CONCURRENT_WORKERS
        ) as executor:
            concurrent_outcomes = list(
                executor.map(
                    lambda _: concurrent_limiter.retry_after(client_key),
                    range(CONCURRENT_REQUEST_COUNT),
                )
            )
        allowed = sum(
            outcome is None for outcome in concurrent_outcomes
        )
        denied = len(concurrent_outcomes) - allowed
        evidence.atomic_concurrency = allowed == 30 and denied == 34
        ttl_concurrent = int(client.pttl(concurrent_key))

        maximum_ttl = RATE_LIMIT_WINDOW_SECONDS * 1_000
        evidence.ttl = all(
            0 < ttl <= maximum_ttl
            for ttl in (ttl_30, ttl_120, ttl_concurrent)
        )
        evidence.client_hash = (
            bool(client.exists(key_30))
            and client_key not in key_30
            and key_30.endswith(digest)
        )
    except Exception:
        return evidence
    finally:
        if client is not None:
            evidence.cleanup = _cleanup_gate_keys(client, created_keys)
            try:
                client.close()
            except Exception:
                evidence.cleanup = False
        elif not created_keys:
            evidence.cleanup = True
    return evidence


def _expected_key(scope: str, digest: str) -> str:
    return f"{REDIS_KEY_PREFIX}:{scope}:{digest}"


def _cleanup_gate_keys(
    client: Redis[bytes],
    keys: list[str],
) -> bool:
    if not keys:
        return True
    expected_prefix = f"{REDIS_KEY_PREFIX}:rendergate"
    if not all(key.startswith(expected_prefix) for key in keys):
        return False
    try:
        client.delete(*keys)
        return all(not bool(client.exists(key)) for key in keys)
    except Exception:
        return False


def _fail_closed_probe() -> bool:
    canary = "render-gate-sensitive-canary"

    class _UnavailableRedis:
        def eval(
            self,
            script: str,
            numkeys: int,
            *keys_and_args: object,
        ) -> object:
            raise RuntimeError(canary)

        def ping(self) -> bool:
            return False

    limiter = RedisSlidingWindowRateLimiter(
        scope="rendergatefailclosed",
        limit=1,
        client=_UnavailableRedis(),
    )
    try:
        limiter.retry_after("render-gate-client")
    except RedisRateLimitUnavailable as exc:
        return canary not in str(exc)
    return False


def main() -> int:
    redis_url = os.environ.get(REDIS_ENV_NAME)
    present = bool(redis_url and redis_url.strip())
    print(f"REDIS_URL_PRESENT={str(present).lower()}")
    valid, reason = validate_redis_url(redis_url)
    print(f"REDIS_URL_VALID={str(valid).lower()}")
    if not valid:
        print("REDIS_GATE_STATUS=REFUSED")
        print(f"REDIS_GATE_REASON={reason}")
        return 2

    assert redis_url is not None
    evidence = run_redis_gate(redis_url)
    for name in (
        "ping",
        "atomic_concurrency",
        "ttl",
        "limit_30",
        "limit_120",
        "client_hash",
        "fail_closed",
        "cleanup",
    ):
        print(
            f"REDIS_{name.upper()}="
            f"{str(getattr(evidence, name)).lower()}"
        )
    print(f"REDIS_GATE_STATUS={'PASS' if evidence.passed else 'FAIL'}")
    print(
        "REDIS_GATE_REASON="
        f"{'ALL_CHECKS_PASSED' if evidence.passed else 'RUNTIME_CHECK_FAILED'}"
    )
    return 0 if evidence.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
