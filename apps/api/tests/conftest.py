"""Shared pytest fixtures."""

import pytest
from qdrant_client import QdrantClient

from jebaerme.models.env import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture(autouse=True)
def _offline_qdrant(monkeypatch: pytest.MonkeyPatch) -> None:
    def _memory_client(_url: str | None = None) -> QdrantClient:
        return QdrantClient(":memory:")

    monkeypatch.setattr("jebaerme.api.app.create_qdrant_client", _memory_client)
