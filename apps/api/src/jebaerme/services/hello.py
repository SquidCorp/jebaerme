"""Greeting generation. No HTTP/router details."""

from langchain_openrouter import ChatOpenRouter
from openrouter.errors.unauthorizedresponse_error import UnauthorizedResponseError

from jebaerme.models.env import env
from jebaerme.models.hello import Hello


class LlmAuthError(RuntimeError):
    """The LLM provider rejected the configured API key."""


def say_hello() -> Hello:
    model = ChatOpenRouter(
        model="nvidia/nemotron-3.5-super-vl",
        temperature=0.9,
        api_key=env.openrouter_api_key(),
    )
    try:
        response = model.invoke("Say Hello in a random language.")
    except UnauthorizedResponseError as exc:
        raise LlmAuthError(
            "OpenRouter rejected OPENROUTER_API_KEY (401 User not found)."
        ) from exc
    return Hello(status="ok", text=response.text)
