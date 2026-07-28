from __future__ import annotations

from dataclasses import dataclass
import re

from sqlalchemy.engine import URL, make_url

_PRODUCTION_ENVS = frozenset({"prod", "production", "live"})
_PRODUCTION_MARKERS = frozenset({"prod", "production", "live", "primary"})
_TEST_MARKERS = frozenset(
    {"ci", "ephemeral", "isolated", "sandbox", "test", "testing"}
)


@dataclass(frozen=True, slots=True)
class DatabaseIsolationResult:
    safe: bool
    reason: str


def validate_isolated_test_database(
    test_database_url: str | None,
    *,
    database_url: str | None,
    app_env: str | None,
) -> DatabaseIsolationResult:
    """Validate a test PostgreSQL target without returning or logging its URL."""
    if not test_database_url:
        return DatabaseIsolationResult(False, "B1_TEST_DATABASE_URL_MISSING")

    environment_tokens = frozenset(
        token
        for token in re.split(
            r"[^a-z0-9]+",
            (app_env or "").strip().casefold(),
        )
        if token
    )
    if environment_tokens & _PRODUCTION_ENVS:
        return DatabaseIsolationResult(False, "APP_ENV_PRODUCTION_LIKE")

    if database_url and test_database_url.strip() == database_url.strip():
        return DatabaseIsolationResult(False, "MATCHES_DATABASE_URL")

    test_url = _parse_postgresql_url(test_database_url)
    if test_url is None:
        return DatabaseIsolationResult(
            False,
            "B1_TEST_DATABASE_URL_INVALID_OR_NOT_POSTGRESQL",
        )

    if database_url:
        production_url = _parse_postgresql_url(database_url)
        if production_url is None:
            return DatabaseIsolationResult(False, "DATABASE_URL_INVALID")
        if _same_database_target(test_url, production_url):
            return DatabaseIsolationResult(
                False,
                "MATCHES_DATABASE_URL_TARGET",
            )

    target_tokens = _target_tokens(test_url)
    if target_tokens & _PRODUCTION_MARKERS:
        return DatabaseIsolationResult(
            False,
            "B1_TEST_DATABASE_URL_PRODUCTION_LIKE",
        )
    if not target_tokens & _TEST_MARKERS:
        return DatabaseIsolationResult(
            False,
            "B1_TEST_DATABASE_URL_NOT_EXPLICITLY_ISOLATED",
        )

    return DatabaseIsolationResult(True, "ISOLATED_TEST_DATABASE_CONFIRMED")


def _parse_postgresql_url(value: str) -> URL | None:
    try:
        parsed = make_url(value.strip())
    except Exception:
        return None
    if parsed.get_backend_name() != "postgresql":
        return None
    if not parsed.database:
        return None
    return parsed


def _same_database_target(left: URL, right: URL) -> bool:
    return (
        (left.host or "").casefold(),
        left.port or 5432,
        left.database,
    ) == (
        (right.host or "").casefold(),
        right.port or 5432,
        right.database,
    )


def _target_tokens(url: URL) -> frozenset[str]:
    target = f"{url.host or ''} {url.database or ''}".casefold()
    return frozenset(
        token for token in re.split(r"[^a-z0-9]+", target) if token
    )


__all__ = [
    "DatabaseIsolationResult",
    "validate_isolated_test_database",
]
