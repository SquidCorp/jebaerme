"""Reusable LLM agent wrapper."""

from collections.abc import AsyncIterator

from langchain_core.messages import AIMessageChunk
from langchain_openrouter import ChatOpenRouter
from openrouter.errors.unauthorizedresponse_error import UnauthorizedResponseError

from jebaerme.models.agent import AgentConfig, AgentPrompt
from jebaerme.models.env import env


class LlmAuthError(RuntimeError):
    """The LLM provider rejected the configured API key."""


class Agent:
    """Wraps ChatOpenRouter so callers pass a prompt and config, not SDK details."""

    def __init__(self, system_prompt: AgentPrompt, config: AgentConfig) -> None:
        self.system_prompt = system_prompt.prompt
        self._llm = ChatOpenRouter(
            model=config.model,
            temperature=config.temperature,
            api_key=env.openrouter_api_key(),
        )
        self._messages: list[tuple[str, str]] = [
            ("system", self.system_prompt),
        ]

    def invoke(self, msg: str) -> str:
        try:
            response = self._llm.invoke([*self._messages, ("human", msg)])
        except UnauthorizedResponseError as exc:
            raise LlmAuthError(
                "OpenRouter rejected OPENROUTER_API_KEY (401 User not found)."
            ) from exc
        return response.text

    async def stream(self, msg: str) -> AsyncIterator[AIMessageChunk]:
        try:
            async for chunk in self._llm.astream([*self._messages, ("human", msg)]):
                yield chunk
        except UnauthorizedResponseError as exc:
            raise LlmAuthError(
                "OpenRouter rejected OPENROUTER_API_KEY (401 User not found)."
            ) from exc
