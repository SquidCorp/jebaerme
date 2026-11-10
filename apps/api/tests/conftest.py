"""Shared pytest fixtures."""

from unittest.mock import MagicMock

import pytest
from pytest import MonkeyPatch

from jebaerme.models.env import Settings


@pytest.fixture(autouse=True)
def stub_init_graph(monkeypatch: MonkeyPatch) -> MagicMock:
    fake_graph = MagicMock()
    init = MagicMock(return_value=fake_graph)
    monkeypatch.setattr("jebaerme.api.app.init_graph", init)
    return init


@pytest.fixture
def settings() -> Settings:
    return Settings()
