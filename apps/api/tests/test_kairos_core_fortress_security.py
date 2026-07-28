from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Event, Lock
from types import SimpleNamespace
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.api.v1.routes.kairos as kairos_routes
from app.main import _openapi_paths, app
from app.modules.kairos.repository import KairosRepository

client = TestClient(app)

KAIROS_ANALYSIS_PATH = "/api/v1/kairos/matches/999/analysis"
KAIROS_METHODOLOGY_PATH = "/api/v1/kairos/methodology"
KAIROS_SUGGESTIONS_PATH = "/api/v1/kairos/suggestions/today"
SECRET_MARKER = "FORTRESS_PRIVATE_PASSWORD"  # pragma: allowlist secret


class _AllowAllLimiter:
    def retry_after(self, client_key: str) -> None:
        return None


class _CountingLimiter:
    def __init__(self, *, limit: int) -> None:
        self.limit = limit
        self.count = 0

    def retry_after(self, client_key: str) -> int | None:
        self.count += 1
        return 60 if self.count > self.limit else None


@pytest.fixture(autouse=True)
def allow_rate_limited_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        kairos_routes,
        "_METHODOLOGY_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_ANALYSIS_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_SUGGESTIONS_RATE_LIMITER",
        _AllowAllLimiter(),
    )


def _forbid_database_session(
    monkeypatch: pytest.MonkeyPatch,
) -> list[bool]:
    calls: list[bool] = []

    def forbidden_factory() -> None:
        calls.append(True)
        raise AssertionError("invalid requests must not open a DB session")

    monkeypatch.setattr(
        kairos_routes,
        "get_session_factory",
        forbidden_factory,
    )
    return calls


@pytest.mark.parametrize(
    "provider_match_id",
    (
        "0",
        "-1",
        "+1",
        "01",
        "1e3",
        "9223372036854775808",
        "999999999999999999999999999999999999999999",
        "1%27%20OR%201%3D1--",
        "1%20UNION%20SELECT%20NULL",
        "%EF%BC%91",
    ),
)
def test_adversarial_provider_match_ids_are_rejected_without_database_access(
    provider_match_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)

    response = client.get(
        f"/api/v1/kairos/matches/{provider_match_id}/analysis"
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "kairos_request_invalid"
    assert len(response.content) < 256
    assert calls == []


def test_oversized_path_input_is_not_reflected_or_amplified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)
    payload = "9" * 5_000

    response = client.get(
        f"/api/v1/kairos/matches/{payload}/analysis"
    )

    assert response.status_code == 422
    assert payload not in response.text
    assert len(response.content) < 256
    assert calls == []


@pytest.mark.parametrize(
    "as_of",
    (
        "",
        "not-a-date",
        "NaN",
        "Infinity",
        "2026-07-27T12:00:00",
        "2026-07-27T12:00:60Z",
        "0001-01-01T00:00:00%2B14:00",
        "0001-01-01T00:00:00Z",
        "9999-12-31T23:59:59-14:00",
        "999999999999999999999999999999999999999999",
        "2026-07-27T12:00:00Z%27%20OR%201%3D1--",
    ),
)
def test_invalid_extreme_or_injectable_as_of_is_safely_rejected(
    as_of: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)

    response = client.get(f"{KAIROS_ANALYSIS_PATH}?as_of={as_of}")

    assert response.status_code == 422
    assert len(response.content) < 512
    assert SECRET_MARKER not in response.text
    assert calls == []


@pytest.mark.parametrize(
    "path",
    (
        f"{KAIROS_ANALYSIS_PATH}?debug=true",
        f"{KAIROS_ANALYSIS_PATH}?as_of=2026-07-27T10%3A00%3A00Z"
        "&as_of=2026-07-27T11%3A00%3A00Z",
        f"{KAIROS_ANALYSIS_PATH}?as_of=2026-07-27T10%3A00%3A00Z"
        "&debug=true",
        f"{KAIROS_METHODOLOGY_PATH}?as_of=2026-07-27T10%3A00%3A00Z",
        f"{KAIROS_SUGGESTIONS_PATH}?limit=999999",
    ),
)
def test_unknown_or_duplicate_query_parameters_are_rejected_before_database(
    path: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)

    response = client.get(path)

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == (
        "kairos_query_parameters_invalid"
    )
    assert len(response.content) < 256
    assert calls == []


@pytest.mark.parametrize(
    "method",
    ("POST", "PUT", "PATCH", "DELETE", "HEAD", "TRACE"),
)
@pytest.mark.parametrize(
    "path",
    (
        KAIROS_METHODOLOGY_PATH,
        KAIROS_SUGGESTIONS_PATH,
        KAIROS_ANALYSIS_PATH,
    ),
)
def test_only_get_is_exposed_for_kairos_routes(
    method: str,
    path: str,
) -> None:
    response = client.request(
        method,
        path,
        headers={"X-HTTP-Method-Override": "GET"},
    )

    assert response.status_code == 405


