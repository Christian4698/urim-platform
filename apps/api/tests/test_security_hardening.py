import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.cors import normalize_cors_origins
from app.core.security import SECURITY_HEADERS, add_cors
from app.db.session import reset_database_engine
from app.main import app

client = TestClient(app)

PUBLIC_GET_ENDPOINTS = (
    "/health",
    "/version",
    "/readiness",
    "/api/v1/system/capabilities",
    "/api/v1/fixtures",
    "/api/v1/predictions",
    "/api/v1/tickets",
    "/api/v1/providers",
    "/api/v1/providers/readiness",
    "/api/v1/providers/sandbox/status",
    "/api/v1/post-match/outcomes",
)

DANGEROUS_POST_ENDPOINTS = (
    "/api/v1/system/capabilities",
    "/api/v1/fixtures",
    "/api/v1/predictions",
    "/api/v1/tickets",
    "/api/v1/providers",
    "/api/v1/providers/readiness",
    "/api/v1/providers/sandbox/status",
    "/api/v1/post-match/outcomes",
)

SECRET_TOKENS = (
    "DATABASE_URL",
    "postgresql+psycopg",
    "urim_local_only",
    "api_key",
    "password",
    "provider_credentials",
    "PROVIDER_API_KEY",
    "PROVIDER_API_SECRET",
    "PROVIDER_WEBHOOK_SECRET",
    "PROVIDER_CLIENT_ID",
    "PROVIDER_CLIENT_SECRET",
    "URIM_API_FOOTBALL_SMOKE_ENABLED",
    "URIM_API_FOOTBALL_SMOKE_AUTH",
    "URIM_API_FOOTBALL_SMOKE_BASE_URL",
    "URIM_API_FOOTBALL_SMOKE_READ_ONLY",
    "URIM_API_FOOTBALL_SMOKE_NON_PROD",
    "DEMO_NON_PROD_FAKE_API_KEY_VALUE",
    "DEMO_NON_PROD_FAKE_TOKEN",
    "DEMO_NON_PROD_FAKE_PASSWORD",
    "DEMO_NON_PROD_FAKE_PHASE14_API_KEY",
    "DEMO_NON_PROD_FAKE_PHASE14_API_SECRET",
    "DEMO_NON_PROD_FAKE_PHASE14_WEBHOOK_SECRET",
    "DEMO_NON_PROD_FAKE_PHASE14_CLIENT_ID",
    "DEMO_NON_PROD_FAKE_PHASE14_CLIENT_SECRET",
    "DEMO_NON_PROD_FAKE_PHASE18_AUTH_MATERIAL",
    "DEMO_NON_PROD_FAKE_PHASE19_AUTH_MATERIAL",
    "DEMO_NON_PROD_FAKE_PHASE23_AUTH_MATERIAL",
    "DEMO_NON_PROD_FAKE_PHASE23_PROVIDER_REFERENCE",
    "DEMO_NON_PROD_FAKE_PHASE24_AUTH_MATERIAL",
    "DEMO_NON_PROD_FAKE_PHASE24_PROVIDER_REFERENCE",
    "example.invalid",
)


