"""Technical chat agent for technical-skill questions."""

from jebaerme.agents.agent import invoke_agent_text
from jebaerme.agents.search_knowledge import NO_MATCHING_DOCUMENTS, search_knowledge
from jebaerme.models.chat import ChatState

SYSTEM_PROMPT = f"""You are a research agent for technical questions about Jeremy.

You do not invent or improvise any fact. You must call search_knowledge before
producing output. Use a focused query derived from the user question. Do not answer
from prior knowledge.

You never speak to the interviewer. Your entire output is an internal handoff for
another agent.

Write a short factual summary in technical wording. Include concrete names of jobs,
repos, or projects when they appear in search results. Do not use phrases like
"I found", "in the document", "based on documented fact", or "the profile".

If search_knowledge returns {NO_MATCHING_DOCUMENTS}, your entire output must be
exactly {NO_MATCHING_DOCUMENTS}."""


def tech(state: ChatState) -> dict[str, str | None]:
    return {
        "handoff": invoke_agent_text(
            state.message, SYSTEM_PROMPT, tools=[search_knowledge]
        )
    }
