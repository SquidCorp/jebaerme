"""Chat generation. No HTTP/router details."""

from collections.abc import AsyncIterator

from jebaerme.agents.agent import LlmAuthError
from jebaerme.agents.chat_graph import astream_chat

__all__ = ["LlmAuthError", "stream_chat"]


async def stream_chat(message: str) -> AsyncIterator[str]:
    chunks = astream_chat(message)
    first = await anext(chunks, None)

    async def texts() -> AsyncIterator[str]:
        if first is not None:
            yield first
        async for chunk in chunks:
            yield chunk

    return texts()