@pytest.mark.parametrize("path", PUBLIC_GET_ENDPOINTS)
def test_public_get_endpoints_include_phase_fourteen_security_headers(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    for header_name, header_value in SECURITY_HEADERS.items():
        assert response.headers[header_name] == header_value


@pytest.mark.parametrize("path", PUBLIC_GET_ENDPOINTS)
def test_public_get_response_bodies_do_not_expose_secrets(path: str) -> None:
    response = client.get(path)
    body = response.text.lower()

    assert response.status_code == 200
    for token in SECRET_TOKENS:
        assert token.lower() not in body


@pytest.mark.parametrize("path", DANGEROUS_POST_ENDPOINTS)
def test_dangerous_post_endpoints_remain_absent(path: str) -> None:
    response = client.post(path, json={})

    assert response.status_code == 405


def test_version_and_capabilities_ignore_dangerous_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "enable_live", True)
    monkeypatch.setattr(settings, "enable_real_betting", True)
    monkeypatch.setattr(settings, "allow_production_mocks", True)

    version_response = client.get("/version")
    capabilities_response = client.get("/api/v1/system/capabilities")

    assert version_response.status_code == 200
    assert capabilities_response.status_code == 200
    assert version_response.json()["live_enabled"] is False
    assert version_response.json()["real_betting_enabled"] is False

    capabilities = capabilities_response.json()["capabilities"]
    assert capabilities["providers_enabled"] is False
    assert capabilities["api_football_connected"] is False
    assert capabilities["bookmakers_enabled"] is False
    assert capabilities["ml_enabled"] is False
    assert capabilities["live_enabled"] is False
    assert capabilities["real_betting_enabled"] is False
    assert capabilities["prediction_creation_enabled"] is False
    assert capabilities["production_mocks_enabled"] is False
    assert capabilities["production_seed_enabled"] is False
    assert capabilities["bet_center_mode"] == "virtual_internal"


def test_readiness_database_failure_exposes_no_connection_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "DO_NOT_EXPOSE_READINESS_PASSWORD"
    host = "private-db.internal.example"
    monkeypatch.setattr(
        settings,
        "database_url",
        f"unsupported://readiness-user:{secret}@{host}:5432/urim",
    )
    reset_database_engine()

    try:
        response = client.get("/readiness")
    finally:
        reset_database_engine()

    assert response.status_code == 200
    assert response.json()["ready"] is False
    assert response.json()["dependencies"]["database"] == "unavailable"
    assert secret not in response.text
    assert host not in response.text


@pytest.mark.parametrize(
    "allowed_origin",
    (
        "http://localhost:3000",
        "https://urim.pro",
        "https://www.urim.pro",
        "https://urim-web.onrender.com",
    ),
)
def test_cors_allows_only_configured_frontend_origins(allowed_origin: str) -> None:
    allowed_response = client.get("/health", headers={"Origin": allowed_origin})
    denied_response = client.get(
        "/health",
        headers={"Origin": "https://untrusted.example"},
    )

    assert allowed_response.status_code == 200
    assert allowed_response.headers["access-control-allow-origin"] == allowed_origin
    assert denied_response.status_code == 200
    assert "access-control-allow-origin" not in denied_response.headers


def test_cors_preflight_allows_get_without_wildcard() -> None:
    origin = "http://localhost:3000"
    response = client.options(
        "/readiness",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "GET" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-origin"] != "*"


def test_cors_rejects_wildcard_configuration() -> None:
    isolated_app = FastAPI()

    with pytest.raises(ValueError, match="Wildcard CORS origins are not allowed"):
        add_cors(isolated_app, ("*",))


@pytest.mark.parametrize(
    "origin",
    (
        "https://*.urim.pro",
        "https://user:password@urim.pro",
        "https://urim.pro/path",
        "https://urim.pro?debug=true",
        "javascript://urim.pro",
        "not-an-origin",
        "",
    ),
)
def test_cors_rejects_non_exact_or_empty_origins(origin: str) -> None:
    with pytest.raises(ValueError):
        normalize_cors_origins(origin)


def test_cors_normalizes_and_deduplicates_exact_origins() -> None:
    assert normalize_cors_origins(
        " https://URIM.PRO/,http://localhost:3000,https://urim.pro "
    ) == ("https://urim.pro", "http://localhost:3000")


def test_cors_allows_official_production_origins() -> None:
    production_app = FastAPI()
    production_origins = ("https://urim.pro", "https://www.urim.pro")
    add_cors(production_app, production_origins)
    production_client = TestClient(production_app)

    @production_app.get("/health")
    def isolated_health() -> dict[str, str]:
        return {"status": "ok"}

    for origin in production_origins:
        response = production_client.get("/health", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin
