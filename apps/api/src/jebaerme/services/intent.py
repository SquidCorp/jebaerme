"""Intent classification. No HTTP/router details."""

from jebaerme.jev.jev import Jev, JevAuthError
from jebaerme.models.jev import BaseJevResponse, ChoiceQuestion

__all__ = ["JevAuthError", "classify_intent"]

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


def classify_intent(state: str) -> BaseJevResponse:
    jev = Jev({"intent": _INTENT_QUESTION})
    return jev.send(state)
