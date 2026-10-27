import os

from pytest import MonkeyPatch

from jebaerme.models.env import Settings

_LANGSMITH_KEYS = (
    "LANGSMITH_TRACING",
    "LANGSMITH_ENDPOINT",
    "LANGSMITH_API_KEY",
    "LANGSMITH_AGENT_ID",
    "LANGSMITH_AGENT_ENVIRONMENT",
)


def test_apply_langsmith_env_exports_sdk_vars(monkeypatch: MonkeyPatch) -> None:
    for key in _LANGSMITH_KEYS:
        monkeypatch.delenv(key, raising=False)

    settings = Settings(
        LANGSMITH_TRACING=True,
        LANGSMITH_ENDPOINT="https://api.smith.langchain.com",
        LANGSMITH_API_KEY="lsv2_test",
        LANGSMITH_AGENT_ID="rune",
        LANGSMITH_AGENT_ENVIRONMENT="local",
    )
    settings.apply_langsmith_env()

    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_ENDPOINT"] == "https://api.smith.langchain.com"
    assert os.environ["LANGSMITH_API_KEY"] == "lsv2_test"
    assert os.environ["LANGSMITH_AGENT_ID"] == "rune"
    assert os.environ["LANGSMITH_AGENT_ENVIRONMENT"] == "local"


def test_apply_langsmith_env_disabled_clears_vars(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    settings = Settings(LANGSMITH_TRACING=False)
    settings.apply_langsmith_env()
    assert "LANGSMITH_TRACING" not in os.environ
