import asyncio
import logging

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.modules.sports_data.provider import (
    API_FOOTBALL_AUTH_HEADER,
    ApiFootballClient,
    ApiFootballDisabledError,
    ApiFootballQuotaError,
    ApiFootballRateLimitError,
    ApiFootballRequestError,
    ApiFootballValidationError,
    validate_provider_request,
)


def provider_response(
    response: list[object] | None = None,
    *,
    errors: dict[str, str] | None = None,
) -> dict[str, object]:
    rows = response or []
    return {
        "get": "leagues",
        "parameters": {"id": "39"},
        "errors": errors or [],
        "results": len(rows),
        "paging": {"current": 1, "total": 1},
        "response": rows,
    }


def run(coroutine):
    return asyncio.run(coroutine)


def test_client_is_disabled_without_backend_credential() -> None:
    called = False

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json=provider_response())

    async def scenario() -> None:
        client = ApiFootballClient(
            api_key=None,
            enabled=True,
            transport=httpx.MockTransport(handler),
        )
        with pytest.raises(ApiFootballDisabledError):
            async with client:
                pass

    run(scenario())
    assert called is False


def test_client_reads_quota_headers_and_validates_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "v3.football.api-sports.io"
        assert request.url.path == "/leagues"
        assert request.headers[API_FOOTBALL_AUTH_HEADER] == "TEST_ONLY_SECRET"
        return httpx.Response(
            200,
            headers={
                "x-ratelimit-requests-limit": "100",
                "x-ratelimit-requests-remaining": "99",
                "x-ratelimit-limit": "10",
                "x-ratelimit-remaining": "9",
            },
            json=provider_response([{"league": {"id": 39, "name": "Fixture"}}]),
        )

    async def scenario() -> None:
        client = ApiFootballClient(
            api_key="TEST_ONLY_SECRET",
            enabled=True,
            transport=httpx.MockTransport(handler),
        )
        async with client:
            envelope = await client.get("leagues", {"id": 39})
        assert envelope.data.results == 1
        assert envelope.quota_limit_daily == 100
        assert envelope.quota_remaining_daily == 99
        assert envelope.quota_limit_minute == 10
        assert envelope.quota_remaining_minute == 9
        assert len(envelope.raw_hash) == 64
        assert envelope.observed_at <= envelope.available_at <= envelope.fetched_at

    run(scenario())


def test_retry_is_limited_and_uses_backoff() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(503, json={})
        return httpx.Response(200, json=provider_response())

    async def sleeper(delay: float) -> None:
        sleeps.append(delay)

    async def scenario() -> None:
        client = ApiFootballClient(
            api_key="TEST_ONLY_SECRET",
            enabled=True,
            max_retries=1,
            requests_per_minute=10,
            transport=httpx.MockTransport(handler),
            sleeper=sleeper,
            jitter=lambda: 0,
        )
        async with client:
            await client.get("leagues", {"id": 39})
        assert client.request_count == 2

    run(scenario())
    assert attempts == 2
    assert sleeps == [1]


def test_rate_limit_and_provider_errors_are_public_safe(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={
                **provider_response(errors={"rateLimit": "PRIVATE_PROVIDER_BODY"}),
            },
        )

    async def scenario() -> None:
        client = ApiFootballClient(
            api_key="TEST_ONLY_SECRET",
            enabled=True,
            max_retries=0,
            transport=httpx.MockTransport(handler),
        )
        async with client:
            with pytest.raises(ApiFootballRateLimitError) as caught:
                await client.get("leagues", {"id": 39})
        assert "TEST_ONLY_SECRET" not in str(caught.value)
        assert "PRIVATE_PROVIDER_BODY" not in str(caught.value)

    with caplog.at_level(logging.INFO):
        run(scenario())
    assert "TEST_ONLY_SECRET" not in caplog.text
    assert "PRIVATE_PROVIDER_BODY" not in caplog.text


def test_quota_zero_blocks_the_next_request() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            headers={"x-ratelimit-requests-remaining": "0"},
            json=provider_response(),
        )

    async def scenario() -> None:
        client = ApiFootballClient(
            api_key="TEST_ONLY_SECRET",
            enabled=True,
            transport=httpx.MockTransport(handler),
        )
        async with client:
            await client.get("leagues", {"id": 39})
            with pytest.raises(ApiFootballQuotaError):
                await client.get("leagues", {"id": 39})

    run(scenario())
    assert calls == 1


def test_invalid_or_provider_error_responses_are_neutralized() -> None:
    responses = iter(
        [
            httpx.Response(200, json={"unexpected": True}),
            httpx.Response(
                200,
                json=provider_response(errors={"token": "PRIVATE_VALUE"}),
            ),
        ]
    )

    def handler(_request: httpx.Request) -> httpx.Response:
        return next(responses)

    async def scenario() -> None:
        client = ApiFootballClient(
            api_key="TEST_ONLY_SECRET",
            enabled=True,
            transport=httpx.MockTransport(handler),
        )
        async with client:
            with pytest.raises(ApiFootballValidationError):
                await client.get("leagues", {"id": 39})
            with pytest.raises(ApiFootballRequestError) as caught:
                await client.get("leagues", {"id": 39})
            assert "PRIVATE_VALUE" not in str(caught.value)

    run(scenario())


@pytest.mark.parametrize(
    ("endpoint", "params"),
    [
        ("odds", {}),
        ("predictions", {}),
        ("fixtures", {"live": "all"}),
        ("fixtures", {"url": "https://example.test"}),
    ],
)
def test_request_allowlist_blocks_forbidden_surfaces(
    endpoint: str,
    params: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        validate_provider_request(endpoint, params)


def test_settings_keep_api_key_secret_and_require_explicit_enable() -> None:
    settings = Settings(
        api_football_key=SecretStr("TEST_ONLY_SECRET"),
        api_football_enabled=False,
    )
    assert settings.api_football_key_configured is True
    assert settings.api_football_runtime_enabled is False
    assert "TEST_ONLY_SECRET" not in repr(settings)


@pytest.mark.parametrize(
    "overrides",
    [
        {"api_football_priority_competitions": "39,not-an-id"},
        {"api_football_priority_competitions": "39,39"},
        {"api_football_request_timeout_seconds": 31},
        {"api_football_max_retries": 4},
        {"api_football_requests_per_minute": 0},
        {"api_football_max_requests_per_sync": 101},
        {"api_football_upcoming_days": 31},
        {"api_football_freshness_minutes": 0},
    ],
)
def test_settings_fail_fast_on_unbounded_provider_configuration(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        Settings(**overrides)
