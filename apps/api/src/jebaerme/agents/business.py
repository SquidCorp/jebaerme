"""Business chat agent for generic and soft-skill questions."""

from jebaerme.agents.agent import stream_agent_text
from jebaerme.models.chat import ChatState

SYSTEM_PROMPT = """You are the referant agent to answer generic and business questions.
You do not invent or improvised any fact and all your answer will imply
a research in the document.

You collect clues that match the input request by using your tools.

You handoff your discoveries in business wording in a short summarization."""


async def business(state: ChatState) -> dict[str, str | None]:
    prompt = SYSTEM_PROMPT
    if state.intent_instruction:
        prompt = f"{prompt}\n{state.intent_instruction}"
    return {"response": await stream_agent_text(state.message, prompt)}
