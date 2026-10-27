"""Intent classification. No HTTP/router details."""

from jebaerme.jev.jev import Jev, JevAuthError
from jebaerme.models.jev import BaseJevResponse, ChoiceQuestion

__all__ = [
    "INTENT_LANGUAGE_INSTRUCTIONS",
    "JevAuthError",
    "classify_intent",
    "instruction_for_intent",
]

INTENT_LANGUAGE_INSTRUCTIONS = {
    "generic": (
        "The user expects a generic response. Use everyday language, "
        "do not use too technical terms."
    ),
    "soft_skills": (
        "The user expects a response in business language, "
        "do not use too technical terms."
    ),
    "technical_skills": (
        "The user expects a technical response. Use precise technical terms "
        "and include relevant implementation detail."
    ),
}

_INTENT_QUESTION = ChoiceQuestion(
    instructions="What is the intent of this message?",
    criteria={
        "generic": (
            "intent is to learn something more personal about the person."
            "Personal details. Language spoken. Hobbies."
        ),
        "soft_skills": (
            "intent is about evaluating how the person acts in a "
            "professional environment. Will the person fit in the team."
        ),
        "technical_skills": (
            "intent is about evaluation the knowledge of the person in technical fields"
        ),
    },
)


def instruction_for_intent(choice: str) -> str | None:
    return INTENT_LANGUAGE_INSTRUCTIONS.get(choice)


def classify_intent(state: str) -> BaseJevResponse:
    jev = Jev({"intent": _INTENT_QUESTION})
    return jev.send(state)
