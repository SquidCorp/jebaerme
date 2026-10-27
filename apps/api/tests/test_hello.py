from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from jebaerme.api.app import create_app
from jebaerme.services.hello import LlmAuthError, say_hello


@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_say_hello(mock_create_agent: MagicMock, _mock_chat: MagicMock) -> None:
    graph = MagicMock()
    graph.invoke.return_value = {"messages": [AIMessage(content="Bonjour")]}
    mock_create_agent.return_value = graph
    hello = say_hello()
    assert hello.status == "ok"
    assert hello.text == "Bonjour"
    graph.invoke.assert_called_once()


@patch("jebaerme.agents.agent.ChatOpenRouter")
@patch("jebaerme.agents.agent.create_agent")
def test_hello_endpoint(mock_create_agent: MagicMock, _mock_chat: MagicMock) -> None:
    graph = MagicMock()
    graph.invoke.return_value = {"messages": [AIMessage(content="Hola")]}
    mock_create_agent.return_value = graph
    client = TestClient(create_app())
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "text": "Hola"}


@patch("jebaerme.api.chat.say_hello", side_effect=LlmAuthError("rejected"))
def test_hello_endpoint_maps_auth_error(_say_hello: MagicMock) -> None:
    client = TestClient(create_app())
    response = client.get("/hello")
    assert response.status_code == 502
    assert response.json() == {"detail": "rejected"}
