import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_capabilities_keep_dangerous_features_disabled() -> None:
    response = client.get("/api/v1/system/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"] == {
        "app_name": "URIM",
        "engine_name": "Kairos",
        "locale": "fr-CD",
        "currency": "CDF",
        "phase": "phase-3-api-foundation",
    }

    capabilities = payload["capabilities"]
    assert capabilities["providers_enabled"] is False
    assert capabilities["api_football_connected"] is False
    assert capabilities["bookmakers_enabled"] is False
    assert capabilities["ml_enabled"] is False
    assert capabilities["live_enabled"] is False
    assert capabilities["real_betting_enabled"] is False
    assert capabilities["bet_center_mode"] == "virtual_internal_phase_3"
    assert capabilities["prediction_creation_enabled"] is False
    assert capabilities["production_mocks_enabled"] is False
    assert capabilities["production_seed_enabled"] is False
    assert capabilities["post_match_learning_source"] == "post_match_outcomes_only"


@pytest.mark.parametrize(
    ("path", "resource"),
    [
        ("/api/v1/fixtures", "fixtures"),
        ("/api/v1/predictions", "predictions"),
        ("/api/v1/tickets", "tickets"),
        ("/api/v1/providers", "providers"),
        ("/api/v1/post-match/outcomes", "post_match_outcomes"),
    ],
)
def test_skeleton_collections_are_read_only_and_empty(path: str, resource: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["phase"] == "phase-3-api-foundation"
    assert payload["resource"] == resource
    assert payload["status"] == "read_only_skeleton_phase_3"
    assert payload["items"] == []
    assert payload["pagination"] == {"limit": 0, "offset": 0, "total": 0}
    assert payload["safeguards"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/fixtures",
        "/api/v1/predictions",
        "/api/v1/tickets",
        "/api/v1/providers",
        "/api/v1/post-match/outcomes",
    ],
)
def test_dangerous_creation_routes_are_absent(path: str) -> None:
    response = client.post(path, json={})

    assert response.status_code == 405
