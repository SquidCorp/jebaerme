"""Reusable LLM agent wrapper."""

from collections.abc import AsyncIterator

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_openrouter import ChatOpenRouter
from langgraph.config import get_stream_writer
from openrouter.errors.unauthorizedresponse_error import UnauthorizedResponseError

from jebaerme.models.agent import AgentConfig, AgentPrompt
from jebaerme.models.env import env


class LlmAuthError(RuntimeError):
    """The LLM provider rejected the configured API key."""


class Agent:
    """Wraps create_agent so callers pass a prompt and config, not SDK details."""

    def __init__(self, system_prompt: AgentPrompt, config: AgentConfig) -> None:
        self.system_prompt = system_prompt.prompt
        self._llm = ChatOpenRouter(
            model=config.model,
            temperature=config.temperature,
            api_key=env.openrouter_api_key(),
        )
        self._agent = create_agent(
            model=self._llm,
            system_prompt=self.system_prompt,
            name=env.LANGSMITH_AGENT_ID,
        )

    def invoke(self, msg: str) -> str:
        try:
            result = self._agent.invoke(_user_turn(msg))
        except UnauthorizedResponseError as exc:
            raise LlmAuthError(
                "OpenRouter rejected OPENROUTER_API_KEY (401 User not found)."
            ) from exc
        last = result["messages"][-1]
        if not isinstance(last, AIMessage):
            raise RuntimeError("Agent did not return an AI message.")
        return last.text

    async def stream(self, msg: str) -> AsyncIterator[AIMessageChunk]:
        try:
            async for event in self._agent.astream(
                _user_turn(msg),
                stream_mode="messages",
            ):
                chunk = event[0] if isinstance(event, tuple) else event
                if isinstance(chunk, AIMessageChunk):
                    yield chunk
        except UnauthorizedResponseError as exc:
            raise LlmAuthError(
                "OpenRouter rejected OPENROUTER_API_KEY (401 User not found)."
            ) from exc


async def stream_agent_text(message: str, system_prompt: str) -> str:
    writer = get_stream_writer()
    agent = Agent(
        AgentPrompt(prompt=system_prompt),
        AgentConfig(
            model=env.CHAT_MODEL,
            temperature=0.9,
        ),
    )
    texts: list[str] = []
    async for chunk in agent.stream(message):
        if chunk.text:
            writer(chunk.text)
            texts.append(chunk.text)
    return "".join(texts)


def _user_turn(msg: str) -> dict[str, list[dict[str, str]]]:
    return {"messages": [{"role": "user", "content": msg}]}
