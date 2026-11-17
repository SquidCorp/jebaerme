from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from jebaerme.api.app import create_app
from jebaerme.db.qdrant import (
    create_qdrant_client,
    ensure_qdrant_ready,
    qdrant_is_ready,
)
from jebaerme.models.env import env


class _UnreachableQdrant:
    def get_collections(self) -> None:
        raise ConnectionError("refused")

    def close(self) -> None:
        return None


class _ReadyQdrant:
    def __init__(self) -> None:
        self.closed = False

    def get_collections(self) -> object:
        return object()

    def close(self) -> None:
        self.closed = True


def test_create_qdrant_client_uses_url(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_client(**kwargs: object) -> MagicMock:
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr("jebaerme.db.qdrant.QdrantClient", fake_client)
    create_qdrant_client("http://example.invalid:6333")
    assert captured["url"] == "http://example.invalid:6333"
    assert captured["timeout"] == 5


def test_create_qdrant_client_defaults_to_settings(
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_client(**kwargs: object) -> MagicMock:
        captured.update(kwargs)
        return MagicMock()

    monkeypatch.setattr("jebaerme.db.qdrant.QdrantClient", fake_client)
    create_qdrant_client()
    assert captured["url"] == env.QDRANT_URL


def test_ensure_qdrant_ready_raises_clear_error() -> None:
    with pytest.raises(RuntimeError, match="Qdrant is unreachable at"):
        ensure_qdrant_ready(_UnreachableQdrant(), url="http://127.0.0.1:6333")


def test_qdrant_is_ready_false_when_unreachable() -> None:
    assert qdrant_is_ready(_UnreachableQdrant()) is False


def test_qdrant_is_ready_true_when_collections_ok() -> None:
    assert qdrant_is_ready(_ReadyQdrant()) is True


def test_lifespan_fails_when_qdrant_unreachable(tmp_path: Path) -> None:
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        qdrant_client=_UnreachableQdrant(),
    )
    with (
        pytest.raises(RuntimeError, match="Qdrant is unreachable"),
        TestClient(app),
    ):
        pass


def test_lifespan_uses_injected_client_and_closes(tmp_path: Path) -> None:
    client = _ReadyQdrant()
    app = create_app(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        qdrant_client=client,
    )
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["qdrant"] == "ok"
    assert client.closed is True
