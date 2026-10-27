from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk
from pytest import MonkeyPatch

from jebaerme.api.app import create_app
from jebaerme.models.jev import BaseJevResponse
from jebaerme.services.chat import LlmAuthError
from jebaerme.services.intent import (
    INTENT_LANGUAGE_INSTRUCTIONS,
    JevAuthError,
)

_INTENT_RESPONSE = {
    "id": "gen-dec-1",
    "model": "typesafe/jev-1.14",
    "provider": "TypeSafe",
    "answers": {
        "intent": {
            "type": "choice",
            "choice": "soft_skills",
            "confidence": 0.8,
            "probabilities": {
                "generic": 0.1,
                "soft_skills": 0.8,
                "technical_skills": 0.1,
            },
        }
    },
    "usage": {"input_tokens": 100, "output_tokens": 10, "cost": 0.0001},
}


async def fake_chunks() -> AsyncIterator[tuple[AIMessageChunk, dict[str, str]]]:
    yield AIMessageChunk(content="Hel"), {}
    yield AIMessageChunk(content="lo"), {}


def _set_intent_flag(monkeypatch: MonkeyPatch, enabled: bool) -> None:
    monkeypatch.setattr(
        "jebaerme.agents.chat_graph.env.ENABLE_INTENT_DECISION",
        enabled,
    )


@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_chat_endpoint_streams(
    mock_create_agent: MagicMock,
    _mock_chat: MagicMock,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_intent_flag(monkeypatch, False)
    graph = MagicMock()
    graph.astream.return_value = fake_chunks()
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "Hi"})
    assert response.status_code == 200
    assert response.text == "Hello"
    graph.astream.assert_called_once()
    assert mock_create_agent.call_args.kwargs["system_prompt"] == (
        "You are a helpful assistant."
    )


@patch("jebaerme.agents.chat_graph.classify_intent")
@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_chat_skips_jev_when_intent_flag_off(
    mock_create_agent: MagicMock,
    _mock_chat: MagicMock,
    classify: MagicMock,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_intent_flag(monkeypatch, False)
    graph = MagicMock()
    graph.astream.return_value = fake_chunks()
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "Hi"})
    assert response.status_code == 200
    classify.assert_not_called()


@patch("jebaerme.agents.chat_graph.classify_intent")
@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_chat_appends_intent_instruction_when_flag_on(
    mock_create_agent: MagicMock,
    _mock_chat: MagicMock,
    classify: MagicMock,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_intent_flag(monkeypatch, True)
    classify.return_value = BaseJevResponse.model_validate(_INTENT_RESPONSE)
    graph = MagicMock()
    graph.astream.return_value = fake_chunks()
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "How does she handle conflict?"})
    assert response.status_code == 200
    assert response.text == "Hello"
    classify.assert_called_once_with("How does she handle conflict?")
    prompt = mock_create_agent.call_args.kwargs["system_prompt"]
    assert prompt.startswith("You are a helpful assistant.")
    assert INTENT_LANGUAGE_INSTRUCTIONS["soft_skills"] in prompt


@patch("jebaerme.agents.chat_graph.classify_intent")
@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_chat_retries_jev_then_continues_without_intent(
    mock_create_agent: MagicMock,
    _mock_chat: MagicMock,
    classify: MagicMock,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_intent_flag(monkeypatch, True)
    classify.side_effect = JevAuthError("rejected")
    graph = MagicMock()
    graph.astream.return_value = fake_chunks()
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "Hi"})
    assert response.status_code == 200
    assert response.text == "Hello"
    assert classify.call_count == 3
    assert mock_create_agent.call_args.kwargs["system_prompt"] == (
        "You are a helpful assistant."
    )


@patch("jebaerme.agents.chat_graph.classify_intent")
@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_chat_uses_intent_after_jev_retries(
    mock_create_agent: MagicMock,
    _mock_chat: MagicMock,
    classify: MagicMock,
    monkeypatch: MonkeyPatch,
) -> None:
    _set_intent_flag(monkeypatch, True)
    classify.side_effect = [
        JevAuthError("rejected"),
        JevAuthError("rejected"),
        BaseJevResponse.model_validate(_INTENT_RESPONSE),
    ]
    graph = MagicMock()
    graph.astream.return_value = fake_chunks()
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "Hi"})
    assert response.status_code == 200
    assert classify.call_count == 3
    prompt = mock_create_agent.call_args.kwargs["system_prompt"]
    assert INTENT_LANGUAGE_INSTRUCTIONS["soft_skills"] in prompt


@patch("jebaerme.api.chat.stream_chat", new_callable=AsyncMock)
def test_chat_endpoint_maps_auth_error(stream_chat: AsyncMock) -> None:
    stream_chat.side_effect = LlmAuthError("rejected")
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "Hi"})
    assert response.status_code == 502
    assert response.json() == {"detail": "rejected"}


def test_chat_endpoint_rejects_empty_message() -> None:
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422
