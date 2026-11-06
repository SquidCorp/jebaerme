from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from openrouter.errors.unauthorizedresponse_error import UnauthorizedResponseError

from jebaerme.agents.agent import LlmAuthError
from jebaerme.agents.deepagent import DeepAgent
from jebaerme.models.agent import AgentConfig, AgentPrompt


def _agent() -> DeepAgent:
    return DeepAgent(
        AgentPrompt(prompt="You are a deep agent."),
        AgentConfig(model="minimax/minimax-m3.1-flash", temperature=0.9),
    )


@patch("jebaerme.agents.deepagent.ChatOpenRouter")
@patch("jebaerme.agents.deepagent.create_deep_agent")
def test_invoke_returns_last_ai_text(
    mock_create: MagicMock, _mock_chat: MagicMock
) -> None:
    graph = MagicMock()
    graph.invoke.return_value = {
        "messages": [HumanMessage(content="Hi"), AIMessage(content="Bonjour")]
    }
    mock_create.return_value = graph
    assert _agent().invoke("Hi") == "Bonjour"


@patch("jebaerme.agents.deepagent.ChatOpenRouter")
@patch("jebaerme.agents.deepagent.create_deep_agent")
def test_invoke_maps_auth_error(mock_create: MagicMock, _mock_chat: MagicMock) -> None:
    graph = MagicMock()
    graph.invoke.side_effect = UnauthorizedResponseError.__new__(
        UnauthorizedResponseError
    )
    mock_create.return_value = graph
    with pytest.raises(LlmAuthError, match="OPENROUTER_API_KEY"):
        _agent().invoke("Hi")


@patch("jebaerme.agents.deepagent.ChatOpenRouter")
@patch("jebaerme.agents.deepagent.create_deep_agent")
def test_invoke_rejects_non_ai_last_message(
    mock_create: MagicMock, _mock_chat: MagicMock
) -> None:
    graph = MagicMock()
    graph.invoke.return_value = {"messages": [HumanMessage(content="Hi")]}
    mock_create.return_value = graph
    with pytest.raises(RuntimeError, match="AI message"):
        _agent().invoke("Hi")
