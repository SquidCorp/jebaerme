from fastapi.testclient import TestClient

from jebaerme.api.app import create_app
from jebaerme.services.health import get_health


def test_health_status_ok() -> None:
    health = get_health()
    assert health.status == "ok"


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "env" in payload
