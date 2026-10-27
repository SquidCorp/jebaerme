from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessageChunk

from jebaerme.api.app import create_app
from jebaerme.services.chat import LlmAuthError


async def fake_chunks() -> AsyncIterator[tuple[AIMessageChunk, dict[str, str]]]:
    yield AIMessageChunk(content="Hel"), {}
    yield AIMessageChunk(content="lo"), {}


@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_chat_endpoint_streams(
    mock_create_agent: MagicMock, _mock_chat: MagicMock
) -> None:
    graph = MagicMock()
    graph.astream.return_value = fake_chunks()
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "Hi"})
    assert response.status_code == 200
    assert response.text == "Hello"
    graph.astream.assert_called_once()


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
