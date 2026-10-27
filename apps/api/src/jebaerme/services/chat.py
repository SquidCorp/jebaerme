"""Chat generation. No HTTP/router details."""

from collections.abc import AsyncIterator

from jebaerme.agents.agent import Agent, LlmAuthError
from jebaerme.models.agent import AgentConfig, AgentPrompt

__all__ = ["LlmAuthError", "stream_chat"]


async def stream_chat(message: str) -> AsyncIterator[str]:
    agent = Agent(
        AgentPrompt(prompt="You are a helpful assistant."),
        AgentConfig(
            model="anthropic/claude-haiku-5.5",
            temperature=0.9,
        ),
    )
    chunks = agent.stream(message)
    first = await anext(chunks, None)

    async def texts() -> AsyncIterator[str]:
        if first is not None and first.text:
            yield first.text
        async for chunk in chunks:
            if chunk.text:
                yield chunk.text

    return texts()
