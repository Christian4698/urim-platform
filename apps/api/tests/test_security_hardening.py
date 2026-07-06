import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import SECURITY_HEADERS
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
