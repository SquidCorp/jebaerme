"""Chat LangGraph: optional Jev intent, then the agent."""

from collections.abc import AsyncIterator
from typing import Literal

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from jebaerme.agents.agent import Agent
from jebaerme.models.agent import AgentConfig, AgentPrompt
from jebaerme.models.chat import ChatState
from jebaerme.models.env import env
from jebaerme.models.jev import ChoiceAnswer
from jebaerme.services.intent import classify_intent, instruction_for_intent

BASE_SYSTEM_PROMPT = "You are a helpful assistant."
INTENT_CLASSIFY_RETRIES = 2
_MAX_INTENT_ATTEMPTS = 1 + INTENT_CLASSIFY_RETRIES


def _should_classify(_state: ChatState) -> Literal["fetch_intent", "respond"]:
    if env.ENABLE_INTENT_DECISION:
        return "fetch_intent"
    return "respond"


def fetch_intent(state: ChatState) -> dict[str, str | None]:
    for _ in range(_MAX_INTENT_ATTEMPTS):
        try:
            result = classify_intent(state.message)
        except Exception:
            continue
        answer = result.answers.get("intent")
        if isinstance(answer, ChoiceAnswer):
            return {
                "intent": answer.choice,
                "intent_instruction": instruction_for_intent(answer.choice),
            }
        return {"intent": None, "intent_instruction": None}
    return {"intent": None, "intent_instruction": None}


async def respond(state: ChatState) -> dict[str, str | None]:
    writer = get_stream_writer()
    prompt = BASE_SYSTEM_PROMPT
    if state.intent_instruction:
        prompt = f"{prompt}\n{state.intent_instruction}"
    agent = Agent(
        AgentPrompt(prompt=prompt),
        AgentConfig(
            model=env.CHAT_MODEL,
            temperature=0.9,
        ),
    )
    texts: list[str] = []
    async for chunk in agent.stream(state.message):
        if chunk.text:
            writer(chunk.text)
            texts.append(chunk.text)
    return {"response": "".join(texts)}


def build_chat_graph() -> CompiledStateGraph[ChatState, None, ChatState, ChatState]:
    graph = StateGraph(ChatState)
    graph.add_node("fetch_intent", fetch_intent)
    graph.add_node("respond", respond)
    graph.add_conditional_edges(
        START,
        _should_classify,
        {"fetch_intent": "fetch_intent", "respond": "respond"},
    )
    graph.add_edge("fetch_intent", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


graph = build_chat_graph()


async def astream_chat(message: str) -> AsyncIterator[str]:
    async for chunk in graph.astream(ChatState(message=message), stream_mode="custom"):
        if isinstance(chunk, str) and chunk:
            yield chunk
