from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from jebaerme.api.app import create_app
from jebaerme.services.hello import LlmAuthError, say_hello


@patch("jebaerme.services.hello.ChatOpenRouter")
def test_say_hello(mock_chat: MagicMock) -> None:
    mock_chat.return_value.invoke.return_value = AIMessage(content="Bonjour")
    hello = say_hello()
    assert hello.status == "ok"
    assert hello.text == "Bonjour"
    mock_chat.return_value.invoke.assert_called_once()


@patch("jebaerme.services.hello.ChatOpenRouter")
def test_hello_endpoint(mock_chat: MagicMock) -> None:
    mock_chat.return_value.invoke.return_value = AIMessage(content="Hola")
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
