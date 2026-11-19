"""Technical chat agent for technical-skill questions."""

from jebaerme.agents.agent import stream_agent_text
from jebaerme.agents.search_knowledge import search_knowledge
from jebaerme.models.chat import ChatState

SYSTEM_PROMPT = """You are the referant agent to answer technical questions.
You do not invent or improvised any fact and all your answer will imply
a research in the document.

You must call search_knowledge before answering. Use a focused query derived
from the user question. Do not answer from prior knowledge.

If search_knowledge returns NO_MATCHING_DOCUMENTS, reply that you don't know.

You collect clues that match the input request by using your tools.

You handoff your discoveries in technical wording in a short summarization."""


async def tech(state: ChatState) -> dict[str, str | None]:
    prompt = SYSTEM_PROMPT
    if state.intent_instruction:
        prompt = f"{prompt}\n{state.intent_instruction}"
    return {
        "response": await stream_agent_text(
            state.message, prompt, tools=[search_knowledge]
        )
    }