@pytest.mark.parametrize(
    "path",
    (
        KAIROS_METHODOLOGY_PATH,
        f"{KAIROS_SUGGESTIONS_PATH}?debug=true",
        "/api/v1/kairos/matches/not-an-integer/analysis",
    ),
)
def test_kairos_responses_are_not_cacheable_and_have_security_headers(
    path: str,
) -> None:
    response = client.get(path)

    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["content-security-policy"].startswith(
        "default-src 'none'"
    )
    assert response.headers["permissions-policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )


@pytest.mark.parametrize(
    "origin",
    (
        "https://attacker.invalid",
        "null",
        "https://urim.pro.attacker.invalid",
        "https://urim.pro.",
    ),
)
def test_kairos_cors_rejects_untrusted_origin(origin: str) -> None:
    response = client.get(
        KAIROS_METHODOLOGY_PATH,
        headers={"Origin": origin},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_kairos_cors_rejects_mutating_preflight() -> None:
    response = client.options(
        KAIROS_ANALYSIS_PATH,
        headers={
            "Origin": "https://urim.pro",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "POST" not in response.headers["access-control-allow-methods"]


def test_openapi_exposes_only_get_for_kairos_and_no_sensitive_configuration() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    for path in (
        KAIROS_METHODOLOGY_PATH,
        KAIROS_SUGGESTIONS_PATH,
        "/api/v1/kairos/matches/{provider_match_id}/analysis",
    ):
        assert set(document["paths"][path]) == {"get"}
    serialized = response.text.lower()
    for forbidden in (
        "database_url",
        "api_football_key",
        "password",
        "authorization",
        "automatic_betting_enabled\":true",
        "live_automatic_enabled\":true",
    ):
        assert forbidden not in serialized


def test_openapi_is_disabled_outside_development_environments() -> None:
    assert _openapi_paths("production") == (None, None, None)
    assert _openapi_paths("staging") == (None, None, None)
    assert _openapi_paths("development") == (
        "/openapi.json",
        "/docs",
        "/redoc",
    )


def test_methodology_response_is_bounded_and_contains_no_secret() -> None:
    response = client.get(KAIROS_METHODOLOGY_PATH)

    assert response.status_code == 200
    assert len(response.content) < 32_000
    serialized = response.text.lower()
    assert "database_url" not in serialized
    assert "api_football_key" not in serialized
    assert "password" not in serialized
    assert response.json()["db_writes"] is False
    assert response.json()["provider_calls"] is False
    assert response.json()["automatic_betting_enabled"] is False
    assert response.json()["live_automatic_enabled"] is False


def test_concurrency_bulkhead_rejects_excess_work_before_database(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)
    acquired = 0
    try:
        for _ in range(kairos_routes.MAX_CONCURRENT_KAIROS_ANALYSES):
            assert kairos_routes._ANALYSIS_CAPACITY.acquire(blocking=False)
            acquired += 1

        response = client.get(KAIROS_ANALYSIS_PATH)

        assert response.status_code == 429
        assert response.headers["retry-after"] == "1"
        assert response.json()["detail"]["code"] == (
            "kairos_capacity_exceeded"
        )
        assert calls == []
    finally:
        for _ in range(acquired):
            kairos_routes._ANALYSIS_CAPACITY.release()


def test_concurrent_http_calls_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    all_started = Event()
    release = Event()
    counter_lock = Lock()
    started_count = 0

    def blocking_load(
        _self,
        provider_match_id,
        as_of,
        recent_window,
    ) -> None:
        nonlocal started_count
        with counter_lock:
            started_count += 1
            if (
                started_count
                == kairos_routes.MAX_CONCURRENT_KAIROS_ANALYSES
            ):
                all_started.set()
        assert release.wait(timeout=5)
        return None

    monkeypatch.setattr(
        kairos_routes,
        "_ANALYSIS_RATE_LIMITER",
        _AllowAllLimiter(),
    )
    monkeypatch.setattr(
        kairos_routes,
        "_session",
        lambda: nullcontext(object()),
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset",
        blocking_load,
    )

    with ThreadPoolExecutor(
        max_workers=kairos_routes.MAX_CONCURRENT_KAIROS_ANALYSES + 1
    ) as executor:
        blocked = [
            executor.submit(client.get, KAIROS_ANALYSIS_PATH)
            for _ in range(
                kairos_routes.MAX_CONCURRENT_KAIROS_ANALYSES
            )
        ]
        try:
            assert all_started.wait(timeout=5)
            rejected = executor.submit(
                client.get,
                KAIROS_ANALYSIS_PATH,
            ).result(timeout=5)
            assert rejected.status_code == 429
            assert rejected.json()["detail"]["code"] == (
                "kairos_capacity_exceeded"
            )
        finally:
            release.set()
        assert [future.result(timeout=5).status_code for future in blocked] == [
            404
        ] * kairos_routes.MAX_CONCURRENT_KAIROS_ANALYSES


def test_rate_limit_is_enforced_with_bounded_retry_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limiter = _CountingLimiter(limit=2)
    monkeypatch.setattr(
        kairos_routes,
        "_METHODOLOGY_RATE_LIMITER",
        limiter,
    )

    assert client.get(KAIROS_METHODOLOGY_PATH).status_code == 200
    assert client.get(KAIROS_METHODOLOGY_PATH).status_code == 200
    response = client.get(KAIROS_METHODOLOGY_PATH)

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == (
        "kairos_rate_limit_exceeded"
    )
    assert 1 <= int(response.headers["retry-after"]) <= 60
    assert response.headers["cache-control"] == "no-store"


def test_analysis_rate_limit_rejects_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)
    limiter = _CountingLimiter(limit=1)
    assert limiter.retry_after("testclient") is None
    monkeypatch.setattr(
        kairos_routes,
        "_ANALYSIS_RATE_LIMITER",
        limiter,
    )

    response = client.get(KAIROS_ANALYSIS_PATH)

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == (
        "kairos_rate_limit_exceeded"
    )
    assert calls == []


def test_daily_suggestions_rate_limit_rejects_before_database_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _forbid_database_session(monkeypatch)
    limiter = _CountingLimiter(limit=1)
    assert limiter.retry_after("testclient") is None
    monkeypatch.setattr(
        kairos_routes,
        "_SUGGESTIONS_RATE_LIMITER",
        limiter,
    )

    response = client.get(KAIROS_SUGGESTIONS_PATH)

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == (
        "kairos_rate_limit_exceeded"
    )
    assert calls == []


class _RecordingPostgresSession:
    def __init__(self, *, fail_execute: bool = False) -> None:
        self.statements: list[tuple[str, dict[str, str] | None]] = []
        self.closed = False
        self.fail_execute = fail_execute

    def get_bind(self) -> SimpleNamespace:
        return SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    def execute(
        self,
        statement: Any,
        parameters: dict[str, str] | None = None,
    ) -> None:
        if self.fail_execute:
            raise RuntimeError(
                f"{SECRET_MARKER} host=private-postgres.internal"
            )
        self.statements.append((str(statement), parameters))

    def close(self) -> None:
        self.closed = True


def test_postgresql_analysis_session_is_read_only_and_time_bounded() -> None:
    session = _RecordingPostgresSession()

    kairos_routes._configure_read_only_session(cast(Session, session))

    assert session.statements == [
        ("SET TRANSACTION READ ONLY", None),
        (
            "SELECT set_config('statement_timeout', "
            ":statement_timeout, true)",
            {"statement_timeout": "3000ms"},
        ),
    ]


def test_postgresql_session_hardening_failure_is_public_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _RecordingPostgresSession(fail_execute=True)
    monkeypatch.setattr(
        kairos_routes,
        "get_session_factory",
        lambda: lambda: cast(Session, session),
    )

    response = client.get(KAIROS_ANALYSIS_PATH)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "kairos_data_unavailable"
    assert SECRET_MARKER not in response.text
    assert "private-postgres.internal" not in response.text
    assert session.closed is True


class _CloseFailingSession:
    def get_bind(self) -> SimpleNamespace:
        return SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))

    def close(self) -> None:
        raise RuntimeError(f"{SECRET_MARKER} close failure")


def test_session_close_failure_is_public_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _CloseFailingSession()
    monkeypatch.setattr(
        kairos_routes,
        "get_session_factory",
        lambda: lambda: cast(Session, session),
    )
    monkeypatch.setattr(
        KairosRepository,
        "load_match_dataset",
        lambda _self, provider_match_id, as_of, recent_window: None,
    )

    response = client.get(KAIROS_ANALYSIS_PATH)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "kairos_data_unavailable"
    assert SECRET_MARKER not in response.text


def test_internal_failure_details_are_not_written_to_application_logs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def fail_session_factory() -> None:
        raise RuntimeError(f"{SECRET_MARKER} host=private.internal")

    monkeypatch.setattr(
        kairos_routes,
        "get_session_factory",
        fail_session_factory,
    )

    response = client.get(KAIROS_ANALYSIS_PATH)

    assert response.status_code == 503
    assert SECRET_MARKER not in response.text
    assert SECRET_MARKER not in caplog.text
    assert "private.internal" not in caplog.text
