"""Shared pytest fixtures."""

import pytest

from jebaerme.models.env import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings()
