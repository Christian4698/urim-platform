import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.security import SECURITY_HEADERS, phase_fourteen_security_assertions
from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "URIM",
        "engine_name": "Kairos",
        "phase": "programme-b1-real-sports-data-foundation",
    }

    for header_name, header_value in SECURITY_HEADERS.items():
        assert response.headers[header_name] == header_value


def test_version_endpoint_exposes_phase_fourteen_safety_overrides() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "URIM"
    assert payload["engine_name"] == "Kairos"
    assert payload["default_locale"] == "fr-CD"
    assert payload["default_currency"] == "CDF"
    assert payload["live_enabled"] is False
    assert payload["real_betting_enabled"] is False


def test_readiness_endpoint_reports_unavailable_database_and_preserves_other_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "get_database_status", lambda: "unavailable")

    response = client.get("/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is False
    assert payload["phase"] == "programme-b1-real-sports-data-foundation"
    assert payload["dependencies"]["database"] == "unavailable"
    assert payload["dependencies"]["redis"] == "not_required"
    assert payload["dependencies"]["sports_providers"] == "disabled"
    assert payload["dependencies"]["bookmakers"] == "disabled"
    assert payload["dependencies"]["ml_models"] == "disabled"
    assert payload["dependencies"]["live"] == "disabled"
    assert payload["dependencies"]["real_betting"] == "disabled"
    assert payload["dependencies"]["prediction_creation"] == "disabled"


def test_readiness_endpoint_is_ready_when_database_probe_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main_module, "get_database_status", lambda: "ok")

    response = client.get("/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["dependencies"]["database"] == "ok"


def test_phase_fourteen_security_assertions() -> None:
    assert phase_fourteen_security_assertions() == {
        "providers_disabled": True,
        "bookmakers_disabled": True,
        "ml_disabled": True,
        "live_disabled": True,
        "real_betting_disabled": True,
        "prediction_creation_disabled": True,
        "production_mocks_disabled": True,
    }
