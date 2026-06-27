from fastapi.testclient import TestClient

from app.core.security import phase_two_security_assertions
from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "URIM",
        "engine_name": "Kairos",
        "phase": "phase-2-database-migrations",
    }


def test_version_endpoint_exposes_phase_two_flags() -> None:
    response = client.get("/version")

    assert response.status_code == 200
    payload = response.json()
    assert payload["app_name"] == "URIM"
    assert payload["engine_name"] == "Kairos"
    assert payload["default_locale"] == "fr-CD"
    assert payload["default_currency"] == "CDF"
    assert payload["live_enabled"] is False
    assert payload["real_betting_enabled"] is False


def test_readiness_endpoint_has_no_required_real_dependencies() -> None:
    response = client.get("/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["phase"] == "phase-2-database-migrations"
    assert payload["dependencies"]["redis"] == "not_required_phase_2"
    assert payload["dependencies"]["sports_providers"] == "disabled_phase_2"
    assert payload["dependencies"]["bookmakers"] == "disabled_phase_2"
    assert payload["dependencies"]["ml_models"] == "disabled_phase_2"


def test_phase_two_security_assertions() -> None:
    assert phase_two_security_assertions() == {
        "live_disabled": True,
        "real_betting_disabled": True,
        "production_mocks_disabled": True,
    }
