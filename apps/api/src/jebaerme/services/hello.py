"""Greeting generation. No HTTP/router details."""

from jebaerme.agents.agent import Agent, LlmAuthError
from jebaerme.models.agent import AgentConfig, AgentPrompt
from jebaerme.models.hello import Hello

__all__ = ["LlmAuthError", "say_hello"]


def say_hello() -> Hello:
    agent = Agent(
        AgentPrompt(prompt="You are speaking a lot of different language"),
        AgentConfig(
            model="minimax/minimax-m3.1-flash",
            temperature=0.9,
        ),
    )
    return Hello(status="ok", text=agent.invoke("Say Hello in a random language"))
