from fastapi.testclient import TestClient

from jebaerme.api.app import create_app
from jebaerme.services.health import get_health


class _ReadyQdrant:
    def get_collections(self) -> object:
        return object()

    def close(self) -> None:
        return None


def test_health_status_ok() -> None:
    health = get_health(qdrant_client=_ReadyQdrant())
    assert health.status == "ok"
    assert health.qdrant == "ok"


def test_health_qdrant_unavailable_without_client() -> None:
    health = get_health()
    assert health.status == "ok"
    assert health.qdrant == "unavailable"


def test_health_endpoint() -> None:
    app = create_app(qdrant_client=_ReadyQdrant())
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "env" in payload
    assert payload["qdrant"] == "ok"
